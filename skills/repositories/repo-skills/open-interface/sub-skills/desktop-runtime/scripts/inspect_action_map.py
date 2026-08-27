#!/usr/bin/env python3
"""Validate Open Interface runtime command contracts without GUI or API calls.

This helper mirrors the repository's OpenAI computer-use action conversion and
basic LLM step schema. It deliberately does not import pyautogui, take
screenshots, launch Tk, or contact any model provider.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KEY_MAPPINGS = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "cmd": "command",
    "command": "command",
    "option": "option",
    "alt": "alt",
    "return": "enter",
    "esc": "esc",
    "arrowleft": "left",
    "arrowright": "right",
    "arrowup": "up",
    "arrowdown": "down",
}

BUILTIN_CASES: list[dict[str, Any]] = [
    {
        "id": "click",
        "action": {"type": "click", "x": 10, "y": 20, "button": "left"},
        "expected": [{"function": "click", "parameters": {"x": 10, "y": 20, "button": "left", "clicks": 1}}],
    },
    {
        "id": "double-click",
        "action": {"type": "double_click", "x": 11, "y": 22},
        "expected": [{"function": "click", "parameters": {"x": 11, "y": 22, "button": "left", "clicks": 2}}],
    },
    {
        "id": "move",
        "action": {"type": "move", "x": 33, "y": 44},
        "expected": [{"function": "moveTo", "parameters": {"x": 33, "y": 44}}],
    },
    {
        "id": "scroll",
        "action": {"type": "scroll", "scroll_y": 5},
        "expected": [{"function": "scroll", "parameters": {"clicks": -5}}],
    },
    {
        "id": "type",
        "action": {"type": "type", "text": "hello"},
        "expected": [{"function": "write", "parameters": {"string": "hello", "interval": 0.03}}],
    },
    {
        "id": "wait",
        "action": {"type": "wait"},
        "expected": [{"function": "sleep", "parameters": {"secs": 1}}],
    },
    {
        "id": "keypress-hotkey",
        "action": {"type": "keypress", "keys": ["CTRL", "L"]},
        "expected": [{"function": "hotkey", "parameters": {"keys": ["ctrl", "l"]}}],
    },
    {
        "id": "keypress-single",
        "action": {"type": "keypress", "keys": ["ArrowLeft"]},
        "expected": [{"function": "press", "parameters": {"key": "left"}}],
    },
    {
        "id": "drag",
        "action": {"type": "drag", "path": [[1, 2], [3, 4], [5, 6]]},
        "expected": [
            {"function": "moveTo", "parameters": {"x": 1, "y": 2}},
            {"function": "dragTo", "parameters": {"x": 5, "y": 6, "duration": 0.2, "button": "left"}},
        ],
    },
    {"id": "screenshot", "action": {"type": "screenshot"}, "expected": []},
    {"id": "unsupported", "action": {"type": "swipe"}, "expected": []},
]


def read_obj(obj: Any, key: Any, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    if isinstance(obj, (list, tuple)) and isinstance(key, int):
        if 0 <= key < len(obj):
            return obj[key]
        return default
    return getattr(obj, key, default)


def normalize_key_name(key: str) -> str:
    key_l = str(key).lower()
    return KEY_MAPPINGS.get(key_l, key_l)


def convert_action_to_steps(action: Any) -> list[dict[str, Any]]:
    """Mirror Open Interface's OpenAIComputerUse.convert_action_to_steps."""
    action_type = read_obj(action, "type")

    if action_type == "click":
        return [{
            "function": "click",
            "parameters": {
                "x": read_obj(action, "x"),
                "y": read_obj(action, "y"),
                "button": read_obj(action, "button") or "left",
                "clicks": 1,
            },
        }]

    if action_type == "double_click":
        return [{
            "function": "click",
            "parameters": {"x": read_obj(action, "x"), "y": read_obj(action, "y"), "button": "left", "clicks": 2},
        }]

    if action_type == "move":
        return [{"function": "moveTo", "parameters": {"x": read_obj(action, "x"), "y": read_obj(action, "y")}}]

    if action_type == "scroll":
        scroll_y = read_obj(action, "scroll_y") or 0
        return [{"function": "scroll", "parameters": {"clicks": int(-scroll_y)}}]

    if action_type == "type":
        return [{"function": "write", "parameters": {"string": read_obj(action, "text") or "", "interval": 0.03}}]

    if action_type == "wait":
        return [{"function": "sleep", "parameters": {"secs": 1}}]

    if action_type == "keypress":
        keys = read_obj(action, "keys") or []
        normalized_keys = [normalize_key_name(key) for key in keys if key]
        if len(normalized_keys) == 0:
            return []
        if len(normalized_keys) == 1:
            return [{"function": "press", "parameters": {"key": normalized_keys[0]}}]
        return [{"function": "hotkey", "parameters": {"keys": normalized_keys}}]

    if action_type == "drag":
        path = read_obj(action, "path") or []
        if len(path) < 2:
            return []
        start_x = read_obj(path[0], 0)
        start_y = read_obj(path[0], 1)
        end_x = read_obj(path[-1], 0)
        end_y = read_obj(path[-1], 1)
        if None in [start_x, start_y, end_x, end_y]:
            return []
        return [
            {"function": "moveTo", "parameters": {"x": start_x, "y": start_y}},
            {"function": "dragTo", "parameters": {"x": end_x, "y": end_y, "duration": 0.2, "button": "left"}},
        ]

    if action_type == "screenshot":
        return []

    return []


