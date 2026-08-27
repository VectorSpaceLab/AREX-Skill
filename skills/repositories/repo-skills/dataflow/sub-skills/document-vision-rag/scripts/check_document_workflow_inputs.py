#!/usr/bin/env python3
"""Validate document workflow inputs without network calls.

Checks performed:
- document paths and directories
- PDF suffix expectations
- JSON/JSONL record columns
- requested environment variables

The script never downloads data, calls APIs, or starts models.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SKIP_DIRS = {".cache", ".git", ".venv", "venv", "__pycache__", "node_modules"}

PROFILE_RULES = {
    "kbc": {
        "required_columns": ("source",),
        "allow_empty_columns": (),
        "allowed_suffixes": {".pdf", ".txt", ".md", ".html", ".xml", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".json", ".jsonl"},
        "allow_urls": True,
    },
    "pdf2vqa": {
        "required_columns": ("input_pdf_paths", "name"),
        "allow_empty_columns": (),
        "allowed_suffixes": {".pdf"},
        "allow_urls": False,
    },
    "rag": {
        "required_columns": (),
        "allow_empty_columns": (),
        "allowed_suffixes": {".txt", ".md", ".json", ".jsonl", ".html", ".xml"},
        "allow_urls": False,
    },
    "speech": {
        "required_columns": ("raw_content",),
        "allow_empty_columns": (),
        "allowed_suffixes": {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac", ".mp4", ".webm"},
        "allow_urls": True,
    },
    "chemistry": {
        "required_columns": ("text",),
        "allow_empty_columns": (),
        "allowed_suffixes": {".json", ".jsonl", ".csv", ".txt", ".md"},
        "allow_urls": False,
    },
    "pdf2model-kbc": {
        "required_columns": ("instruction", "input", "output"),
        "allow_empty_columns": ("input",),
        "allowed_suffixes": {".json", ".jsonl"},
        "allow_urls": False,
    },
    "pdf2model-vqa": {
        "required_columns": ("messages", "images"),
        "allow_empty_columns": (),
        "allowed_suffixes": {".json", ".jsonl"},
        "allow_urls": False,
    },
}


@dataclass
class Finding:
    level: str
    location: str
    message: str


def is_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def as_items(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def resolve_relative(raw: str, base_dir: Path) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate

    base_candidate = (base_dir / candidate).resolve()
    if base_candidate.exists():
        return base_candidate

    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    return base_candidate


def collect_files(path: Path, recursive: bool) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []

    files: list[Path] = []
    iterator = path.rglob("*") if recursive else path.iterdir()
    for item in iterator:
        if not item.is_file():
            continue
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        if any(part.startswith(".") and part not in {".", ".."} for part in item.parts):
            continue
        files.append(item)
    return files


def load_records(json_path: Path) -> list[tuple[str, dict[str, Any]]]:
    suffix = json_path.suffix.lower()
    payload = json_path.read_text(encoding="utf-8")

    if suffix == ".jsonl":
        records: list[tuple[str, dict[str, Any]]] = []
        for line_no, line in enumerate(payload.splitlines(), 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{json_path}:{line_no} must be a JSON object")
            records.append((f"{json_path.name}:{line_no}", obj))
        return records

    if suffix == ".json":
        obj = json.loads(payload)
        if isinstance(obj, dict):
            return [(json_path.name, obj)]
        if isinstance(obj, list):
            records = []
            for idx, item in enumerate(obj, 1):
                if not isinstance(item, dict):
                    raise ValueError(f"{json_path}:{idx} must be a JSON object")
                records.append((f"{json_path.name}#{idx}", item))
            return records
        raise ValueError(f"{json_path} must contain a JSON object or array of objects")

    raise ValueError(f"{json_path} must end with .json or .jsonl")


def add_finding(findings: list[Finding], level: str, location: str, message: str) -> None:
    findings.append(Finding(level=level, location=location, message=message))


def validate_file_suffix(path: Path, allowed_suffixes: set[str], expect_pdf: bool, location: str, findings: list[Finding]) -> None:
    suffix = path.suffix.lower()
    if expect_pdf and suffix != ".pdf":
        add_finding(findings, "error", location, f"expected a PDF suffix, got {suffix or '<no suffix>'}")
        return

    if allowed_suffixes and suffix not in allowed_suffixes:
        add_finding(findings, "error", location, f"unsupported suffix {suffix or '<no suffix>'}")


def validate_pathish(
    value: Any,
    *,
    field: str,
    location: str,
    base_dir: Path,
    allowed_suffixes: set[str],
    allow_urls: bool,
    expect_pdf: bool,
    recursive: bool,
    findings: list[Finding],
) -> None:
    items = as_items(value)
    if not items or all(is_empty(item) for item in items):
        add_finding(findings, "error", location, f"field '{field}' is empty")
        return

    for idx, item in enumerate(items):
        item_loc = f"{location}.{field}[{idx}]" if len(items) > 1 else f"{location}.{field}"
        if not isinstance(item, str) or not item.strip():
            add_finding(findings, "error", item_loc, "must be a non-empty string")
            continue

        text = item.strip()
        if is_url(text):
            if not allow_urls:
                add_finding(findings, "error", item_loc, "URLs are not allowed in this profile")
                continue
            if expect_pdf and not text.lower().split("?")[0].endswith(".pdf"):
                add_finding(findings, "warning", item_loc, "remote PDF suffix cannot be verified offline")
            continue

        path = resolve_relative(text, base_dir)
        if path.is_dir():
            files = collect_files(path, recursive=recursive)
            if not files:
                add_finding(findings, "error", item_loc, f"directory contains no files: {path}")
                continue
            for file_path in files:
                file_loc = f"{item_loc}:{file_path.name}"
                validate_file_suffix(file_path, allowed_suffixes, expect_pdf, file_loc, findings)
            continue

        if not path.exists():
            add_finding(findings, "error", item_loc, f"path does not exist: {path}")
            continue

        validate_file_suffix(path, allowed_suffixes, expect_pdf, item_loc, findings)


def validate_required_columns(
    record: dict[str, Any],
    *,
    required_columns: tuple[str, ...],
    allow_empty_columns: tuple[str, ...],
    location: str,
    findings: list[Finding],
) -> None:
    for column in required_columns:
        if column not in record:
            add_finding(findings, "error", location, f"missing required column '{column}'")
            continue
        if column not in allow_empty_columns and is_empty(record[column]):
            add_finding(findings, "error", location, f"column '{column}' is empty")


def validate_messages(value: Any, location: str, findings: list[Finding]) -> None:
    if not isinstance(value, list) or not value:
        add_finding(findings, "error", location, "messages must be a non-empty list")
        return
    for idx, message in enumerate(value):
        if not isinstance(message, dict):
            add_finding(findings, "error", f"{location}.messages[{idx}]", "message must be an object")
            continue
        if "role" not in message or "content" not in message:
            add_finding(findings, "error", f"{location}.messages[{idx}]", "message must contain role and content")


def validate_record_profile(
    profile: str,
    record: dict[str, Any],
    *,
    location: str,
    base_dir: Path,
    expect_pdf: bool,
    recursive: bool,
    findings: list[Finding],
) -> None:
    rules = PROFILE_RULES[profile]
    validate_required_columns(
        record,
        required_columns=rules["required_columns"],
        allow_empty_columns=rules["allow_empty_columns"],
        location=location,
        findings=findings,
    )

    if profile == "kbc" and "source" in record:
        validate_pathish(
            record["source"],
            field="source",
            location=location,
            base_dir=base_dir,
            allowed_suffixes=rules["allowed_suffixes"],
            allow_urls=rules["allow_urls"],
            expect_pdf=expect_pdf,
            recursive=recursive,
            findings=findings,
        )
        return

    if profile == "pdf2vqa" and "input_pdf_paths" in record:
        validate_pathish(
            record["input_pdf_paths"],
            field="input_pdf_paths",
            location=location,
            base_dir=base_dir,
            allowed_suffixes=rules["allowed_suffixes"],
            allow_urls=rules["allow_urls"],
            expect_pdf=True,
            recursive=recursive,
            findings=findings,
        )
        if "name" in record and is_empty(record["name"]):
            add_finding(findings, "error", location, "column 'name' is empty")
        return

    if profile == "rag":
        return

    if profile == "speech" and "raw_content" in record:
        validate_pathish(
            record["raw_content"],
            field="raw_content",
            location=location,
            base_dir=base_dir,
            allowed_suffixes=rules["allowed_suffixes"],
            allow_urls=rules["allow_urls"],
            expect_pdf=False,
            recursive=recursive,
            findings=findings,
        )
        return

    if profile == "chemistry":
        if is_empty(record.get("text")):
            add_finding(findings, "error", location, "column 'text' is empty")
        if "abbreviations" in record and is_empty(record["abbreviations"]):
            add_finding(findings, "warning", location, "column 'abbreviations' is empty")
        return

    if profile == "pdf2model-kbc":
        if is_empty(record.get("instruction")):
            add_finding(findings, "error", location, "column 'instruction' is empty")
        if is_empty(record.get("output")):
            add_finding(findings, "error", location, "column 'output' is empty")
        return

    if profile == "pdf2model-vqa":
        validate_messages(record.get("messages"), location, findings)
        images = record.get("images")
        if not isinstance(images, list) or not images:
            add_finding(findings, "error", location, "images must be a non-empty list")
            return
        for idx, image in enumerate(images):
            image_loc = f"{location}.images[{idx}]"
            if not isinstance(image, str) or not image.strip():
                add_finding(findings, "error", image_loc, "image path must be a non-empty string")
                continue
            image_path = resolve_relative(image, base_dir)
            if not image_path.exists():
                add_finding(findings, "error", image_loc, f"image path does not exist: {image_path}")
        return


def validate_docs(
    profile: str,
    doc_inputs: list[str],
    *,
    expect_pdf: bool,
    recursive: bool,
    findings: list[Finding],
) -> None:
    if not doc_inputs:
        return

    rules = PROFILE_RULES[profile]
    allowed_suffixes = set(rules["allowed_suffixes"])
    if expect_pdf:
        allowed_suffixes = {".pdf"}

    for raw in doc_inputs:
        loc = f"doc:{raw}"
        if not isinstance(raw, str) or not raw.strip():
            add_finding(findings, "error", loc, "document path must be a non-empty string")
            continue

        text = raw.strip()
        if is_url(text):
            if not rules["allow_urls"]:
                add_finding(findings, "error", loc, "URLs are not allowed in this profile")
            elif expect_pdf and not text.lower().split("?")[0].endswith(".pdf"):
                add_finding(findings, "warning", loc, "remote PDF suffix cannot be verified offline")
            continue

        path = resolve_relative(text, Path.cwd())
        if not path.exists():
            add_finding(findings, "error", loc, f"path does not exist: {path}")
            continue

        if path.is_dir():
            files = collect_files(path, recursive=recursive)
            if not files:
                add_finding(findings, "error", loc, f"directory contains no files: {path}")
                continue
            for file_path in files:
                file_loc = f"{loc}:{file_path.name}"
                validate_file_suffix(file_path, allowed_suffixes, expect_pdf, file_loc, findings)
            continue

        validate_file_suffix(path, allowed_suffixes, expect_pdf, loc, findings)


def validate_env_vars(env_names: list[str], findings: list[Finding]) -> None:
    for name in env_names:
        value = os.environ.get(name)
        if value is None or value.strip() == "":
            add_finding(findings, "error", f"env:{name}", f"environment variable '{name}' is missing")


def print_findings(findings: list[Finding]) -> None:
    for item in findings:
        prefix = item.level.upper()
        loc = f" [{item.location}]" if item.location else ""
        print(f"{prefix}{loc}: {item.message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate document workflow inputs without network calls.",
        epilog="Profiles: kbc, pdf2vqa, rag, speech, chemistry, pdf2model-kbc, pdf2model-vqa",
    )
    parser.add_argument("--profile", required=True, choices=sorted(PROFILE_RULES.keys()), help="Workflow profile to validate")
    parser.add_argument("--doc", action="append", default=[], help="Document path, directory, or URL. Repeatable.")
    parser.add_argument("--jsonl", type=Path, default=None, help="JSON or JSONL manifest to validate.")
    parser.add_argument("--require-column", action="append", default=[], help="Extra required JSON field. Repeatable.")
    parser.add_argument("--require-env", action="append", default=[], help="Environment variable that must be set. Repeatable.")
    parser.add_argument("--expect-pdf", action="store_true", help="Require local document paths to end with .pdf.")
    parser.add_argument("--no-recursive", action="store_true", help="Do not recurse into directories.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    recursive = not args.no_recursive
    rules = PROFILE_RULES[args.profile]
    expect_pdf = bool(args.expect_pdf or args.profile == "pdf2vqa")

    validate_docs(
        args.profile,
        list(args.doc),
        expect_pdf=expect_pdf,
        recursive=recursive,
        findings=findings,
    )

    if args.jsonl is not None:
        json_path = args.jsonl.expanduser()
        if not json_path.exists():
            add_finding(findings, "error", f"json:{json_path}", f"manifest does not exist: {json_path}")
        else:
            if json_path.suffix.lower() not in {".json", ".jsonl"}:
                add_finding(findings, "error", f"json:{json_path}", "manifest must end with .json or .jsonl")
            else:
                try:
                    records = load_records(json_path)
                except Exception as exc:  # noqa: BLE001
                    add_finding(findings, "error", f"json:{json_path}", str(exc))
                else:
                    if not records:
                        add_finding(findings, "error", f"json:{json_path}", "manifest contains no records")
                    for location, record in records:
                        validate_record_profile(
                            args.profile,
                            record,
                            location=location,
                            base_dir=json_path.parent,
                            expect_pdf=expect_pdf,
                            recursive=recursive,
                            findings=findings,
                        )
                        for column in args.require_column:
                            if column not in record:
                                add_finding(findings, "error", location, f"missing required column '{column}'")
                            elif is_empty(record[column]):
                                add_finding(findings, "error", location, f"column '{column}' is empty")

    validate_env_vars(list(args.require_env), findings)

    print(f"Profile: {args.profile}")
    if args.doc:
        print(f"Documents checked: {len(args.doc)}")
    if args.jsonl is not None:
        print(f"Manifest: {args.jsonl}")
    if args.require_env:
        print(f"Env vars checked: {', '.join(args.require_env)}")

    print_findings(findings)

    errors = [item for item in findings if item.level == "error"]
    warnings = [item for item in findings if item.level == "warning"]

    print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
