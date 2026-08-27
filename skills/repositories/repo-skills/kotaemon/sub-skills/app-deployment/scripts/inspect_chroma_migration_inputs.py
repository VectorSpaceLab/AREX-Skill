#!/usr/bin/env python3
"""Read-only preflight for Kotaemon Chroma metadata migration inputs.

The source migration updates Chroma collection metadata using file IDs from the
Kotaemon SQLite database. This helper validates paths and table/collection clues
without importing chromadb/sqlalchemy or mutating any data.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse


CHROMA_MARKERS = ["chroma.sqlite3", "index", "index_metadata.pickle"]


def sqlite_path_from_uri(value: str) -> Path:
    if value.startswith("sqlite:///"):
        parsed = urlparse(value)
        path = unquote(parsed.path)
        return Path(path)
    if value.startswith("sqlite://"):
        raise ValueError("Only local sqlite:/// URIs are supported for read-only preflight")
    return Path(value)


def list_tables(sqlite_path: Path) -> list[str]:
    uri = f"file:{sqlite_path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        rows = connection.execute(
            "select name from sqlite_master where type = 'table' order by name"
        ).fetchall()
    finally:
        connection.close()
    return [row[0] for row in rows]


def count_rows(sqlite_path: Path, table: str) -> int | None:
    if not table.replace("_", "").isalnum():
        return None
    uri = f"file:{sqlite_path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        row = connection.execute(f'select count(*) from "{table}"').fetchone()
    except sqlite3.Error:
        return None
    finally:
        connection.close()
    if row is None:
        return None
    return int(row[0])


def infer_index_ids(tables: list[str]) -> list[int]:
    ids: set[int] = set()
    prefix = "index__"
    for table in tables:
        if not table.startswith(prefix):
            continue
        parts = table.split("__")
        if len(parts) >= 3 and parts[1].isdigit():
            ids.add(int(parts[1]))
    return sorted(ids)


def inspect_chroma_dir(path: Path) -> int:
    issues = 0
    print("== Chroma directory ==")
    if not path.exists():
        print(f"WARN directory does not exist: {path}")
        return 1
    if not path.is_dir():
        print(f"WARN path is not a directory: {path}")
        return 1
    print(f"OK directory exists: {path}")

    entries = sorted(child.name for child in path.iterdir())
    if not entries:
        print("WARN directory is empty")
        issues += 1
    else:
        preview = ", ".join(entries[:8])
        suffix = " ..." if len(entries) > 8 else ""
        print(f"INFO entries: {preview}{suffix}")

    markers_found = [marker for marker in CHROMA_MARKERS if (path / marker).exists()]
    uuid_dirs = [child for child in path.iterdir() if child.is_dir() and len(child.name) >= 16]
    if markers_found or uuid_dirs:
        print("OK Chroma-like markers found")
        if markers_found:
            print(f"INFO markers: {', '.join(markers_found)}")
        if uuid_dirs:
            print(f"INFO possible collection directories: {len(uuid_dirs)}")
    else:
        print("WARN no obvious Chroma markers found; verify this is the persistent vectorstore root")
        issues += 1
    return issues


def inspect_sqlite(sqlite_path: Path, requested_index_ids: list[int]) -> tuple[int, list[int]]:
    issues = 0
    print("\n== SQLite database ==")
    if not sqlite_path.exists():
        print(f"WARN SQLite file does not exist: {sqlite_path}")
        return 1, []
    if not sqlite_path.is_file():
        print(f"WARN SQLite path is not a file: {sqlite_path}")
        return 1, []
    print(f"OK SQLite file exists: {sqlite_path}")

    try:
        tables = list_tables(sqlite_path)
    except sqlite3.Error as exc:
        print(f"WARN cannot open SQLite read-only: {exc}")
        return 1, []

    print(f"INFO table count: {len(tables)}")
    inferred_ids = infer_index_ids(tables)
    if inferred_ids:
        print(f"OK inferred index ids from resource tables: {', '.join(map(str, inferred_ids))}")
    else:
        print("WARN no index__<id>__source/index tables inferred")
        issues += 1

    index_ids = requested_index_ids or inferred_ids or [1]
    for index_id in index_ids:
        source_table = f"index__{index_id}__source"
        relation_table = f"index__{index_id}__index"
        for table in [source_table, relation_table]:
            if table in tables:
                count = count_rows(sqlite_path, table)
                count_text = "unknown" if count is None else str(count)
                print(f"OK {table}: present, rows={count_text}")
            else:
                print(f"WARN {table}: missing")
                issues += 1

    if "index" in tables:
        count = count_rows(sqlite_path, "index")
        count_text = "unknown" if count is None else str(count)
        print(f"INFO app index table present, rows={count_text}")
    else:
        print("INFO app index table not found under literal name 'index'; this may be normal for some schemas")

    return issues, index_ids


def inspect_collection_names(chroma_dir: Path, index_ids: list[int]) -> int:
    print("\n== Migration plan ==")
    if not index_ids:
        print("WARN no index ids available for collection-name planning")
        return 1
    for index_id in index_ids:
        print(f"INFO would inspect Chroma collection name: index_{index_id}")
        print(f"INFO would join SQLite tables: index__{index_id}__source and index__{index_id}__index")
        print("INFO would update metadata.file_id only in a separate approved mutating migration")
    print(f"INFO source Chroma root: {chroma_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only preflight for Kotaemon Chroma migration inputs."
    )
    parser.add_argument(
        "--chroma-dir",
        type=Path,
        required=True,
        help="Path to the existing Chroma persistent directory/vectorstore root.",
    )
    parser.add_argument(
        "--sqlite-uri",
        required=True,
        help="SQLite URI or path, for example sqlite:///ktem_app_data/user_data/sql.db.",
    )
    parser.add_argument(
        "--index-id",
        type=int,
        action="append",
        default=[],
        help="Specific Kotaemon file index id to preflight. May be repeated. Defaults to inferred ids.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    chroma_dir = args.chroma_dir.expanduser().resolve()
    try:
        sqlite_path = sqlite_path_from_uri(args.sqlite_uri).expanduser().resolve()
    except ValueError as exc:
        print(f"WARN {exc}")
        return 1

    issues = 0
    issues += inspect_chroma_dir(chroma_dir)
    sqlite_issues, index_ids = inspect_sqlite(sqlite_path, args.index_id)
    issues += sqlite_issues
    issues += inspect_collection_names(chroma_dir, index_ids)

    print("\n== Summary ==")
    print("OK no migration was run; no Chroma collections or SQLite rows were modified.")
    if issues:
        print(f"WARN completed with {issues} warning(s). Resolve them and create a backup before any mutating migration.")
        return 1
    print("OK inputs look plausible for a later approved mutating migration. Create a backup before proceeding.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
