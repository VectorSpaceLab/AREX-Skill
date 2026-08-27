#!/usr/bin/env python3
"""Validate FlashRAG config and JSONL input shapes without importing FlashRAG.

The checks are intentionally lightweight: they catch missing files, invalid JSONL,
role-specific required fields, duplicate ids, and common config-risk patterns before
an agent runs expensive indexing or pipeline work.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


CONFIG_KEYS_FOR_SUMMARY = [
    "disable_save",
    "dataset_name",
    "data_dir",
    "split",
    "save_dir",
    "save_note",
    "seed",
    "retrieval_method",
    "corpus_path",
    "index_path",
    "generator_model",
    "framework",
]

REQUIRED_CONFIG_KEYS = [
    "dataset_name",
    "data_dir",
    "split",
    "retrieval_method",
    "generator_model",
    "save_dir",
    "save_note",
    "seed",
]


class Finding:
    def __init__(self, severity: str, path: Path, message: str) -> None:
        self.severity = severity
        self.path = path
        self.message = message

    def format(self) -> str:
        return f"[{self.severity}] {self.path}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate FlashRAG config YAML presence and dataset/corpus JSONL schemas without importing FlashRAG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config my_config.yaml --show-effective-summary
  %(prog)s --eval-jsonl dataset/nq/test.jsonl
  %(prog)s --corpus-jsonl indexes/general_knowledge.jsonl
  %(prog)s --config my_config.yaml --eval-jsonl dataset/nq/test.jsonl --corpus-jsonl indexes/general_knowledge.jsonl
""",
    )
    parser.add_argument("--config", type=Path, help="FlashRAG YAML config to check for presence and lightweight key hints.")
    parser.add_argument("--eval-jsonl", type=Path, action="append", default=[], help="Evaluation dataset JSONL path; may be supplied multiple times.")
    parser.add_argument("--corpus-jsonl", type=Path, action="append", default=[], help="Retrieval corpus JSONL path; may be supplied multiple times.")
    parser.add_argument("--max-rows", type=int, default=0, help="Maximum rows to validate per JSONL file; 0 validates all rows.")
    parser.add_argument("--allow-blank-lines", action="store_true", help="Ignore blank lines in JSONL files instead of reporting them.")
    parser.add_argument("--show-effective-summary", action="store_true", help="Print high-impact config keys found by lightweight YAML scanning.")
    return parser.parse_args()


def add(finding_list: List[Finding], severity: str, path: Path, message: str) -> None:
    finding_list.append(Finding(severity, path, message))


def file_must_exist(path: Optional[Path], findings: List[Finding], label: str) -> bool:
    if path is None:
        return False
    if not path.exists():
        add(findings, "ERROR", path, f"{label} does not exist")
        return False
    if not path.is_file():
        add(findings, "ERROR", path, f"{label} is not a file")
        return False
    return True


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    output = []
    for char in value:
        if escaped:
            output.append(char)
            escaped = False
            continue
        if char == "\\" and in_double:
            output.append(char)
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        if char == "#" and not in_single and not in_double:
            break
        output.append(char)
    return "".join(output).strip()


def parse_scalar(value: str) -> Any:
    value = strip_inline_comment(value)
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"~", "null", "none"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def scan_top_level_yaml(path: Path) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith((" ", "\t", "-")):
            continue
        if ":" not in raw_line:
            continue
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = parse_scalar(raw_value.strip())
    return values


def validate_config(path: Optional[Path], findings: List[Finding], show_summary: bool) -> None:
    if path is None:
        return
    if not file_must_exist(path, findings, "config"):
        return
    if path.suffix.lower() not in {".yaml", ".yml"}:
        add(findings, "WARN", path, "FlashRAG configs are expected to be YAML files ending in .yaml or .yml")
    try:
        scanned = scan_top_level_yaml(path)
    except UnicodeDecodeError as exc:
        add(findings, "ERROR", path, f"cannot read config as UTF-8: {exc}")
        return
    except OSError as exc:
        add(findings, "ERROR", path, f"cannot read config: {exc}")
        return

    if not scanned:
        add(findings, "WARN", path, "no top-level YAML keys detected by lightweight scanner")
        return

    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in scanned]
    if missing:
        add(
            findings,
            "WARN",
            path,
            "missing common top-level config keys; FlashRAG defaults may fill them if using Config defaults: " + ", ".join(missing),
        )

    split = scanned.get("split", "__missing__")
    if split == "__missing__":
        pass
    elif isinstance(split, str):
        add(findings, "INFO", path, "split is a string and FlashRAG Config will normalize it to a one-item list")
    elif split is None:
        add(findings, "INFO", path, "split is null and FlashRAG Config will normalize it to ['train', 'dev', 'test']")

    if scanned.get("disable_save") is not True:
        add(findings, "INFO", path, "disable_save is not true; constructing FlashRAG Config may create a timestamped save_dir")

    if show_summary:
        print(f"Config summary for {path}:")
        for key in CONFIG_KEYS_FOR_SUMMARY:
            if key in scanned:
                print(f"  {key}: {scanned[key]!r}")
            else:
                print(f"  {key}: <not set in this file>")


