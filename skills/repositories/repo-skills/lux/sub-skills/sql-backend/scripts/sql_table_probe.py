#!/usr/bin/env python3
"""Non-destructive PostgreSQL table probe for Lux SQL workflows.

The probe checks connector availability, service connectivity, table existence,
row count, and a small preview. It does not create/drop/update/insert and it
intentionally does not invoke Lux metadata generation.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Sequence, Tuple


MAX_PREVIEW_ROWS = 20


def fail(message: str, exit_code: int = 2) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return exit_code


def quote_identifier_part(part: str) -> str:
    part = part.strip()
    if not part:
        raise ValueError("empty identifier component")
    return '"' + part.replace('"', '""') + '"'


def quote_qualified_identifier(name: str) -> str:
    """Quote a PostgreSQL identifier or dotted schema.table name safely."""
    parts = [part.strip() for part in name.split(".")]
    if not parts or any(part == "" for part in parts):
        raise ValueError("--table must be a non-empty table or schema.table identifier")
    return ".".join(quote_identifier_part(part) for part in parts)


def classify_db_error(exc: BaseException) -> str:
    details = str(exc).strip()
    class_name = exc.__class__.__name__
    haystack = f"{class_name} {details}".lower()

    if "undefinedtable" in haystack or "does not exist" in haystack or "relation" in haystack:
        prefix = "table lookup failed; verify --table, schema/search_path, and read privileges"
    elif "authentication" in haystack or "password" in haystack or "role" in haystack:
        prefix = "authentication failed; verify database user, password, and permissions"
    elif (
        "connection refused" in haystack
        or "could not connect" in haystack
        or "timeout" in haystack
        or "could not translate host" in haystack
        or "name or service not known" in haystack
        or "server closed the connection" in haystack
    ):
        prefix = "PostgreSQL service connection failed; verify host, port, network, and service status"
    else:
        prefix = "database probe failed"

    if details:
        return f"{prefix}: {class_name}: {details}"
    return f"{prefix}: {class_name}"


def normalize_preview_rows(value: int) -> int:
    if value < 0:
        raise argparse.ArgumentTypeError("--preview-rows must be >= 0")
    if value > MAX_PREVIEW_ROWS:
        raise argparse.ArgumentTypeError(f"--preview-rows must be <= {MAX_PREVIEW_ROWS}")
    return value


def print_rows(columns: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    columns = list(columns)
    if columns:
        print("columns: " + ", ".join(columns))
    else:
        print("columns: (none returned)")
    for idx, row in enumerate(rows, start=1):
        print(f"preview[{idx}]: {tuple(row)!r}")


def run_psycopg2_probe(dsn: str, table_name: str, preview_rows: int) -> Tuple[int, Sequence[str], Sequence[Sequence[object]]]:
    try:
        import psycopg2  # type: ignore
    except ModuleNotFoundError:
        raise RuntimeError(
            "missing psycopg2; install psycopg2-binary or psycopg2 before using --dsn"
        )

    identifier = quote_qualified_identifier(table_name)
    connection = None
    try:
        connection = psycopg2.connect(dsn)
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(1) AS length FROM {identifier}")
            row_count = int(cursor.fetchone()[0])

            columns = []
            rows = []
            if preview_rows:
                cursor.execute(f"SELECT * FROM {identifier} LIMIT %s", (preview_rows,))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
            return row_count, columns, rows
    finally:
        if connection is not None:
            connection.close()


def run_sqlalchemy_probe(url: str, table_name: str, preview_rows: int) -> Tuple[int, Sequence[str], Sequence[Sequence[object]]]:
    try:
        from sqlalchemy import create_engine, text  # type: ignore
    except ModuleNotFoundError:
        raise RuntimeError(
            "missing SQLAlchemy; install sqlalchemy and a PostgreSQL DBAPI such as psycopg2-binary before using --sqlalchemy-url"
        )

    identifier = quote_qualified_identifier(table_name)
    engine = None
    try:
        engine = create_engine(url)
        with engine.connect() as connection:
            row_count = int(connection.execute(text(f"SELECT COUNT(1) AS length FROM {identifier}")).scalar_one())

            columns = []
            rows = []
            if preview_rows:
                result = connection.execute(
                    text(f"SELECT * FROM {identifier} LIMIT :preview_rows"),
                    {"preview_rows": preview_rows},
                )
                columns = list(result.keys())
                rows = [tuple(row) for row in result.fetchall()]
            return row_count, columns, rows
    finally:
        if engine is not None:
            engine.dispose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Non-destructively probe a PostgreSQL table before using LuxSQLTable. "
            "Runs SELECT COUNT(1) and an optional SELECT preview only."
        )
    )
    connector = parser.add_mutually_exclusive_group(required=True)
    connector.add_argument(
        "--dsn",
        help="psycopg2 DSN string, for example from an environment variable",
    )
    connector.add_argument(
        "--sqlalchemy-url",
        help="SQLAlchemy PostgreSQL URL, for example from an environment variable",
    )
    parser.add_argument(
        "--table",
        required=True,
        help="existing table or schema.table identifier to probe",
    )
    parser.add_argument(
        "--preview-rows",
        type=normalize_preview_rows,
        default=5,
        help=f"number of preview rows to fetch, 0-{MAX_PREVIEW_ROWS} (default: 5)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.dsn:
            row_count, columns, rows = run_psycopg2_probe(args.dsn, args.table, args.preview_rows)
            connector = "psycopg2"
        else:
            row_count, columns, rows = run_sqlalchemy_probe(
                args.sqlalchemy_url, args.table, args.preview_rows
            )
            connector = "SQLAlchemy"
    except RuntimeError as exc:
        return fail(str(exc))
    except ValueError as exc:
        return fail(str(exc))
    except Exception as exc:  # connector-specific DB errors are intentionally classified here
        return fail(classify_db_error(exc))

    print(f"OK: {connector} connected and queried table {args.table!r}")
    print(f"row_count: {row_count}")
    if args.preview_rows:
        print_rows(columns, rows)
    else:
        print("preview: skipped (--preview-rows 0)")
    print("next_step: configure lux.config.set_SQL_connection(...) and create lux.LuxSQLTable(table_name=...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
