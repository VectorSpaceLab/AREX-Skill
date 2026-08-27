#!/usr/bin/env python3
"""Validate a paperai corpus and optional configuration without loading models."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


REQUIRED = {
    "articles": {"id", "tags", "entry"},
    "sections": {"id", "article", "name", "text"},
}


def nonnegative(value: str) -> int:
    """Parse a non-negative bound for the safe checker."""

    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0; use 0 for unbounded")
    return parsed


def table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    """Return lower-case columns for a known table name."""

    return {
        row[1].lower()
        for row in connection.execute(f"PRAGMA table_info({table})")
    }


def config_report(config_path: Path | None, vectors: str | None) -> tuple[dict[str, Any], list[str]]:
    """Parse a YAML mapping or record an untouched vector reference."""

    report: dict[str, Any] = {}
    errors: list[str] = []
    if config_path and vectors:
        errors.append("--config and --vectors are mutually exclusive")
        return report, errors

    if config_path:
        report["config"] = str(config_path)
        if config_path.suffix != ".yml":
            errors.append(
                "paperai.index recognizes YAML configuration files only when "
                "the path ends in lowercase .yml"
            )
        try:
            import yaml

            with config_path.open("r", encoding="utf-8") as stream:
                value = yaml.safe_load(stream)
        except FileNotFoundError:
            errors.append(f"configuration file not found: {config_path}")
            return report, errors
        except OSError as error:
            errors.append(f"configuration file cannot be read: {error}")
            return report, errors
        except Exception as error:  # YAML parser types vary by PyYAML version.
            errors.append(f"configuration parse failed: {error}")
            return report, errors

        if not isinstance(value, dict):
            errors.append("configuration root must be a YAML mapping")
        else:
            report["config_keys"] = sorted(str(key) for key in value)
            report["config_path"] = value.get("path")
            report["config_scoring"] = value.get("scoring")
            report["config_gpu"] = value.get("gpu")
    elif vectors:
        vector_path = Path(vectors).expanduser()
        report["vectors"] = vectors
        report["vectors_exists"] = vector_path.exists()
        report["vectors_is_file"] = vector_path.is_file()
        report["vectors_is_directory"] = vector_path.is_dir()
        # Do not inspect or instantiate the vector backend. A model identifier
        # can be remote and a vector database's format is backend-specific.

    return report, errors


def validate(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    """Validate the SQLite layout and bounded source queries."""

    root = args.path.expanduser()
    dbfile = root / "articles.sqlite"
    report: dict[str, Any] = {
        "path": str(root),
        "database": str(dbfile),
        "maxsize": args.maxsize,
        "toprank": args.toprank,
    }
    errors: list[str] = []

    config, config_errors = config_report(args.config, args.vectors)
    report.update(config)
    errors.extend(config_errors)

    if not dbfile.is_file():
        errors.append(f"missing source artifact: {dbfile}")
        return report, errors

    try:
        connection = sqlite3.connect(f"file:{dbfile}?mode=ro", uri=True)
    except sqlite3.Error as error:
        errors.append(f"cannot open SQLite database read-only: {error}")
        return report, errors

    try:
        tables = {
            row[0].lower()
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        report["tables"] = sorted(tables)
        for table, required in REQUIRED.items():
            if table not in tables:
                errors.append(f"missing table: {table}")
                continue
            columns = table_columns(connection, table)
            report[f"{table}_columns"] = sorted(columns)
            missing = sorted(required - columns)
            if missing:
                errors.append(f"{table} missing columns: {', '.join(missing)}")

        if args.toprank > 0:
            if "citations" not in tables:
                errors.append("toprank > 0 requires table: citations")
            else:
                citations = table_columns(connection, "citations")
                report["citations_columns"] = sorted(citations)
                if "reference" not in citations:
                    errors.append("citations missing column: reference")

        usable = True
        for table, required in REQUIRED.items():
            if table not in tables or not required.issubset(table_columns(connection, table)):
                usable = False
        if args.toprank > 0 and (
            "citations" not in tables
            or not {"reference"}.issubset(table_columns(connection, "citations"))
        ):
            usable = False

        if usable:
            report["article_count"] = connection.execute(
                "SELECT COUNT(*) FROM articles"
            ).fetchone()[0]
            report["tagged_article_count"] = connection.execute(
                "SELECT COUNT(*) FROM articles WHERE tags IS NOT NULL"
            ).fetchone()[0]
            report["section_count"] = connection.execute(
                "SELECT COUNT(*) FROM sections"
            ).fetchone()[0]

            query = (
                "SELECT COUNT(*) FROM sections "
                "WHERE article IN (SELECT a.id FROM articles a WHERE a.tags IS NOT NULL)"
            )
            parameters: list[Any] = []
            if args.maxsize > 0:
                query += " AND article IN (SELECT id FROM articles ORDER BY entry DESC LIMIT ?)"
                parameters.append(args.maxsize)
            if args.toprank > 0:
                query += (
                    " AND article IN (SELECT reference FROM citations "
                    "GROUP BY reference ORDER BY count(*) DESC LIMIT ?)"
                )
                parameters.append(args.toprank)
            report["candidate_section_count"] = connection.execute(
                query, parameters
            ).fetchone()[0]
    except sqlite3.DatabaseError as error:
        errors.append(f"SQLite validation query failed: {error}")
    finally:
        connection.close()

    return report, errors


def parser() -> argparse.ArgumentParser:
    """Build the command-line parser without importing optional packages."""

    command = argparse.ArgumentParser(
        description=(
            "Validate CORPUS_DIR/articles.sqlite and optional YAML/vector "
            "references without importing txtai or downloading models."
        )
    )
    command.add_argument(
        "path",
        type=Path,
        help="directory containing the source artifact articles.sqlite",
    )
    group = command.add_mutually_exclusive_group()
    group.add_argument("--config", type=Path, help="YAML mapping to shape-check")
    group.add_argument("--vectors", help="vector/model reference; never loaded")
    command.add_argument(
        "--maxsize",
        type=nonnegative,
        default=0,
        help="positive newest-article bound; 0 means unbounded (default: 0)",
    )
    command.add_argument(
        "--toprank",
        type=nonnegative,
        default=0,
        help="positive citation-reference bound; 0 means unbounded (default: 0)",
    )
    command.add_argument(
        "--json",
        action="store_true",
        help="emit one JSON object instead of human-readable lines",
    )
    return command


def main(argv: list[str] | None = None) -> int:
    """Run validation and return a process status."""

    args = parser().parse_args(argv)
    report, errors = validate(args)
    report["ok"] = not errors
    if args.json:
        print(json.dumps({"report": report, "errors": errors}, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
        if errors:
            print("errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("status: ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