def iter_jsonl(path: Path, max_rows: int, allow_blank_lines: bool, findings: List[Finding]) -> Iterable[Tuple[int, Dict[str, Any]]]:
    seen_rows = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    if not allow_blank_lines:
                        add(findings, "ERROR", path, f"line {line_number}: blank line is not valid JSONL")
                    continue
                seen_rows += 1
                if max_rows and seen_rows > max_rows:
                    break
                try:
                    value = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    add(findings, "ERROR", path, f"line {line_number}: invalid JSON: {exc.msg}")
                    continue
                if not isinstance(value, dict):
                    add(findings, "ERROR", path, f"line {line_number}: expected a JSON object, got {type(value).__name__}")
                    continue
                yield line_number, value
    except UnicodeDecodeError as exc:
        add(findings, "ERROR", path, f"cannot read JSONL as UTF-8: {exc}")
    except OSError as exc:
        add(findings, "ERROR", path, f"cannot read JSONL: {exc}")


def require_non_empty_string(row: Dict[str, Any], key: str) -> bool:
    return isinstance(row.get(key), str) and bool(row[key].strip())


def validate_eval_jsonl(path: Path, findings: List[Finding], max_rows: int, allow_blank_lines: bool) -> None:
    if not file_must_exist(path, findings, "evaluation JSONL"):
        return
    ids: Dict[str, int] = {}
    row_count = 0
    for line_number, row in iter_jsonl(path, max_rows, allow_blank_lines, findings):
        row_count += 1
        if not require_non_empty_string(row, "question"):
            add(findings, "ERROR", path, f"line {line_number}: evaluation row requires non-empty string field 'question'")
        answers = row.get("golden_answers")
        if not isinstance(answers, list) or not answers or not all(isinstance(item, str) and item for item in answers):
            add(findings, "ERROR", path, f"line {line_number}: evaluation row requires non-empty list[str] field 'golden_answers'")
        if "id" not in row:
            add(findings, "WARN", path, f"line {line_number}: missing recommended field 'id' for traceability")
        else:
            id_key = json.dumps(row["id"], ensure_ascii=False, sort_keys=True)
            if id_key in ids:
                add(findings, "WARN", path, f"line {line_number}: duplicate id also seen on line {ids[id_key]}")
            else:
                ids[id_key] = line_number
        if "contents" in row:
            add(findings, "WARN", path, f"line {line_number}: contains corpus-style field 'contents' in an evaluation file")
    if row_count == 0:
        add(findings, "ERROR", path, "no JSON object rows found")


def validate_corpus_jsonl(path: Path, findings: List[Finding], max_rows: int, allow_blank_lines: bool) -> None:
    if not file_must_exist(path, findings, "corpus JSONL"):
        return
    ids: Dict[str, int] = {}
    row_count = 0
    for line_number, row in iter_jsonl(path, max_rows, allow_blank_lines, findings):
        row_count += 1
        if "id" not in row:
            add(findings, "ERROR", path, f"line {line_number}: corpus row requires field 'id'")
        else:
            id_key = json.dumps(row["id"], ensure_ascii=False, sort_keys=True)
            if id_key in ids:
                add(findings, "WARN", path, f"line {line_number}: duplicate id also seen on line {ids[id_key]}")
            else:
                ids[id_key] = line_number
        if not require_non_empty_string(row, "contents"):
            add(findings, "ERROR", path, f"line {line_number}: corpus row requires non-empty string field 'contents'")
        if "question" in row or "golden_answers" in row:
            add(findings, "WARN", path, f"line {line_number}: contains evaluation-style fields in a corpus file")
    if row_count == 0:
        add(findings, "ERROR", path, "no JSON object rows found")


def main() -> int:
    args = parse_args()
    findings: List[Finding] = []

    if args.max_rows < 0:
        print("--max-rows must be >= 0", file=sys.stderr)
        return 2

    if not args.config and not args.eval_jsonl and not args.corpus_jsonl:
        print("Nothing to validate. Provide --config, --eval-jsonl, or --corpus-jsonl.\n", file=sys.stderr)
        parse_args_for_help = argparse.ArgumentParser(prog=Path(sys.argv[0]).name)
        return 2

    validate_config(args.config, findings, args.show_effective_summary)
    for eval_path in args.eval_jsonl:
        validate_eval_jsonl(eval_path, findings, args.max_rows, args.allow_blank_lines)
    for corpus_path in args.corpus_jsonl:
        validate_corpus_jsonl(corpus_path, findings, args.max_rows, args.allow_blank_lines)

    errors = [finding for finding in findings if finding.severity == "ERROR"]
    warnings = [finding for finding in findings if finding.severity == "WARN"]
    infos = [finding for finding in findings if finding.severity == "INFO"]

    for finding in findings:
        print(finding.format(), file=sys.stderr if finding.severity == "ERROR" else sys.stdout)

    print(
        f"Validation complete: {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info message(s)."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
