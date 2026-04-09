"""
Metrics computation for tool call evaluation.

Compares actual tool calls from the LLM against expected values
and computes per-case and aggregate metrics.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class CaseResult:
    """Result of evaluating a single test case."""

    case_id: str
    tool_name: str
    complexity: str
    test_type: str
    prompt: str

    # What the model actually did
    raw_response: str = ""
    actual_tool_name: str | None = None
    actual_parameters: dict | None = None
    response_time_ms: float = 0.0

    # Scores
    tool_selected_correctly: bool = False
    valid_json: bool = False
    required_params_present: bool = False
    required_params_correct: bool = False
    optional_params_bonus: float = 0.0  # 0.0 to 1.0
    format_compliant: bool = False

    # Details for debugging
    missing_params: list[str] = field(default_factory=list)
    wrong_params: dict = field(default_factory=dict)  # param -> {expected, actual}
    extra_params: list[str] = field(default_factory=list)
    error: str | None = None


def evaluate_case(
    test_case: dict,
    actual_tool_name: str | None,
    actual_parameters: dict | None,
    raw_response: str,
    response_time_ms: float,
) -> CaseResult:
    """Evaluate a single tool call against expected values."""
    result = CaseResult(
        case_id=test_case["id"],
        tool_name=test_case["tool_name"],
        complexity=test_case["complexity"],
        test_type=test_case["test_type"],
        prompt=test_case["prompt"],
        raw_response=raw_response,
        actual_tool_name=actual_tool_name,
        actual_parameters=actual_parameters,
        response_time_ms=response_time_ms,
    )

    # 1. Valid JSON — did we get parseable tool call at all?
    result.valid_json = actual_parameters is not None

    if not result.valid_json:
        return result

    # 2. Tool selection
    result.tool_selected_correctly = actual_tool_name == test_case["tool_name"]

    if not result.tool_selected_correctly:
        return result

    # 3. Required parameter completeness & correctness
    expected = test_case["expected_parameters"]
    actual = actual_parameters or {}

    missing = []
    wrong = {}
    all_correct = True

    for key, expected_val in expected.items():
        if key not in actual:
            missing.append(key)
            all_correct = False
        else:
            if not _values_match(expected_val, actual[key]):
                wrong[key] = {"expected": expected_val, "actual": actual[key]}
                all_correct = False

    result.missing_params = missing
    result.wrong_params = wrong
    result.required_params_present = len(missing) == 0
    result.required_params_correct = all_correct

    # 4. Extra parameters (not in expected or optional)
    expected_optional = test_case.get("expected_optional_parameters", {})
    all_expected_keys = set(expected.keys()) | set(expected_optional.keys())
    result.extra_params = [k for k in actual if k not in all_expected_keys]

    # 5. Optional parameter handling
    if expected_optional:
        matched = 0
        for key, expected_val in expected_optional.items():
            if key in actual and _values_match(expected_val, actual[key]):
                matched += 1
        result.optional_params_bonus = matched / len(expected_optional)
    else:
        result.optional_params_bonus = 1.0  # no optional params to check

    # 6. Format compliance — check types match schema expectations
    result.format_compliant = _check_format_compliance(expected, actual)

    return result


def _values_match(expected, actual) -> bool:
    """Flexible value comparison that handles type coercion and normalization."""
    if expected is None:
        return actual is None

    # Exact match
    if expected == actual:
        return True

    # String comparison (case-insensitive for enum-like values, normalize whitespace)
    if isinstance(expected, str) and isinstance(actual, str):
        if expected.lower().strip() == actual.lower().strip():
            return True
        # Date format flexibility: accept various separators
        if _normalize_date(expected) == _normalize_date(actual):
            return True
        return False

    # Numeric comparison (int vs float tolerance)
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if isinstance(expected, int) and isinstance(actual, int):
            return expected == actual
        return abs(float(expected) - float(actual)) < 0.01

    # String-to-number coercion (model might return "100" instead of 100)
    if isinstance(expected, (int, float)) and isinstance(actual, str):
        try:
            return abs(float(expected) - float(actual)) < 0.01
        except ValueError:
            return False

    # List comparison (order-insensitive for simple lists)
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False
        # Try order-sensitive first
        if all(_values_match(e, a) for e, a in zip(expected, actual)):
            return True
        # Try order-insensitive for simple string/number lists
        if all(isinstance(x, (str, int, float)) for x in expected):
            return sorted(str(x).lower() for x in expected) == sorted(
                str(x).lower() for x in actual
            )
        return False

    # Dict comparison (recursive)
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in expected:
            if key not in actual:
                return False
            if not _values_match(expected[key], actual[key]):
                return False
        return True

    return False


def _normalize_date(s: str) -> str:
    """Normalize date strings for comparison."""
    # Remove timezone info for comparison
    s = re.sub(r"[+-]\d{2}:\d{2}$", "", s)
    s = s.replace("Z", "")
    # Normalize separators
    s = s.replace("/", "-")
    return s.strip()


def _check_format_compliance(expected: dict, actual: dict) -> bool:
    """Check if actual parameter types roughly match expected types."""
    for key, expected_val in expected.items():
        if key not in actual:
            continue
        actual_val = actual[key]
        # Check nested dict
        if isinstance(expected_val, dict) and not isinstance(actual_val, dict):
            return False
        # Check list
        if isinstance(expected_val, list) and not isinstance(actual_val, list):
            return False
    return True


@dataclass
class AggregateMetrics:
    """Aggregate metrics across all test cases."""

    total_cases: int = 0
    valid_json_count: int = 0
    tool_selection_correct: int = 0
    required_params_present_count: int = 0
    required_params_correct_count: int = 0
    format_compliant_count: int = 0
    avg_optional_bonus: float = 0.0
    avg_response_time_ms: float = 0.0
    error_count: int = 0

    @property
    def valid_json_rate(self) -> float:
        return self.valid_json_count / self.total_cases if self.total_cases else 0

    @property
    def tool_selection_accuracy(self) -> float:
        return self.tool_selection_correct / self.total_cases if self.total_cases else 0

    @property
    def param_completeness(self) -> float:
        return (
            self.required_params_present_count / self.total_cases
            if self.total_cases
            else 0
        )

    @property
    def param_accuracy(self) -> float:
        return (
            self.required_params_correct_count / self.total_cases
            if self.total_cases
            else 0
        )

    @property
    def format_compliance_rate(self) -> float:
        return (
            self.format_compliant_count / self.total_cases if self.total_cases else 0
        )


def compute_aggregate(results: list[CaseResult]) -> AggregateMetrics:
    """Compute aggregate metrics from a list of case results."""
    if not results:
        return AggregateMetrics()

    m = AggregateMetrics(total_cases=len(results))

    optional_bonuses = []
    response_times = []

    for r in results:
        if r.valid_json:
            m.valid_json_count += 1
        if r.tool_selected_correctly:
            m.tool_selection_correct += 1
        if r.required_params_present:
            m.required_params_present_count += 1
        if r.required_params_correct:
            m.required_params_correct_count += 1
        if r.format_compliant:
            m.format_compliant_count += 1
        if r.error:
            m.error_count += 1
        optional_bonuses.append(r.optional_params_bonus)
        response_times.append(r.response_time_ms)

    m.avg_optional_bonus = sum(optional_bonuses) / len(optional_bonuses)
    m.avg_response_time_ms = sum(response_times) / len(response_times)

    return m


def compute_grouped_metrics(
    results: list[CaseResult], group_by: str
) -> dict[str, AggregateMetrics]:
    """Group results by a field and compute metrics per group."""
    groups: dict[str, list[CaseResult]] = {}
    for r in results:
        key = getattr(r, group_by)
        groups.setdefault(key, []).append(r)

    return {key: compute_aggregate(group_results) for key, group_results in groups.items()}
