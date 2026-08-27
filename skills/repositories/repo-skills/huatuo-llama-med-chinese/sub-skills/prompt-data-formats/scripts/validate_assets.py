#!/usr/bin/env python3
"""Validate Huatuo-Llama-Med-Chinese prompt, data, and benchmark assets.

The script intentionally uses only the Python standard library so it can run in
lightweight inspection environments. It validates schema and serialization
shape; it does not run model inference, training, or benchmark scoring.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

CHECK_ORDER = ("templates", "data", "benchmark")
JSONL_DATA_FILES = ("data/infer.json", "data/llama_data.json")
LITERATURE_JSON = "data-literature/liver_cancer.json"
KNOWLEDGE_SAMPLE = "data/knowledge_tuning_data_sample.txt"
BENCHMARK_QUESTIONS = "benchmark/question.json"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Huatuo-Llama-Med-Chinese template JSON, instruction "
            "data, literature JSON, knowledge sample text, and CMCOQA "
            "benchmark question schemas."
        )
    )
    parser.add_argument(
        "--asset-root",
        default=".",
        help="Asset root containing templates/, data/, data-literature/, and/or benchmark/ (default: current directory).",
    )
    parser.add_argument(
        "--check",
        action="append",
        default=None,
        metavar="NAME[,NAME...]",
        help="Checks to run: templates, data, benchmark. May be repeated or comma-separated. Default: all.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Maximum records to validate per data/benchmark file. Default: validate all records.",
    )
    return parser.parse_args(argv)


def normalize_checks(values: Sequence[str] | None) -> list[str]:
    if not values:
        return list(CHECK_ORDER)
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip().lower()
            if not item:
                continue
            if item not in CHECK_ORDER:
                raise ValueError(
                    f"unknown --check value {item!r}; expected one of: {', '.join(CHECK_ORDER)}"
                )
            if item not in seen:
                seen.add(item)
                result.append(item)
    if not result:
        raise ValueError("--check did not name any checks")
    return result


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path, errors: list[str], root: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{rel(path, root)}: file is missing")
    except json.JSONDecodeError as exc:
        errors.append(f"{rel(path, root)}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except UnicodeDecodeError as exc:
        errors.append(f"{rel(path, root)}: not valid UTF-8: {exc}")
    return None


def require_string(record: object, key: str, location: str, errors: list[str], *, allow_empty: bool = False) -> str | None:
    if not isinstance(record, dict):
        errors.append(f"{location}: expected object/dict")
        return None
    if key not in record:
        errors.append(f"{location}: missing required key {key!r}")
        return None
    value = record[key]
    if not isinstance(value, str):
        errors.append(f"{location}: key {key!r} must be a string, got {type(value).__name__}")
        return None
    if not allow_empty and value == "":
        errors.append(f"{location}: key {key!r} must not be empty")
    return value


def bounded_items(items: Iterable[object], max_records: int | None) -> Iterable[tuple[int, object]]:
    for idx, item in enumerate(items, 1):
        if max_records is not None and idx > max_records:
            break
        yield idx, item


def validate_templates(root: Path, max_records: int | None, errors: list[str], warnings: list[str]) -> str:
    del max_records
    template_dir = root / "templates"
    if not template_dir.exists():
        errors.append("templates/: directory is missing")
        return "templates: missing directory"
    paths = sorted(template_dir.glob("*.json"))
    if not paths:
        errors.append("templates/: no .json templates found")
        return "templates: no files"

    checked = 0
    for path in paths:
        checked += 1
        obj = load_json(path, errors, root)
        if obj is None:
            continue
        location = rel(path, root)
        if not isinstance(obj, dict):
            errors.append(f"{location}: template must be a JSON object")
            continue
        description = require_string(obj, "description", location, errors)
        prompt_no_input = require_string(obj, "prompt_no_input", location, errors)
        response_split = require_string(obj, "response_split", location, errors)
        if prompt_no_input is not None and "{instruction}" not in prompt_no_input:
            errors.append(f"{location}: prompt_no_input must contain {{instruction}}")
        if response_split is not None and prompt_no_input is not None and response_split not in prompt_no_input:
            prompt_input_text = obj.get("prompt_input")
            if not isinstance(prompt_input_text, str) or response_split not in prompt_input_text:
                errors.append(
                    f"{location}: response_split {response_split!r} does not appear in prompt_no_input or prompt_input"
                )
        if "prompt_input" in obj:
            prompt_input = require_string(obj, "prompt_input", location, errors)
            if prompt_input is not None and "{instruction}" not in prompt_input:
                errors.append(f"{location}: prompt_input must contain {{instruction}}")
        else:
            warnings.append(
                f"{location}: no prompt_input key; use only with empty input values unless a prompt_input variant is added"
            )
        if description is not None and description.strip() != description:
            warnings.append(f"{location}: description has leading/trailing whitespace")
    return f"templates: checked {checked} template file(s)"


def validate_jsonl_file(path: Path, root: Path, max_records: int | None, errors: list[str]) -> int:
    checked = 0
    if not path.exists():
        errors.append(f"{rel(path, root)}: file is missing")
        return checked
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                if max_records is not None and checked >= max_records:
                    break
                checked += 1
                if stripped.startswith("["):
                    errors.append(f"{rel(path, root)}:{line_no}: expected JSONL object, got a JSON array/list opener")
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"{rel(path, root)}:{line_no}: invalid JSONL record at column {exc.colno}: {exc.msg}"
                    )
                    continue
                location = f"{rel(path, root)}:{line_no}"
                require_string(record, "instruction", location, errors)
                require_string(record, "input", location, errors, allow_empty=True)
                require_string(record, "output", location, errors)
    except UnicodeDecodeError as exc:
        errors.append(f"{rel(path, root)}: not valid UTF-8: {exc}")
    if checked == 0:
        errors.append(f"{rel(path, root)}: no JSONL records found")
    return checked


def validate_literature_json(root: Path, max_records: int | None, errors: list[str]) -> int:
    path = root / LITERATURE_JSON
    obj = load_json(path, errors, root)
    if obj is None:
        return 0
    if not isinstance(obj, list):
        errors.append(f"{rel(path, root)}: expected a JSON list/array")
        return 0
    checked = 0
    for idx, record in bounded_items(obj, max_records):
        checked += 1
        location = f"{rel(path, root)}[{idx}]"
        instruction = require_string(record, "instruction", location, errors)
        require_string(record, "input", location, errors, allow_empty=True)
        require_string(record, "output", location, errors)
        if instruction is not None:
            normalized = instruction.lstrip("\ufeff \t\r\n")
            if not normalized.startswith("<user>:"):
                errors.append(f"{location}: literature instruction should start with '<user>:' after whitespace")
            if "<user>" in instruction and "<user>:" not in instruction:
                errors.append(f"{location}: malformed user dialogue prefix; expected '<user>:'")
            if "<bot>" in instruction and "<bot>:" not in instruction:
                errors.append(f"{location}: malformed bot dialogue prefix; expected '<bot>:'")
    if not obj:
        errors.append(f"{rel(path, root)}: literature list is empty")
    return checked


def validate_knowledge_sample(root: Path, max_records: int | None, errors: list[str]) -> int:
    path = root / KNOWLEDGE_SAMPLE
    if not path.exists():
        errors.append(f"{rel(path, root)}: file is missing")
        return 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        errors.append(f"{rel(path, root)}: not valid UTF-8: {exc}")
        return 0
    if not lines:
        errors.append(f"{rel(path, root)}: file is empty")
        return 0
    if lines[0].strip() != "input":
        errors.append(f"{rel(path, root)}: first line should be the header 'input'")
    data_lines = lines[1:]
    checked = 0
    for idx, line in bounded_items(data_lines, max_records):
        checked += 1
        if not isinstance(line, str) or not line.strip():
            errors.append(f"{rel(path, root)}:{idx + 1}: question line must not be empty")
    if checked == 0:
        errors.append(f"{rel(path, root)}: no question lines found after header")
    return checked


def validate_data(root: Path, max_records: int | None, errors: list[str], warnings: list[str]) -> str:
    del warnings
    jsonl_counts: list[str] = []
    for rel_path in JSONL_DATA_FILES:
        count = validate_jsonl_file(root / rel_path, root, max_records, errors)
        jsonl_counts.append(f"{rel_path}={count}")
    literature_count = validate_literature_json(root, max_records, errors)
    knowledge_count = validate_knowledge_sample(root, max_records, errors)
    return (
        "data: checked "
        + ", ".join(jsonl_counts)
        + f", {LITERATURE_JSON}={literature_count}, {KNOWLEDGE_SAMPLE}={knowledge_count}"
    )


def validate_benchmark(root: Path, max_records: int | None, errors: list[str], warnings: list[str]) -> str:
    del warnings
    path = root / BENCHMARK_QUESTIONS
    obj = load_json(path, errors, root)
    if obj is None:
        return "benchmark: missing or invalid question file"
    if not isinstance(obj, list):
        errors.append(f"{rel(path, root)}: expected a JSON list/array")
        return "benchmark: invalid container"
    if not obj:
        errors.append(f"{rel(path, root)}: question list is empty")
        return "benchmark: empty question list"

    categories: Counter[str] = Counter()
    checked = 0
    for idx, record in bounded_items(obj, max_records):
        checked += 1
        location = f"{rel(path, root)}[{idx}]"
        question = require_string(record, "question", location, errors)
        icd10 = require_string(record, "ICD-10", location, errors)
        if question is not None and question.strip() != question:
            # Leading/trailing whitespace in questions is not fatal, but it often
            # indicates a copy/paste issue that should be reviewed.
            pass
        if icd10:
            categories[icd10] += 1
    category_summary = f", categories={len(categories)}" if categories else ""
    return f"benchmark: checked {checked} question record(s){category_summary}"


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    if args.max_records is not None and args.max_records <= 0:
        print("error: --max-records must be a positive integer", file=sys.stderr)
        return 2
    try:
        checks = normalize_checks(args.check)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    root = Path(args.asset_root).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    summaries: list[str] = []

    if not root.exists():
        print(f"error: --asset-root does not exist: {args.asset_root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: --asset-root is not a directory: {args.asset_root}", file=sys.stderr)
        return 2

    for check in checks:
        if check == "templates":
            summaries.append(validate_templates(root, args.max_records, errors, warnings))
        elif check == "data":
            summaries.append(validate_data(root, args.max_records, errors, warnings))
        elif check == "benchmark":
            summaries.append(validate_benchmark(root, args.max_records, errors, warnings))

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if errors:
        print("asset validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("asset validation passed")
    for summary in summaries:
        print(f"- {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
