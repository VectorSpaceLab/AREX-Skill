#!/usr/bin/env python3
"""Summarize an OASIS SQLite database without importing OASIS.

The script is intentionally stdlib-only. It opens the target database in
read-only mode, lists known OASIS tables found, counts rows, summarizes trace
action counts, and prints recent trace rows with compact/truncated info.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

OASIS_TABLES = [
    "user",
    "post",
    "follow",
    "mute",
    "like",
    "dislike",
    "report",
    "trace",
    "rec",
    "comment",
    "comment_like",
    "comment_dislike",
    "product",
    "chat_group",
    "group_members",
    "group_messages",
]


def quote_identifier(name: str) -> str:
    """Return a safely quoted SQLite identifier."""
    return '"' + name.replace('"', '""') + '"'


def compact(value: object, max_len: int = 240) -> str:
    """Return a single-line, truncated, human-safe representation."""
    if value is None:
        text = ""
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = " ".join(text.split())
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def compact_trace_info(raw: object) -> str:
    if raw is None:
        return ""
    try:
        parsed = json.loads(str(raw))
    except Exception:
        parsed = raw
    return compact(parsed)


def connect_read_only(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"database path does not exist: {db_path}")
    if not db_path.is_file():
        raise FileNotFoundError(f"database path is not a file: {db_path}")
    uri = f"{db_path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(row["name"]) for row in rows]


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(
        f"SELECT COUNT(*) AS count FROM {quote_identifier(table)}"
    ).fetchone()
    return int(row["count"])


def print_table_counts(conn: sqlite3.Connection, tables: list[str]) -> None:
    if not tables:
        print("No known OASIS tables found.")
        return
    print(f"OASIS tables found ({len(tables)}):")
    for table in tables:
        try:
            count = count_rows(conn, table)
        except sqlite3.Error as exc:
            print(f"  - {table}: ERROR counting rows: {exc}")
        else:
            print(f"  - {table}: {count} rows")


def print_trace_counts(conn: sqlite3.Connection, tables: list[str]) -> None:
    if "trace" not in tables:
        print("\nTrace action counts: trace table not found.")
        return
    rows = conn.execute(
        """
        SELECT action, COUNT(*) AS count
        FROM trace
        GROUP BY action
        ORDER BY count DESC, action ASC
        """
    ).fetchall()
    print("\nTrace action counts:")
    if not rows:
        print("  (no trace rows)")
        return
    for row in rows:
        print(f"  - {row['action']}: {row['count']}")


def print_recent_trace(conn: sqlite3.Connection, tables: list[str], limit: int) -> None:
    if "trace" not in tables:
        return
    rows = conn.execute(
        """
        SELECT rowid, user_id, created_at, action, info
        FROM trace
        ORDER BY rowid DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    print(f"\nRecent trace rows (limit {limit}, newest rowid first):")
    if not rows:
        print("  (no trace rows)")
        return
    for row in rows:
        info = compact_trace_info(row["info"])
        print(
            "  - "
            f"rowid={row['rowid']} "
            f"user_id={row['user_id']} "
            f"created_at={compact(row['created_at'], 80)} "
            f"action={row['action']} "
            f"info={info}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize an OASIS SQLite database read-only."
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Path to an OASIS SQLite .db file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent trace rows to print (default: 10).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.limit < 0:
        print("--limit must be non-negative", file=sys.stderr)
        return 2

    db_path = Path(args.db_path).expanduser()
    try:
        conn = connect_read_only(db_path)
    except Exception as exc:
        print(f"ERROR: could not open database read-only: {exc}", file=sys.stderr)
        return 1

    with conn:
        print(f"Database: {db_path.resolve()}")
        print("Open mode: read-only")
        all_tables = list_tables(conn)
        oasis_tables = [table for table in OASIS_TABLES if table in all_tables]
        other_tables = [table for table in all_tables if table not in OASIS_TABLES]
        print_table_counts(conn, oasis_tables)
        if other_tables:
            print("\nOther SQLite tables:")
            for table in other_tables:
                print(f"  - {table}")
        print_trace_counts(conn, oasis_tables)
        print_recent_trace(conn, oasis_tables, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
