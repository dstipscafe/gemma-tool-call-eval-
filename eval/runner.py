"""
Evaluation runner — sends test cases to the Gemma API and collects results.
"""

from __future__ import annotations

import json
import time
import sys

from openai import OpenAI

import config
from tools.definitions import ALL_TOOLS
from tools.mock_handlers import get_mock_response
from eval.metrics import CaseResult, evaluate_case


def create_client() -> OpenAI:
    return OpenAI(
        base_url=config.API_BASE_URL,
        api_key=config.API_KEY,
        timeout=config.REQUEST_TIMEOUT,
    )


def run_single_case(
    client: OpenAI, test_case: dict, case_index: int, total: int
) -> CaseResult:
    """Run a single test case against the model and return the evaluation result."""
    case_id = test_case["id"]
    print(f"  [{case_index+1}/{total}] {case_id} ...", end=" ", flush=True)

    actual_tool_name = None
    actual_parameters = None
    raw_response = ""
    response_time_ms = 0.0
    error = None

    for attempt in range(config.MAX_RETRIES):
        try:
            start = time.perf_counter()
            response = client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant with access to tools. "
                            "When the user's request can be fulfilled by calling a tool, "
                            "you MUST call the appropriate tool with the correct parameters. "
                            "Do not ask for confirmation — just call the tool directly."
                        ),
                    },
                    {"role": "user", "content": test_case["prompt"]},
                ],
                tools=ALL_TOOLS,
                tool_choice="auto",
            )
            elapsed = time.perf_counter() - start
            response_time_ms = elapsed * 1000

            raw_response = response.model_dump_json()

            # Extract tool call from response
            message = response.choices[0].message
            if message.tool_calls and len(message.tool_calls) > 0:
                tool_call = message.tool_calls[0]
                actual_tool_name = tool_call.function.name
                try:
                    actual_parameters = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    actual_parameters = None
                    error = f"Invalid JSON in arguments: {tool_call.function.arguments[:200]}"
            else:
                # Model didn't make a tool call
                error = f"No tool call in response. Content: {(message.content or '')[:200]}"

            break  # success, no retry needed

        except Exception as e:
            error = f"API error (attempt {attempt+1}): {str(e)}"
            if attempt < config.MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # exponential backoff
            continue

    result = evaluate_case(
        test_case=test_case,
        actual_tool_name=actual_tool_name,
        actual_parameters=actual_parameters,
        raw_response=raw_response,
        response_time_ms=response_time_ms,
    )
    result.error = error

    # Print inline status
    if result.required_params_correct:
        print("✓", flush=True)
    elif result.tool_selected_correctly:
        print("~ (tool ok, params wrong)", flush=True)
    elif result.valid_json:
        print("✗ (wrong tool)", flush=True)
    else:
        print("✗ (no tool call)", flush=True)

    return result


def run_all_cases(test_cases: list[dict]) -> list[CaseResult]:
    """Run all test cases sequentially and return results."""
    client = create_client()
    results: list[CaseResult] = []
    total = len(test_cases)

    print(f"\nStarting evaluation: {total} test cases")
    print(f"Model: {config.MODEL_NAME} @ {config.API_BASE_URL}")
    print("=" * 60)

    for i, case in enumerate(test_cases):
        result = run_single_case(client, case, i, total)
        results.append(result)

    print("=" * 60)
    print(f"Completed: {len(results)}/{total} cases\n")

    return results
