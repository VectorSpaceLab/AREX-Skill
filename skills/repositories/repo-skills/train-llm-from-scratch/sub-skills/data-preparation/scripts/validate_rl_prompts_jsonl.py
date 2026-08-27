#!/usr/bin/env python3
"""Validate RL prompt JSONL for PPO/GRPO and arithmetic curriculum files.

Expected schema: each JSON line is an object with a nonempty string ``prompt``
and a ``gold`` field. For verifier-based GSM8K/arithmetic runs, ``gold`` should
be a JSON number. Some custom prompt sets may allow ``null`` by policy.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


_ARITH_RE = re.compile(r"^\s*What\s+is\s+(-?\d+(?:\.\d+)?)\s*([+\-*])\s*(-?\d+(?:\.\d+)?)\?\s*$", re.IGNORECASE)


def _positive_int(value: str) -> int:
    try:
        out = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if out <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return out


def _fail(message: str) -> None:
    raise SystemExit(f"VALIDATION FAILED: {message}")


def _load_json(line: str, line_no: int) -> Any:
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        _fail(f"line {line_no}: invalid JSON: {exc.msg}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _arithmetic_expected(prompt: str) -> float | None:
    match = _ARITH_RE.match(prompt)
    if not match:
        return None
    a = float(match.group(1))
    op = match.group(2)
    b = float(match.group(3))
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    return None


def validate(path: Path, limit_rows: int | None, *, gold_policy: str, arithmetic_sanity: bool) -> dict:
    if not path.exists():
        _fail(f"file not found: {path}")

    rows_checked = 0
    blank_lines = 0
    numeric_gold = 0
    null_gold = 0
    max_prompt_chars = 0
    arithmetic_checked = 0
    arithmetic_nonmatching = 0

    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if limit_rows is not None and rows_checked >= limit_rows:
                break
            if not line.strip():
                blank_lines += 1
                continue
            row = _load_json(line, line_no)
            if not isinstance(row, dict):
                _fail(f"line {line_no}: row must be a JSON object, got {type(row).__name__}")
            if "prompt" not in row:
                _fail(f"line {line_no}: missing required field 'prompt'")
            if not isinstance(row["prompt"], str):
                _fail(f"line {line_no}: field 'prompt' must be a string, got {type(row['prompt']).__name__}")
            prompt = row["prompt"]
            if not prompt.strip():
                _fail(f"line {line_no}: field 'prompt' is empty or whitespace")
            if "gold" not in row:
                _fail(f"line {line_no}: missing required field 'gold'")
            gold = row["gold"]
            if _is_number(gold):
                numeric_gold += 1
            elif gold is None:
                null_gold += 1
                if gold_policy == "numeric":
                    _fail(f"line {line_no}: gold is null but --gold-policy numeric requires a number")
            else:
                _fail(f"line {line_no}: gold must be a JSON number or null, got {gold!r}")

            if gold_policy == "nullable" and gold is None:
                pass
            elif gold_policy in ("numeric", "nullable") and not _is_number(gold):
                _fail(f"line {line_no}: gold must be numeric under policy {gold_policy!r}")

            if arithmetic_sanity:
                expected = _arithmetic_expected(prompt)
                if expected is None:
                    arithmetic_nonmatching += 1
                else:
                    arithmetic_checked += 1
                    if not _is_number(gold):
                        _fail(f"line {line_no}: arithmetic prompt has nonnumeric gold {gold!r}")
                    if not math.isclose(float(gold), expected, rel_tol=0.0, abs_tol=1e-9):
                        _fail(f"line {line_no}: arithmetic gold {gold!r} does not match prompt result {expected}")

            rows_checked += 1
            max_prompt_chars = max(max_prompt_chars, len(prompt))

    if rows_checked == 0:
        _fail("no nonblank JSONL rows checked")
    if arithmetic_sanity and arithmetic_checked == 0:
        _fail("--arithmetic-sanity was requested but no checked row matched 'What is A +|-|* B?' pattern")

    return {
        "path": str(path),
        "rows_checked": rows_checked,
        "blank_lines_skipped": blank_lines,
        "numeric_gold_rows": numeric_gold,
        "null_gold_rows": null_gold,
        "gold_policy": gold_policy,
        "max_prompt_chars": max_prompt_chars,
        "arithmetic_sanity": arithmetic_sanity,
        "arithmetic_rows_checked": arithmetic_checked,
        "arithmetic_rows_not_matching_pattern": arithmetic_nonmatching,
    }


def make_fixture(path: Path, *, bad: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"prompt": "What is 2 + 2?", "gold": 4.0},
        {"prompt": "What is 7 * 6?", "gold": 42},
    ]
    if bad == "nonnumeric":
        rows[0]["gold"] = "4"
    elif bad == "bad-arithmetic":
        rows[1]["gold"] = 41
    elif bad == "null":
        rows[0]["gold"] = None
    elif bad == "missing-prompt":
        del rows[0]["prompt"]
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        good = Path(td) / "rl.jsonl"
        make_fixture(good)
        summary = validate(good, None, gold_policy="numeric", arithmetic_sanity=True)
        assert summary["rows_checked"] == 2
        assert summary["arithmetic_rows_checked"] == 2

        bad = Path(td) / "bad.jsonl"
        make_fixture(bad, bad="bad-arithmetic")
        try:
            validate(bad, None, gold_policy="numeric", arithmetic_sanity=True)
        except SystemExit as exc:
            assert "does not match" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("bad arithmetic fixture should fail")
    print("SELF TEST PASSED")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate RL prompt JSONL rows with prompt/gold fields.")
    p.add_argument("path", nargs="?", type=Path, help="RL prompt JSONL file")
    p.add_argument("--limit-rows", type=_positive_int, default=None, help="Validate at most this many nonblank rows")
    p.add_argument(
        "--gold-policy",
        choices=["numeric", "nullable"],
        default="numeric",
        help="Whether gold must be numeric or may be null; verifier GSM8K/arithmetic runs should use numeric",
    )
    p.add_argument("--arithmetic-sanity", action="store_true", help="Check prompts shaped like 'What is A +|-|* B?' against numeric gold")
    p.add_argument("--json", action="store_true", help="Emit JSON summary only")
    p.add_argument("--self-test", action="store_true", help="Run temporary fixture checks and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0
    if args.path is None:
        raise SystemExit("path is required unless --self-test is used")
    summary = validate(args.path, args.limit_rows, gold_policy=args.gold_policy, arithmetic_sanity=args.arithmetic_sanity)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("VALIDATION PASSED")
        print(f"path: {summary['path']}")
        print(f"rows checked: {summary['rows_checked']} | blank lines skipped: {summary['blank_lines_skipped']}")
        print(f"gold rows: numeric={summary['numeric_gold_rows']} null={summary['null_gold_rows']} policy={summary['gold_policy']}")
        print(f"max prompt chars: {summary['max_prompt_chars']}")
        if summary["arithmetic_sanity"]:
            print(
                f"arithmetic checked: {summary['arithmetic_rows_checked']} | "
                f"nonmatching pattern rows: {summary['arithmetic_rows_not_matching_pattern']}"
            )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(1)
