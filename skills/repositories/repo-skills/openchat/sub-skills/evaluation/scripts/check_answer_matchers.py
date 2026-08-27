#!/usr/bin/env python3
"""Run tiny synthetic checks for OpenChat evaluation answer matchers.

By default this imports the installed OpenChat matchers and verifies representative
multiple-choice, GSM8K numeric, and HumanEval extraction behavior. Use
--standalone only to validate the bundled smoke-test logic when OpenChat's full
evaluation dependencies are not importable; standalone mode is not proof that
the installed OpenChat package can run benchmarks.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from typing import Any, Callable

Matcher = Callable[[dict[str, Any], str], tuple[bool, Any]]


def _standalone_mc(task_data: dict[str, Any], response: str) -> tuple[bool, str]:
    for char in response:
        if char in task_data["options"]:
            return True, char
    return False, ""


def _standalone_gsm8k(task_data: dict[str, Any], response: str) -> tuple[bool, str]:
    matches = re.findall(r"\d*\.?\d+", response)
    if matches:
        return True, matches[-1]
    return False, response


def _function_exists(code: str, func_name: str) -> bool:
    tree = ast.parse(code)
    return any(isinstance(node, ast.FunctionDef) and node.name == func_name for node in ast.walk(tree))


def _code_blocks_and_raw(content: str) -> list[str]:
    blocks = [m[1] for m in re.findall(r"(`{3}.*?\n+)([\s\S]*?)(\n+`{3})", content)]
    blocks.append(content)
    return blocks


def _try_humaneval_match(content: str, prefix: str, entry_point: str) -> str | None:
    for block in _code_blocks_and_raw(content):
        try:
            completion = prefix + block
            if _function_exists(completion, entry_point):
                return completion
        except SyntaxError:
            continue
    return None


def _standalone_humaneval(task_data: dict[str, Any], response: str) -> tuple[bool, dict[str, str]]:
    metadata = task_data["_metadata"]
    include_prefix = metadata["prompt"].split("def")[0].strip() + "\n\n"

    result = _try_humaneval_match(response, include_prefix, metadata["entry_point"])
    if result:
        return True, {"task_id": metadata["task_id"], "completion": result}

    result = _try_humaneval_match(response, metadata["prompt"], metadata["entry_point"])
    if result:
        return True, {"task_id": metadata["task_id"], "completion": result}

    return False, {"task_id": metadata["task_id"], "completion": response}


def load_matchers(*, standalone: bool) -> dict[str, Matcher]:
    if standalone:
        return {
            "multiple-choice": _standalone_mc,
            "gsm8k": _standalone_gsm8k,
            "humaneval": _standalone_humaneval,
        }

    try:
        from ochat.evaluation.match_answer import MATCH_ANSWER_FUNCTION
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Could not import installed OpenChat answer matchers. "
            "Install OpenChat with evaluation dependencies, or rerun with --standalone "
            "only to test the bundled smoke-test logic. "
            f"Import error: {type(exc).__name__}: {exc}"
        ) from exc

    return {
        "multiple-choice": MATCH_ANSWER_FUNCTION["zs/bbh_mc_orca"],
        "gsm8k": MATCH_ANSWER_FUNCTION["fs_cothub/gsm8k"],
        "humaneval": MATCH_ANSWER_FUNCTION["coding/humaneval"],
    }


def check_multiple_choice(fn: Matcher) -> dict[str, Any]:
    task = {"options": ["A", "B", "C", "D"], "label": ["C"]}
    matched, answer = fn(task, "final option: C")
    assert matched is True, "multiple-choice matcher did not report a match"
    assert answer == "C", f"expected C, got {answer!r}"
    return {"case": "multiple-choice", "matched": matched, "answer": answer, "correct": answer in task["label"]}


def check_gsm8k(fn: Matcher) -> dict[str, Any]:
    task = {"options": None, "label": ["42"]}
    matched, answer = fn(task, "We compute 6 * 7 = 42. Therefore the answer is 42.")
    assert matched is True, "GSM8K matcher did not report a match"
    assert answer == "42", f"expected last numeric answer 42, got {answer!r}"
    return {"case": "gsm8k", "matched": matched, "answer": answer, "correct": answer in task["label"]}


def check_humaneval(fn: Matcher) -> dict[str, Any]:
    task = {
        "options": [],
        "label": "",
        "_metadata": {
            "task_id": "HumanEval/0",
            "prompt": "def add(a: int, b: int) -> int:\n",
            "entry_point": "add",
        },
    }
    response = "```python\ndef add(a: int, b: int) -> int:\n    return a + b\n```"
    matched, answer = fn(task, response)
    assert matched is True, "HumanEval matcher did not report a match"
    assert isinstance(answer, dict), f"expected answer object, got {type(answer).__name__}"
    assert answer.get("task_id") == "HumanEval/0", f"unexpected task_id: {answer!r}"
    assert "def add" in answer.get("completion", ""), "completion does not define the entry point"
    return {
        "case": "humaneval",
        "matched": matched,
        "task_id": answer["task_id"],
        "completion_contains_entry_point": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run synthetic checks for OpenChat answer matcher behavior.")
    parser.add_argument(
        "--case",
        choices=["all", "multiple-choice", "gsm8k", "humaneval"],
        default="all",
        help="Which synthetic matcher check to run.",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Use bundled mini-matchers instead of importing installed OpenChat matchers.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    matchers = load_matchers(standalone=args.standalone)

    checks: list[tuple[str, Callable[[Matcher], dict[str, Any]]]] = [
        ("multiple-choice", check_multiple_choice),
        ("gsm8k", check_gsm8k),
        ("humaneval", check_humaneval),
    ]
    if args.case != "all":
        checks = [item for item in checks if item[0] == args.case]

    results = [check(matchers[name]) for name, check in checks]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        mode = "standalone smoke logic" if args.standalone else "installed OpenChat matchers"
        print(f"checked {len(results)} case(s) using {mode}")
        for result in results:
            print(f"- {result['case']}: matched={result['matched']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
