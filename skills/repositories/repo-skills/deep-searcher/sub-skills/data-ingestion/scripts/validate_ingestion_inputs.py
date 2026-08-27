#!/usr/bin/env python3
"""Validate DeepSearcher ingestion inputs without indexing or provider initialization.

This helper performs only local filesystem and syntax checks. It does not import
DeepSearcher, initialize providers, call embedding/LLM/vector DB services, perform
network requests, or read credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

LOCAL_DEFAULT_SUFFIXES = {".pdf", ".md", ".txt"}
TEXT_SUFFIXES = {".md", ".txt"}
JSON_SUFFIXES = {".json", ".jsonl"}
DOCLING_SUFFIXES = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".md",
    ".adoc",
    ".asciidoc",
    ".html",
    ".xhtml",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
}


def normalize_collection_name(name: str | None) -> str | None:
    """Match load_from_local_files collection normalization."""
    if name is None:
        return None
    return name.replace(" ", "_").replace("-", "_")


def add_issue(issues: list[dict[str, str]], severity: str, subject: str, message: str) -> None:
    issues.append({"severity": severity, "subject": subject, "message": message})


def validate_url(url: str, issues: list[dict[str, str]]) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        add_issue(issues, "error", url, "URL scheme must be http or https.")
    if not parsed.netloc:
        add_issue(issues, "error", url, "URL must include a host name.")
    if any(ch.isspace() for ch in url):
        add_issue(issues, "warning", url, "URL contains whitespace; encode or remove it.")


def iter_json_records(path: Path, issues: list[dict[str, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        if path.suffix.lower() == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                for lineno, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError as exc:
                        add_issue(
                            issues,
                            "error",
                            str(path),
                            f"Invalid JSONL at line {lineno}: {exc.msg}.",
                        )
                        continue
                    if not isinstance(item, dict):
                        add_issue(
                            issues,
                            "error",
                            str(path),
                            f"JSONL line {lineno} is {type(item).__name__}; expected object/dict.",
                        )
                        continue
                    records.append(item)
        else:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, list):
                add_issue(
                    issues,
                    "error",
                    str(path),
                    "JSON file must contain a top-level list of objects for JsonFileLoader.",
                )
                return records
            for index, item in enumerate(data):
                if not isinstance(item, dict):
                    add_issue(
                        issues,
                        "error",
                        str(path),
                        f"JSON item {index} is {type(item).__name__}; expected object/dict.",
                    )
                    continue
                records.append(item)
    except UnicodeDecodeError as exc:
        add_issue(issues, "error", str(path), f"File is not valid UTF-8 JSON text: {exc}.")
    except json.JSONDecodeError as exc:
        add_issue(issues, "error", str(path), f"Invalid JSON: {exc.msg} at line {exc.lineno}.")
    except OSError as exc:
        add_issue(issues, "error", str(path), f"Could not read file: {exc}.")
    return records


def validate_json_text_key(path: Path, text_key: str, issues: list[dict[str, str]]) -> None:
    records = iter_json_records(path, issues)
    if not records:
        add_issue(issues, "warning", str(path), "No JSON records found to validate.")
        return

    missing = []
    non_string = []
    empty = []
    for index, record in enumerate(records):
        if text_key not in record:
            missing.append(index)
            continue
        value = record[text_key]
        if not isinstance(value, str):
            non_string.append(index)
        elif not value.strip():
            empty.append(index)

    if missing:
        preview = ", ".join(map(str, missing[:10]))
        add_issue(
            issues,
            "error",
            str(path),
            f"text_key '{text_key}' missing in {len(missing)} record(s); first indices: {preview}.",
        )
    if non_string:
        preview = ", ".join(map(str, non_string[:10]))
        add_issue(
            issues,
            "warning",
            str(path),
            f"text_key '{text_key}' is non-string in {len(non_string)} record(s); first indices: {preview}.",
        )
    if empty:
        preview = ", ".join(map(str, empty[:10]))
        add_issue(
            issues,
            "warning",
            str(path),
            f"text_key '{text_key}' is empty in {len(empty)} record(s); first indices: {preview}.",
        )


def summarize_directory(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for child in path.rglob("*"):
        if child.is_file():
            suffix = child.suffix.lower() or "<no suffix>"
            counts[suffix] = counts.get(suffix, 0) + 1
    return dict(sorted(counts.items()))


def validate_path(path_text: str, json_text_key: str | None, issues: list[dict[str, str]]) -> None:
    path = Path(path_text).expanduser()
    if not path.exists():
        add_issue(issues, "error", path_text, "Local path does not exist.")
        return

    if path.is_dir():
        counts = summarize_directory(path)
        if not counts:
            add_issue(issues, "warning", path_text, "Directory is empty.")
            return
        default_hits = sum(count for suffix, count in counts.items() if suffix in LOCAL_DEFAULT_SUFFIXES)
        docling_hits = sum(count for suffix, count in counts.items() if suffix in DOCLING_SUFFIXES)
        json_hits = sum(count for suffix, count in counts.items() if suffix in JSON_SUFFIXES)
        if default_hits == 0:
            add_issue(
                issues,
                "warning",
                path_text,
                "Directory has no .pdf/.md/.txt files for the default PDFLoader.",
            )
        if docling_hits > default_hits:
            add_issue(
                issues,
                "info",
                path_text,
                "Directory includes formats that may require DoclingLoader or UnstructuredLoader.",
            )
        if json_text_key and json_hits:
            add_issue(
                issues,
                "warning",
                path_text,
                "JsonFileLoader directory traversal is unreliable in this checkout; pass JSON/JSONL files directly.",
            )
            for json_file in sorted(path.rglob("*")):
                if json_file.is_file() and json_file.suffix.lower() in JSON_SUFFIXES:
                    validate_json_text_key(json_file, json_text_key, issues)
        return

    if not path.is_file():
        add_issue(issues, "error", path_text, "Local path is neither a regular file nor a directory.")
        return

    suffix = path.suffix.lower()
    if suffix not in LOCAL_DEFAULT_SUFFIXES:
        if suffix in JSON_SUFFIXES:
            add_issue(
                issues,
                "info",
                path_text,
                "JSON/JSONL requires JsonFileLoader(text_key=...) and should be passed as a direct file.",
            )
        elif suffix in DOCLING_SUFFIXES:
            add_issue(
                issues,
                "info",
                path_text,
                "This suffix is not handled by the default PDFLoader but is supported by DoclingLoader.",
            )
        else:
            add_issue(
                issues,
                "warning",
                path_text,
                "Suffix is not supported by the default PDFLoader; choose an appropriate loader.",
            )

    if suffix in TEXT_SUFFIXES:
        try:
            with path.open("r", encoding="utf-8") as handle:
                handle.read(4096)
        except UnicodeDecodeError as exc:
            add_issue(issues, "error", path_text, f"Text file is not valid UTF-8: {exc}.")
        except OSError as exc:
            add_issue(issues, "error", path_text, f"Could not read text file: {exc}.")

    if json_text_key and suffix in JSON_SUFFIXES:
        validate_json_text_key(path, json_text_key, issues)


def validate_chunking(args: argparse.Namespace, issues: list[dict[str, str]]) -> None:
    if args.chunk_size <= 0:
        add_issue(issues, "error", "chunk_size", "chunk_size must be positive.")
    elif args.chunk_size < 100:
        add_issue(issues, "warning", "chunk_size", "Very small chunks may fragment context.")
    elif args.chunk_size > 10000:
        add_issue(issues, "warning", "chunk_size", "Very large chunks may be expensive and imprecise.")

    if args.chunk_overlap < 0:
        add_issue(issues, "error", "chunk_overlap", "chunk_overlap must be non-negative.")
    elif args.chunk_size > 0 and args.chunk_overlap >= args.chunk_size:
        add_issue(issues, "error", "chunk_overlap", "chunk_overlap must be smaller than chunk_size.")
    elif args.chunk_size > 0 and args.chunk_overlap > args.chunk_size // 2:
        add_issue(issues, "warning", "chunk_overlap", "Overlap exceeds 50% of chunk_size.")

    if args.batch_size <= 0:
        add_issue(issues, "error", "batch_size", "batch_size must be positive.")
    elif args.batch_size > 1024:
        add_issue(issues, "warning", "batch_size", "Large batch_size may hit memory or provider rate limits.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate DeepSearcher ingestion paths, URLs, collection-name normalization, "
            "chunk settings, and optional JSON text keys without indexing or network calls."
        )
    )
    parser.add_argument("--path", action="append", default=[], help="Local file or directory to validate. May be repeated.")
    parser.add_argument("--url", action="append", default=[], help="HTTP/HTTPS URL shape to validate. May be repeated.")
    parser.add_argument("--collection-name", help="Collection name to preview using local-loading normalization.")
    parser.add_argument("--json-text-key", help="Validate this JsonFileLoader text_key in JSON/JSONL files.")
    parser.add_argument("--chunk-size", type=int, default=1500, help="Chunk size to validate. Default: 1500.")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Chunk overlap to validate. Default: 100.")
    parser.add_argument("--batch-size", type=int, default=256, help="Embedding batch size to validate. Default: 256.")
    parser.add_argument("--as-json", action="store_true", help="Emit a JSON report instead of human-readable text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    issues: list[dict[str, str]] = []

    if not args.path and not args.url:
        add_issue(issues, "warning", "inputs", "No --path or --url values were provided.")

    for path_text in args.path:
        validate_path(path_text, args.json_text_key, issues)

    for url in args.url:
        validate_url(url, issues)

    validate_chunking(args, issues)

    normalized = normalize_collection_name(args.collection_name)
    report = {
        "ok": not any(issue["severity"] == "error" for issue in issues),
        "paths_checked": args.path,
        "urls_checked": args.url,
        "collection_name": args.collection_name,
        "local_loading_collection_name": normalized,
        "web_loading_collection_name": args.collection_name,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "batch_size": args.batch_size,
        "issues": issues,
    }

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DeepSearcher ingestion input validation")
        print("=======================================")
        print(f"Status: {'OK' if report['ok'] else 'ERROR'}")
        if args.collection_name is not None:
            print(f"Collection name: {args.collection_name}")
            print(f"  local load_from_local_files name: {normalized}")
            print(f"  web load_from_website name:      {args.collection_name}")
        print(f"Chunking: chunk_size={args.chunk_size}, chunk_overlap={args.chunk_overlap}, batch_size={args.batch_size}")
        print(f"Paths checked: {len(args.path)}")
        print(f"URLs checked:  {len(args.url)}")
        if issues:
            print("\nIssues:")
            for issue in issues:
                print(f"- [{issue['severity']}] {issue['subject']}: {issue['message']}")
        else:
            print("\nNo issues found.")
        print("\nNo indexing, network access, or provider initialization was performed.")

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
