#!/usr/bin/env python3
"""Validate preference-pair JSONL for reward-model and DPO-style training.

Expected schema: each JSON line is an object with nonempty string fields
``prompt``, ``chosen``, and ``rejected``. Degenerate rows where chosen equals
rejected are rejected because they contain no pairwise preference signal.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("prompt", "chosen", "rejected")


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


def _clean_field(row: dict, field: str, line_no: int) -> str:
    if field not in row:
        _fail(f"line {line_no}: missing required field {field!r}")
    value = row[field]
    if not isinstance(value, str):
        _fail(f"line {line_no}: field {field!r} must be a string, got {type(value).__name__}")
    if not value.strip():
        _fail(f"line {line_no}: field {field!r} is empty or whitespace")
    return value


def validate(path: Path, limit_rows: int | None, *, warn_long_chars: int | None) -> dict:
    if not path.exists():
        _fail(f"file not found: {path}")
    rows_checked = 0
    blank_lines = 0
    long_prompt_rows = 0
    max_prompt_chars = 0
    max_chosen_chars = 0
    max_rejected_chars = 0
    extra_fields: set[str] = set()

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
            prompt = _clean_field(row, "prompt", line_no)
            chosen = _clean_field(row, "chosen", line_no)
            rejected = _clean_field(row, "rejected", line_no)
            if chosen == rejected:
                _fail(f"line {line_no}: chosen and rejected are identical")
            if chosen.strip() == rejected.strip():
                _fail(f"line {line_no}: chosen and rejected differ only by surrounding whitespace")
            extra_fields.update(k for k in row if k not in REQUIRED_FIELDS)
            rows_checked += 1
            max_prompt_chars = max(max_prompt_chars, len(prompt))
            max_chosen_chars = max(max_chosen_chars, len(chosen))
            max_rejected_chars = max(max_rejected_chars, len(rejected))
            if warn_long_chars is not None and len(prompt) > warn_long_chars:
                long_prompt_rows += 1

    if rows_checked == 0:
        _fail("no nonblank JSONL rows checked")

    return {
        "path": str(path),
        "rows_checked": rows_checked,
        "blank_lines_skipped": blank_lines,
        "extra_fields_seen": sorted(extra_fields),
        "max_prompt_chars": max_prompt_chars,
        "max_chosen_chars": max_chosen_chars,
        "max_rejected_chars": max_rejected_chars,
        "warn_long_chars": warn_long_chars,
        "long_prompt_rows": long_prompt_rows,
    }


def make_fixture(path: Path, *, bad: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"prompt": "Explain photosynthesis briefly.", "chosen": "Plants use light to make sugars.", "rejected": "I do not know."},
        {"prompt": "What is 2 + 2?", "chosen": "4", "rejected": "5"},
    ]
    if bad == "identical":
        rows[1]["rejected"] = rows[1]["chosen"]
    elif bad == "missing":
        del rows[0]["prompt"]
    elif bad == "empty":
        rows[0]["chosen"] = "   "
    with path.open("w", encoding="utf-8") as fh:
        if bad == "invalid-json":
            fh.write('{"prompt": "x", "chosen": "y", "rejected": "z"\n')
            return
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        good = Path(td) / "preferences.jsonl"
        make_fixture(good)
        summary = validate(good, None, warn_long_chars=10)
        assert summary["rows_checked"] == 2
        assert summary["long_prompt_rows"] >= 1

        bad = Path(td) / "bad.jsonl"
        make_fixture(bad, bad="identical")
        try:
            validate(bad, None, warn_long_chars=None)
        except SystemExit as exc:
            assert "identical" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("identical preference fixture should fail")
    print("SELF TEST PASSED")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate preference JSONL rows with prompt/chosen/rejected fields.")
    p.add_argument("path", nargs="?", type=Path, help="Preference JSONL file")
    p.add_argument("--limit-rows", type=_positive_int, default=None, help="Validate at most this many nonblank rows")
    p.add_argument("--warn-long-chars", type=_positive_int, default=8000, help="Warn count for prompts longer than this many characters; use 0 to disable")
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
    warn_long_chars = None if args.warn_long_chars == 0 else args.warn_long_chars
    summary = validate(args.path, args.limit_rows, warn_long_chars=warn_long_chars)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("VALIDATION PASSED")
        print(f"path: {summary['path']}")
        print(f"rows checked: {summary['rows_checked']} | blank lines skipped: {summary['blank_lines_skipped']}")
        print(f"max chars: prompt={summary['max_prompt_chars']} chosen={summary['max_chosen_chars']} rejected={summary['max_rejected_chars']}")
        if summary["extra_fields_seen"]:
            print(f"extra fields seen: {summary['extra_fields_seen']}")
        if summary["warn_long_chars"] is not None and summary["long_prompt_rows"]:
            print(
                f"WARNING: {summary['long_prompt_rows']} checked row(s) have prompts longer than "
                f"{summary['warn_long_chars']} chars; verify stage max_len/context_length before training"
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
