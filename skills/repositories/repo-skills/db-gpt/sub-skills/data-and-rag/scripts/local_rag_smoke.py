#!/usr/bin/env python3
"""Offline DB-GPT-style document/chunk/schema smoke.

This helper deliberately uses only the Python standard library.  It is a
fixture validator, not a replacement for DB-GPT's optional parsers, embeddings,
or vector/graph stores.  It never contacts a network or executes SQL other
than read-only SQLite metadata queries.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

SUPPORTED_TEXT = {".md", ".txt", ".csv"}
KNOWN_UNSUPPORTED = {
    ".pdf": "PDF parser is intentionally not bundled",
    ".doc": "DOC parser is intentionally not bundled",
    ".docx": "DOCX parser is intentionally not bundled",
    ".xls": "Excel parser is intentionally not bundled",
    ".xlsx": "Excel parser is intentionally not bundled",
    ".pptx": "PPTX parser is intentionally not bundled",
}


@dataclass
class Record:
    source: str
    kind: str
    row: int | None
    content: str
    digest: str


@dataclass
class Chunk:
    source: str
    row: int | None
    index: int
    start: int
    end: int
    content: str
    digest: str


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _display(path: Path) -> str:
    return path.as_posix()


def _read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _parse_file(path: Path, warnings: list[str]) -> list[Record]:
    suffix = path.suffix.lower()
    source = _display(path)
    if suffix not in SUPPORTED_TEXT:
        reason = KNOWN_UNSUPPORTED.get(suffix, "unsupported extension")
        warnings.append(f"SKIP {source}: {reason}")
        return []
    if not path.is_file():
        warnings.append(f"SKIP {source}: not a regular file")
        return []
    try:
        raw = _read_utf8(path)
    except UnicodeDecodeError as exc:
        warnings.append(f"SKIP {source}: invalid UTF-8 ({exc.start})")
        return []
    except OSError as exc:
        warnings.append(f"SKIP {source}: read error ({exc})")
        return []

    if suffix == ".csv":
        if not raw.strip():
            warnings.append(f"SKIP {source}: empty CSV")
            return []
        try:
            rows = csv.DictReader(raw.splitlines())
            if not rows.fieldnames:
                warnings.append(f"SKIP {source}: CSV has no header")
                return []
            records: list[Record] = []
            for row_number, row in enumerate(rows):
                values = []
                for key, value in row.items():
                    if key is None or value is None:
                        continue
                    key_text, value_text = str(key).strip(), str(value).strip()
                    if key_text and value_text:
                        values.append(f"{key_text}: {value_text}")
                content = "\n".join(values).strip()
                if not content:
                    warnings.append(f"SKIP {source} row {row_number}: empty row")
                    continue
                records.append(
                    Record(source, "csv", row_number, content, _digest(content))
                )
            if not records:
                warnings.append(f"SKIP {source}: no non-empty CSV rows")
            return records
        except csv.Error as exc:
            warnings.append(f"SKIP {source}: invalid CSV ({exc})")
            return []

    content = raw.strip()
    if not content:
        warnings.append(f"SKIP {source}: empty document")
        return []
    return [Record(source, suffix[1:], None, content, _digest(content))]


def _iter_paths(inputs: Sequence[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for item in inputs:
        if item.is_dir():
            candidates = sorted(p for p in item.rglob("*") if p.is_file())
        else:
            candidates = [item]
        for candidate in candidates:
            resolved = candidate.absolute()
            if resolved not in seen:
                seen.add(resolved)
                yield candidate


def _chunk(record: Record, size: int, overlap: int) -> list[Chunk]:
    text = record.content
    step = size - overlap
    result: list[Chunk] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(len(text), start + size)
        content = text[start:end].strip()
        if content:
            result.append(
                Chunk(
                    source=record.source,
                    row=record.row,
                    index=index,
                    start=start,
                    end=end,
                    content=content,
                    digest=_digest(content),
                )
            )
            index += 1
        if end >= len(text):
            break
        start += step
    return result


def _make_fixture(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "notes.md").write_text(
        "# Local fixture\n\nDB-GPT chunks local documents before retrieval.\n"
        "The source metadata stays attached to each chunk.\n",
        encoding="utf-8",
    )
    (path / "rows.csv").write_text(
        "id,topic\n1,chunking\n2,SQLite schema\n", encoding="utf-8"
    )
    # This is intentional: the validator must report a deterministic encoding
    # warning rather than attempting to guess or repair arbitrary bytes.
    (path / "invalid.md").write_bytes(b"valid prefix\xff\xfe")


def _sqlite_schema(path: str) -> dict:
    """Return read-only SQLite table/column metadata."""
    database = ":memory:" if path == ":memory:" else path
    with sqlite3.connect(database) as connection:
        tables = []
        for (name,) in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ):
            quoted_name = str(name).replace('"', '""')
            columns = [
                {"name": row[1], "type": row[2], "notnull": bool(row[3]), "pk": row[5]}
                for row in connection.execute(f'PRAGMA table_info("{quoted_name}")')
            ]
            tables.append({"name": name, "columns": columns})
        return {"path": path, "tables": tables}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline local document/chunk/schema smoke; no DB-GPT imports, "
            "network calls, embeddings, or vector-store writes."
        )
    )
    parser.add_argument(
        "--input",
        nargs="*",
        type=Path,
        default=[],
        help="files or directories to inspect (default: in-memory fixture)",
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        help="create a tiny fixture here if absent, then inspect it",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=64,
        help="character window size (default: 64)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=8,
        help="character overlap; must be smaller than size (default: 8)",
    )
    parser.add_argument(
        "--sqlite",
        metavar="PATH",
        help="report tables and columns from a SQLite database, read-only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a JSON report instead of human-readable output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.chunk_overlap < 0 or args.chunk_overlap >= args.chunk_size:
        parser.error("--chunk-overlap must satisfy 0 <= overlap < chunk-size")

    warnings: list[str] = []
    inputs = list(args.input)
    if args.fixture_dir:
        if not args.fixture_dir.exists():
            _make_fixture(args.fixture_dir)
        inputs.append(args.fixture_dir)
    records: list[Record] = []
    if inputs:
        for path in _iter_paths(inputs):
            records.extend(_parse_file(path, warnings))
    else:
        fixture = Record(
            source="<memory>/fixture.md",
            kind="md",
            row=None,
            content="A local fixture tests deterministic chunk overlap and metadata.",
            digest=_digest("A local fixture tests deterministic chunk overlap and metadata."),
        )
        records = [fixture]

    chunks = [
        piece
        for record in records
        for piece in _chunk(record, args.chunk_size, args.chunk_overlap)
    ]
    report = {
        "ok": bool(records and chunks),
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "documents": [asdict(record) for record in records],
        "chunks": [asdict(piece) for piece in chunks],
        "warnings": warnings,
    }
    if args.sqlite:
        try:
            report["sqlite"] = _sqlite_schema(args.sqlite)
        except (OSError, sqlite3.Error) as exc:
            report["warnings"].append(f"SQLITE ERROR {args.sqlite}: {exc}")
            report["ok"] = False

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"documents={len(records)} chunks={len(chunks)} "
            f"chunk_size={args.chunk_size} overlap={args.chunk_overlap}"
        )
        for piece in chunks:
            row = "" if piece.row is None else f" row={piece.row}"
            print(
                f"CHUNK {piece.source}{row} [{piece.start}:{piece.end}] "
                f"{piece.content!r}"
            )
        for warning in warnings:
            print(warning, file=sys.stderr)
        if "sqlite" in report:
            print(json.dumps(report["sqlite"], ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
