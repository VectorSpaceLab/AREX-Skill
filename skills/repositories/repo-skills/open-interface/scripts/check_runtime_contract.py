#!/usr/bin/env python3
"""Check Open Interface JSON response contracts without GUI/API calls.

This root helper validates the high-level LLM response shape used by the app.
For detailed OpenAI computer-use action conversion, run the desktop-runtime
sub-skill's inspect_action_map.py helper.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_TOP_LEVEL_KEYS = {"steps", "done"}
REQUIRED_STEP_KEYS = {"function"}
OPTIONAL_STEP_KEYS = {"parameters", "human_readable_justification"}


def load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_response(obj: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(obj, dict):
        return ["response must be a JSON object"]

    missing = ALLOWED_TOP_LEVEL_KEYS - set(obj)
    for key in sorted(missing):
        errors.append(f"missing top-level key: {key}")

    extra = set(obj) - ALLOWED_TOP_LEVEL_KEYS
    for key in sorted(extra):
        errors.append(f"unexpected top-level key: {key}")

    steps = obj.get("steps")
    if not isinstance(steps, list):
        errors.append("steps must be a list")
    else:
        for index, step in enumerate(steps):
            errors.extend(f"steps[{index}]: {err}" for err in validate_step(step))

    done = obj.get("done")
    if done is not None and not isinstance(done, str):
        errors.append("done must be null while continuing or a string when finished")

    if isinstance(steps, list) and done is None and len(steps) == 0:
        errors.append("done is null and steps is empty; set done to a completion string or include next actions")

    return errors


def validate_step(step: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(step, dict):
        return ["step must be an object"]

    missing = REQUIRED_STEP_KEYS - set(step)
    for key in sorted(missing):
        errors.append(f"missing step key: {key}")

    allowed = REQUIRED_STEP_KEYS | OPTIONAL_STEP_KEYS
    for key in sorted(set(step) - allowed):
        errors.append(f"unexpected step key: {key}")

    function = step.get("function")
    if not isinstance(function, str) or not function.strip():
        errors.append("function must be a non-empty string")

    parameters = step.get("parameters", {})
    if parameters is not None and not isinstance(parameters, dict):
        errors.append("parameters must be an object when present")

    justification = step.get("human_readable_justification")
    if justification is not None and not isinstance(justification, str):
        errors.append("human_readable_justification must be a string when present")

    return errors


def builtin_sample(done: bool = False) -> dict[str, Any]:
    if done:
        return {"steps": [], "done": "Done."}
    return {
        "steps": [
            {
                "function": "press",
                "parameters": {"key": "enter"},
                "human_readable_justification": "Submit the focused control.",
            }
        ],
        "done": None,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Open Interface LLM JSON response shape without launching GUI or provider calls."
    )
    parser.add_argument("json_file", nargs="?", help="JSON response file to validate. If omitted, built-in samples are checked.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    samples = [load_json(args.json_file)] if args.json_file else [builtin_sample(False), builtin_sample(True)]
    results = []
    for index, sample in enumerate(samples):
        errors = validate_response(sample)
        results.append({"id": args.json_file or f"builtin-{index}", "ok": not errors, "errors": errors})
    report = {"ok": all(result["ok"] for result in results), "results": results}
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
