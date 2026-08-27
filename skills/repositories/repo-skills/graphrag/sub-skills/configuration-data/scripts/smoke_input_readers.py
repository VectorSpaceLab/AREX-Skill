#!/usr/bin/env python3
"""Smoke-test GraphRAG input readers with tiny temporary local files."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def write_text_fixture(base_dir: Path) -> None:
    (base_dir / "input.txt").write_text("A tiny GraphRAG text document.\n", encoding="utf-8")


def write_csv_fixture(base_dir: Path) -> None:
    with (base_dir / "input.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "title", "text"])
        writer.writeheader()
        writer.writerow({"id": "csv-1", "title": "CSV One", "text": "CSV body"})


def write_json_fixture(base_dir: Path) -> None:
    (base_dir / "input.json").write_text(
        json.dumps([{"id": "json-1", "title": "JSON One", "text": "JSON body"}]),
        encoding="utf-8",
    )


def write_jsonl_fixture(base_dir: Path) -> None:
    (base_dir / "input.jsonl").write_text(
        json.dumps({"id": "jsonl-1", "title": "JSONL One", "text": "JSONL body"}) + "\n",
        encoding="utf-8",
    )


def write_parquet_fixture(base_dir: Path) -> tuple[bool, str | None]:
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover - depends on caller environment
        return False, f"pandas unavailable: {exc}"

    try:
        pd.DataFrame(
            [{"id": "parquet-1", "title": "Parquet One", "text": "Parquet body"}]
        ).to_parquet(base_dir / "input.parquet")
    except Exception as exc:  # pragma: no cover - depends on optional parquet engine
        return False, f"parquet writer unavailable: {exc}"
    return True, None


def document_count(result: Any) -> int:
    if result is None:
        return 0
    if isinstance(result, list):
        return len(result)
    if hasattr(result, "documents"):
        return len(result.documents)
    try:
        return len(result)
    except TypeError:
        return 1


async def read_documents(reader: Any) -> Any:
    for method_name in ("read_files", "read", "load"):
        method = getattr(reader, method_name, None)
        if method is None:
            continue
        result = method()
        if hasattr(result, "__await__"):
            return await result
        return result
    raise AttributeError("reader has no read_files(), read(), or load() method")


async def smoke_reader(
    input_type: str,
    file_pattern: str,
    base_dir: Path,
    text_column: str = "text",
) -> dict[str, Any]:
    from graphrag_input import InputConfig, create_input_reader
    from graphrag_storage.file_storage import FileStorage

    config = InputConfig(
        type=input_type,
        file_pattern=file_pattern,
        id_column="id" if input_type != "text" else None,
        title_column="title" if input_type != "text" else None,
        text_column=text_column if input_type != "text" else None,
    )
    storage = FileStorage(str(base_dir))
    reader = create_input_reader(config, storage)
    result = await read_documents(reader)
    return {
        "ok": True,
        "reader_class": reader.__class__.__name__,
        "documents": document_count(result),
    }


async def run_smokes(include_markitdown: bool) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="graphrag-input-smoke-") as tmp:
        base_dir = Path(tmp)
        write_text_fixture(base_dir)
        write_csv_fixture(base_dir)
        write_json_fixture(base_dir)
        write_jsonl_fixture(base_dir)
        parquet_ready, parquet_skip = write_parquet_fixture(base_dir)

        cases: list[tuple[str, str, str]] = [
            ("text", r".*\.txt$", "text"),
            ("csv", r".*\.csv$", "text"),
            ("json", r".*\.json$", "text"),
            ("jsonl", r".*\.jsonl$", "text"),
        ]
        if parquet_ready:
            cases.append(("parquet", r".*\.parquet$", "text"))
        if include_markitdown:
            cases.append(("markitdown", r".*\.txt$", "text"))

        results: dict[str, Any] = {}
        for input_type, file_pattern, text_column in cases:
            try:
                results[input_type] = await smoke_reader(
                    input_type, file_pattern, base_dir, text_column
                )
            except Exception as exc:
                results[input_type] = {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }

        if not parquet_ready:
            results["parquet"] = {"ok": False, "skipped": True, "reason": parquet_skip}
        if not include_markitdown:
            results["markitdown"] = {
                "ok": False,
                "skipped": True,
                "reason": "disabled by default; pass --include-markitdown to exercise optional converter",
            }
        return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create tiny temporary local files and smoke-test built-in GraphRAG input readers without network or credentials."
    )
    parser.add_argument(
        "--include-markitdown",
        action="store_true",
        help="Also instantiate the MarkItDown reader against a text fixture.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level. Use 0 for compact output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results = asyncio.run(run_smokes(args.include_markitdown))
    except Exception as exc:
        print(f"Failed to run input reader smokes: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    indent = None if args.indent == 0 else args.indent
    print(json.dumps(results, indent=indent, sort_keys=True))

    failures = [name for name, result in results.items() if not result.get("ok") and not result.get("skipped")]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
