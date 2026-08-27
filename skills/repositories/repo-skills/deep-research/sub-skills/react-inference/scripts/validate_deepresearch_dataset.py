#!/usr/bin/env python3
"""Validate DeepResearch ReAct inference JSON/JSONL datasets.

The validator checks the source dataset shape used by run_multi_react.py and,
when uploaded-file markers are present in question text, verifies that referenced
files are safe relative names inside the supplied file corpus directory.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

UPLOAD_RE = re.compile(r"\(Uploaded\s+\d+\s+files?:\s*(\[[^\]]*\])\)", re.IGNORECASE)


class Finding:
    def __init__(self, level: str, record: int | None, message: str) -> None:
        self.level = level
        self.record = record
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "record": self.record, "message": self.message}

    def __str__(self) -> str:
        prefix = self.level.upper()
        if self.record is not None:
            return f"{prefix} record {self.record}: {self.message}"
        return f"{prefix}: {self.message}"


def load_dataset(path: Path) -> Tuple[List[Dict[str, Any]], List[Finding]]:
    findings: List[Finding] = []
    if not path.exists():
        return [], [Finding("error", None, f"dataset does not exist: {path}")]
    if path.suffix not in {".json", ".jsonl"}:
        return [], [Finding("error", None, "dataset extension must be .json or .jsonl")]

    records: List[Dict[str, Any]] = []
    try:
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return [], [Finding("error", None, "JSON dataset must be an array of objects")]
            for idx, item in enumerate(data, start=1):
                if isinstance(item, dict):
                    records.append(item)
                else:
                    findings.append(Finding("error", idx, "JSON array item is not an object"))
        else:
            with path.open("r", encoding="utf-8") as handle:
                for idx, line in enumerate(handle, start=1):
                    raw = line.rstrip("\n")
                    if raw.strip() == "":
                        findings.append(Finding("error", idx, "blank JSONL lines are not accepted by run_multi_react.py"))
                        continue
                    try:
                        item = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        findings.append(Finding("error", idx, f"invalid JSONL object: {exc}"))
                        continue
                    if not isinstance(item, dict):
                        findings.append(Finding("error", idx, "JSONL line is not an object"))
                        continue
                    records.append(item)
    except UnicodeDecodeError as exc:
        return [], [Finding("error", None, f"dataset is not valid UTF-8: {exc}")]
    except json.JSONDecodeError as exc:
        return [], [Finding("error", None, f"invalid JSON: {exc}")]
    return records, findings


def extract_question_from_messages(item: Dict[str, Any]) -> str | None:
    try:
        content = item["messages"][1]["content"]
        if not isinstance(content, str):
            return None
        return content.split("User:", 1)[1].strip() if "User:" in content else content.strip()
    except Exception:
        return None


def parse_file_refs(question: str) -> Tuple[List[str], List[str]]:
    refs: List[str] = []
    errors: List[str] = []
    for match in UPLOAD_RE.finditer(question):
        raw = match.group(1)
        try:
            value = ast.literal_eval(raw)
        except Exception as exc:
            errors.append(f"could not parse uploaded-file list {raw!r}: {exc}")
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"uploaded-file list must be a list of strings: {raw!r}")
            continue
        refs.extend(value)
    return refs, errors


def is_safe_relative_file(name: str) -> bool:
    if name.strip() == "":
        return False
    path = Path(name)
    if path.is_absolute():
        return False
    if any(part in {"", ".", ".."} for part in path.parts):
        return False
    return True


def validate_records(records: Sequence[Dict[str, Any]], args: argparse.Namespace) -> Tuple[List[Finding], Dict[str, Any]]:
    findings: List[Finding] = []
    seen_questions = set()
    file_refs: List[Tuple[int, str]] = []

    for idx, item in enumerate(records, start=1):
        question = item.get("question")
        if question is None or question == "":
            fallback = extract_question_from_messages(item)
            if fallback and args.allow_messages_fallback:
                question = fallback
                findings.append(Finding("warning", idx, "question is empty; messages fallback would be used by run_multi_react.py"))
            else:
                findings.append(Finding("error", idx, "missing or empty string field: question"))
                question = ""
        elif not isinstance(question, str):
            findings.append(Finding("error", idx, "question must be a string"))
            question = str(question)

        if "answer" not in item:
            findings.append(Finding("error", idx, "missing field: answer"))
        elif not isinstance(item.get("answer"), str):
            findings.append(Finding("error", idx, "answer must be a string"))
        elif item.get("answer") == "" and not args.allow_empty_answer:
            findings.append(Finding("warning", idx, "answer is empty; this is acceptable for inference but not for judged benchmark scoring"))

        stripped = question.strip()
        if stripped:
            if stripped in seen_questions:
                findings.append(Finding("warning", idx, "duplicate question; resume logic treats processed questions by stripped question text"))
            seen_questions.add(stripped)

        refs, ref_errors = parse_file_refs(question)
        for error in ref_errors:
            findings.append(Finding("error", idx, error))
        for ref in refs:
            file_refs.append((idx, ref))

    if file_refs:
        if args.file_corpus is None:
            findings.append(Finding("error", None, "file references were found but --file-corpus was not supplied"))
        else:
            corpus = args.file_corpus
            if not corpus.exists() or not corpus.is_dir():
                findings.append(Finding("error", None, "--file-corpus must be an existing directory"))
            else:
                corpus_resolved = corpus.resolve()
                for idx, ref in file_refs:
                    if not is_safe_relative_file(ref):
                        findings.append(Finding("error", idx, f"unsafe file reference {ref!r}; use a relative file name inside file_corpus"))
                        continue
                    candidate = (corpus / ref).resolve()
                    try:
                        candidate.relative_to(corpus_resolved)
                    except ValueError:
                        findings.append(Finding("error", idx, f"file reference escapes file_corpus: {ref!r}"))
                        continue
                    if not candidate.exists() or not candidate.is_file():
                        findings.append(Finding("error", idx, f"referenced file is missing from file_corpus: {ref!r}"))

    summary = {
        "records": len(records),
        "unique_questions": len(seen_questions),
        "file_reference_count": len(file_refs),
        "file_reference_records": sorted({idx for idx, _ in file_refs}),
    }
    return findings, summary


def emit(findings: Iterable[Finding], summary: Dict[str, Any], json_mode: bool) -> None:
    findings = list(findings)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    if json_mode:
        print(json.dumps({"ok": not errors, "summary": summary, "findings": [f.to_dict() for f in findings]}, indent=2))
        return
    print("DeepResearch dataset validation summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    for finding in findings:
        stream = sys.stderr if finding.level == "error" else sys.stdout
        print(str(finding), file=stream)
    if not errors:
        print("Dataset validation passed.")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate JSON/JSONL datasets for DeepResearch ReAct inference.")
    parser.add_argument("dataset", type=Path, help="input .json or .jsonl dataset with question and answer fields")
    parser.add_argument("--file-corpus", type=Path, help="directory containing files referenced by '(Uploaded ...)' markers")
    parser.add_argument("--allow-empty-answer", action="store_true", help="suppress warnings for empty answer fields")
    parser.add_argument("--allow-messages-fallback", action="store_true", help="allow empty question records when messages[1].content can provide the question")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON report")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    records, load_findings = load_dataset(args.dataset)
    findings = list(load_findings)
    if not any(f.level == "error" for f in load_findings):
        record_findings, summary = validate_records(records, args)
        findings.extend(record_findings)
    else:
        summary = {"records": len(records), "unique_questions": 0, "file_reference_count": 0, "file_reference_records": []}
    emit(findings, summary, args.json)
    return 1 if any(f.level == "error" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
