#!/usr/bin/env python3
"""
Gemma 4 26B Tool Call Evaluation — Entry Point

Usage:
    python main.py                  # Run all 150 test cases
    python main.py --quick          # Run 10 cases (1 per tool) for quick smoke test
    python main.py --tool weather   # Run cases for a specific tool (substring match)
    python main.py --type direct    # Run only direct-type cases
    python main.py --complexity simple  # Run only simple-complexity cases
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime

import pandas as pd

import config
from eval.metrics import (
    AggregateMetrics,
    CaseResult,
    compute_aggregate,
    compute_grouped_metrics,
)
from eval.runner import run_all_cases
from test_cases.cases import TEST_CASES


def filter_cases(
    cases: list[dict],
    tool: str | None = None,
    test_type: str | None = None,
    complexity: str | None = None,
    quick: bool = False,
) -> list[dict]:
    filtered = cases
    if tool:
        filtered = [c for c in filtered if tool.lower() in c["tool_name"].lower()]
    if test_type:
        filtered = [c for c in filtered if c["test_type"] == test_type]
    if complexity:
        filtered = [c for c in filtered if c["complexity"] == complexity]
    if quick:
        # Pick 1 direct case per tool
        seen_tools: set[str] = set()
        quick_cases = []
        for c in filtered:
            if c["tool_name"] not in seen_tools and c["test_type"] == "direct":
                quick_cases.append(c)
                seen_tools.add(c["tool_name"])
        filtered = quick_cases
    return filtered


def print_metrics_table(label: str, metrics: AggregateMetrics) -> None:
    print(f"  {label:25s}  n={metrics.total_cases:3d}  "
          f"JSON={metrics.valid_json_rate:5.1%}  "
          f"Tool={metrics.tool_selection_accuracy:5.1%}  "
          f"Params={metrics.param_accuracy:5.1%}  "
          f"Complete={metrics.param_completeness:5.1%}  "
          f"Format={metrics.format_compliance_rate:5.1%}  "
          f"Optional={metrics.avg_optional_bonus:5.1%}  "
          f"Avg ms={metrics.avg_response_time_ms:7.0f}")


def print_report(results: list[CaseResult]) -> None:
    overall = compute_aggregate(results)
    by_complexity = compute_grouped_metrics(results, "complexity")
    by_type = compute_grouped_metrics(results, "test_type")
    by_tool = compute_grouped_metrics(results, "tool_name")

    print("\n" + "=" * 120)
    print("EVALUATION REPORT")
    print("=" * 120)

    print("\n── Overall ──")
    print_metrics_table("ALL", overall)

    print("\n── By Complexity ──")
    for level in ["simple", "medium", "complex"]:
        if level in by_complexity:
            print_metrics_table(level.upper(), by_complexity[level])

    print("\n── By Test Type ──")
    for t in ["direct", "inference", "edge", "distractor"]:
        if t in by_type:
            print_metrics_table(t.upper(), by_type[t])

    print("\n── By Tool ──")
    for tool_name in sorted(by_tool.keys()):
        print_metrics_table(tool_name, by_tool[tool_name])

    # Print failures summary
    failures = [r for r in results if not r.required_params_correct]
    if failures:
        print(f"\n── Failures ({len(failures)}) ──")
        for f in failures[:30]:  # limit output
            reason = ""
            if not f.valid_json:
                reason = "no valid JSON"
            elif not f.tool_selected_correctly:
                reason = f"wrong tool: {f.actual_tool_name}"
            else:
                parts = []
                if f.missing_params:
                    parts.append(f"missing: {f.missing_params}")
                if f.wrong_params:
                    parts.append(f"wrong: {f.wrong_params}")
                reason = "; ".join(parts)
            print(f"  {f.case_id:40s} → {reason}")
        if len(failures) > 30:
            print(f"  ... and {len(failures) - 30} more")

    print()
    if overall.error_count > 0:
        print(f"⚠ {overall.error_count} cases had errors (API timeout, invalid response, etc.)")
    print()


def save_results(results: list[CaseResult]) -> None:
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Full report JSON
    report_path = os.path.join(config.RESULTS_DIR, f"report_{timestamp}.json")
    report_data = {
        "timestamp": timestamp,
        "model": config.MODEL_NAME,
        "api_base_url": config.API_BASE_URL,
        "total_cases": len(results),
        "overall": _metrics_to_dict(compute_aggregate(results)),
        "by_complexity": {
            k: _metrics_to_dict(v)
            for k, v in compute_grouped_metrics(results, "complexity").items()
        },
        "by_test_type": {
            k: _metrics_to_dict(v)
            for k, v in compute_grouped_metrics(results, "test_type").items()
        },
        "by_tool": {
            k: _metrics_to_dict(v)
            for k, v in compute_grouped_metrics(results, "tool_name").items()
        },
        "cases": [_case_to_dict(r) for r in results],
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"Full report saved to: {report_path}")

    # Summary CSV
    csv_path = os.path.join(config.RESULTS_DIR, f"summary_{timestamp}.csv")
    rows = []
    for r in results:
        rows.append({
            "case_id": r.case_id,
            "tool_name": r.tool_name,
            "complexity": r.complexity,
            "test_type": r.test_type,
            "valid_json": r.valid_json,
            "tool_correct": r.tool_selected_correctly,
            "params_present": r.required_params_present,
            "params_correct": r.required_params_correct,
            "format_compliant": r.format_compliant,
            "optional_bonus": r.optional_params_bonus,
            "response_time_ms": r.response_time_ms,
            "error": r.error or "",
        })
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    print(f"Summary CSV saved to: {csv_path}")


def _metrics_to_dict(m: AggregateMetrics) -> dict:
    return {
        "total_cases": m.total_cases,
        "valid_json_rate": round(m.valid_json_rate, 4),
        "tool_selection_accuracy": round(m.tool_selection_accuracy, 4),
        "param_completeness": round(m.param_completeness, 4),
        "param_accuracy": round(m.param_accuracy, 4),
        "format_compliance_rate": round(m.format_compliance_rate, 4),
        "avg_optional_bonus": round(m.avg_optional_bonus, 4),
        "avg_response_time_ms": round(m.avg_response_time_ms, 1),
        "error_count": m.error_count,
    }


def _case_to_dict(r: CaseResult) -> dict:
    return {
        "case_id": r.case_id,
        "tool_name": r.tool_name,
        "complexity": r.complexity,
        "test_type": r.test_type,
        "prompt": r.prompt,
        "actual_tool_name": r.actual_tool_name,
        "actual_parameters": r.actual_parameters,
        "valid_json": r.valid_json,
        "tool_correct": r.tool_selected_correctly,
        "params_present": r.required_params_present,
        "params_correct": r.required_params_correct,
        "format_compliant": r.format_compliant,
        "optional_bonus": r.optional_params_bonus,
        "response_time_ms": round(r.response_time_ms, 1),
        "missing_params": r.missing_params,
        "wrong_params": r.wrong_params,
        "extra_params": r.extra_params,
        "error": r.error,
    }


def main():
    parser = argparse.ArgumentParser(description="Gemma Tool Call Evaluation")
    parser.add_argument("--quick", action="store_true", help="Quick smoke test (10 cases)")
    parser.add_argument("--tool", type=str, help="Filter by tool name (substring match)")
    parser.add_argument("--type", type=str, choices=["direct", "inference", "edge", "distractor"],
                        help="Filter by test type")
    parser.add_argument("--complexity", type=str, choices=["simple", "medium", "complex"],
                        help="Filter by complexity level")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to files")
    args = parser.parse_args()

    cases = filter_cases(
        TEST_CASES,
        tool=args.tool,
        test_type=args.type,
        complexity=args.complexity,
        quick=args.quick,
    )

    if not cases:
        print("No test cases match the given filters.")
        sys.exit(1)

    print(f"Selected {len(cases)} test cases")

    results = run_all_cases(cases)
    print_report(results)

    if not args.no_save:
        save_results(results)


if __name__ == "__main__":
    main()