def validate_step_schema(step: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(step, dict):
        return ["step is not an object"]
    if "function" not in step or not isinstance(step["function"], str) or not step["function"]:
        errors.append("step.function must be a non-empty string")
    if "parameters" in step and not isinstance(step["parameters"], dict):
        errors.append("step.parameters must be an object when present")
    if "human_readable_justification" in step and not isinstance(step["human_readable_justification"], str):
        errors.append("step.human_readable_justification must be a string when present")
    return errors


def validate_llm_response_schema(response: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(response, dict):
        return ["response is not an object"]
    if "steps" not in response:
        errors.append("response.steps is required")
    elif not isinstance(response["steps"], list):
        errors.append("response.steps must be a list")
    else:
        for index, step in enumerate(response["steps"]):
            for error in validate_step_schema(step):
                errors.append(f"steps[{index}]: {error}")
    if "done" not in response:
        errors.append("response.done is required; use null while continuing or a string when finished")
    elif response["done"] is not None and not isinstance(response["done"], str):
        errors.append("response.done must be null or a string")
    return errors


def load_json(path: str | None) -> Any:
    if not path:
        return None
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def normalize_cases(actions: Any, expected: Any | None) -> list[dict[str, Any]]:
    if actions is None:
        return BUILTIN_CASES
    if isinstance(actions, dict) and "steps" in actions and "done" in actions:
        return [{"id": "llm-response", "llm_response": actions, "expected": expected}]
    action_list = actions if isinstance(actions, list) else [actions]
    expected_list: list[Any]
    if expected is None:
        expected_list = [None] * len(action_list)
    elif isinstance(expected, list) and len(action_list) == 1 and (len(expected) == 0 or "function" in (expected[0] if expected else {})):
        expected_list = [expected]
    elif isinstance(expected, list) and len(expected) == len(action_list):
        expected_list = expected
    else:
        raise ValueError("--expect-json must be one expected steps list or a list matching the number of input actions")
    return [
        {"id": f"input-{idx}", "action": action, "expected": expected_list[idx]}
        for idx, action in enumerate(action_list)
    ]


def run_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    failed = 0
    for case in cases:
        if "llm_response" in case:
            errors = validate_llm_response_schema(case["llm_response"])
            ok = not errors
            if not ok:
                failed += 1
            results.append({"id": case.get("id"), "type": "llm-response-schema", "ok": ok, "errors": errors})
            continue
        actual = convert_action_to_steps(case.get("action"))
        expected = case.get("expected")
        ok = expected is None or actual == expected
        if not ok:
            failed += 1
        schema_errors = []
        for index, step in enumerate(actual):
            schema_errors.extend(f"steps[{index}]: {err}" for err in validate_step_schema(step))
        if schema_errors:
            ok = False
            failed += 1
        results.append({
            "id": case.get("id"),
            "type": "action-map",
            "action": case.get("action"),
            "actual": actual,
            "expected": expected,
            "ok": ok,
            "schemaErrors": schema_errors,
        })
    return {"ok": failed == 0, "failed": failed, "results": results}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Open Interface LLM response schema and computer-use action mapping without GUI/API calls."
    )
    parser.add_argument("--input-json", help="JSON file containing one action, a list of actions, or an LLM response object.")
    parser.add_argument("--expect-json", help="Optional JSON file containing expected steps for --input-json actions.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        actions = load_json(args.input_json)
        expected = load_json(args.expect_json)
        report = run_cases(normalize_cases(actions, expected))
    except Exception as exc:  # noqa: BLE001 - intentional CLI boundary
        report = {"ok": False, "failed": 1, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
