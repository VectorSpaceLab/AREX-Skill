#!/usr/bin/env python3
"""Read-only checker for DeepDanbooru-style SQLite databases."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

TRAINING_COLUMNS = {
    "id",
    "md5",
    "file_ext",
    "tag_string",
    "tag_count_general",
}
SOURCE_COLUMNS = TRAINING_COLUMNS | {"rating", "score", "is_deleted"}
SUPPORTED_EXTENSIONS = {"png", "jpg", "jpeg"}


def read_only_connect(path: Path) -> sqlite3.Connection:
    encoded = quote(str(path.resolve()), safe="/")
    connection = sqlite3.connect(f"file:{encoded}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def schema_report(connection: sqlite3.Connection, mode: str) -> dict:
    table_rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'posts'"
    ).fetchall()
    required = SOURCE_COLUMNS if mode == "source" else TRAINING_COLUMNS
    report = {
        "mode": mode,
        "required_columns": sorted(required),
        "columns": [],
        "missing_columns": [],
        "problems": [],
        "warnings": [],
        "row_count": None,
    }
    if not table_rows:
        report["problems"].append("missing table: posts")
        return report

    info = connection.execute("PRAGMA table_info(posts)").fetchall()
    report["columns"] = [
        {
            "name": row["name"],
            "type": row["type"],
            "notnull": bool(row["notnull"]),
            "primary_key": bool(row["pk"]),
        }
        for row in info
    ]
    by_name = {row["name"]: row for row in info}
    missing = sorted(required - set(by_name))
    report["missing_columns"] = missing
    if missing:
        report["problems"].append("missing required columns: " + ", ".join(missing))

    id_info = by_name.get("id")
    if id_info is not None:
        # The loader needs an orderable id but does not require a primary-key
        # constraint. The converter's own output uses INTEGER NOT NULL PRIMARY
        # KEY, so report weaker declarations without rejecting usable inputs.
        if id_info["pk"] != 1:
            report["warnings"].append("posts.id is not declared as the primary key")
        if not id_info["notnull"]:
            report["warnings"].append("posts.id is not declared NOT NULL")
        if str(id_info["type"]).upper() != "INTEGER":
            report["problems"].append(
                f"posts.id has declared type {id_info['type']!r}, expected INTEGER"
            )

    if not missing:
        report["row_count"] = connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    return report


def image_report(
    connection: sqlite3.Connection, dataset_root: Path, minimum_tag_count: int
) -> dict:
    report = {
        "dataset_root": str(dataset_root),
        "minimum_tag_count": minimum_tag_count,
        "eligible_rows": 0,
        "missing_paths": [],
        "malformed_rows": [],
        "skipped_extension_rows": 0,
        "skipped_threshold_rows": 0,
    }
    rows = connection.execute(
        """SELECT id, md5, file_ext, tag_count_general
           FROM posts ORDER BY id"""
    )
    for row in rows:
        extension = row["file_ext"]
        count = row["tag_count_general"]
        if extension not in SUPPORTED_EXTENSIONS:
            report["skipped_extension_rows"] += 1
            continue
        if not isinstance(count, (int, float)):
            report["malformed_rows"].append(
                {
                    "id": row["id"],
                    "tag_count_general": count,
                    "reason": "tag_count_general is not numeric",
                }
            )
            continue
        if count < minimum_tag_count:
            report["skipped_threshold_rows"] += 1
            continue
        report["eligible_rows"] += 1
        md5 = row["md5"]
        if not isinstance(md5, str) or len(md5) < 2 or "/" in md5 or "\\" in md5:
            report["malformed_rows"].append(
                {"id": row["id"], "md5": md5, "reason": "unsafe or short md5 stem"}
            )
            continue
        path = dataset_root / "images" / md5[:2] / f"{md5}.{extension}"
        if not path.is_file():
            report["missing_paths"].append(str(path))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a DeepDanbooru posts schema without modifying the SQLite file."
    )
    parser.add_argument("sqlite_path", type=Path, help="SQLite database file to inspect.")
    parser.add_argument(
        "--mode",
        choices=("dataset", "training", "source"),
        default="dataset",
        help="Required schema: dataset/training use five columns; source adds rating, score, is_deleted.",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Read rows and report missing derived image files; still read-only.",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        help="Dataset directory for --check-images (default: SQLite file parent).",
    )
    parser.add_argument(
        "--minimum-tag-count",
        type=int,
        default=0,
        help="Threshold for --check-images (default: 0).",
    )
    parser.add_argument("--json", action="store_true", help="Emit one JSON report.")
    args = parser.parse_args(argv)

    database = args.sqlite_path.expanduser().resolve()
    report: dict = {"sqlite_path": str(database), "schema": None, "images": None}
    try:
        if not database.is_file():
            raise FileNotFoundError(f"SQLite file does not exist: {database}")
        if args.minimum_tag_count < 0:
            raise ValueError("--minimum-tag-count must be non-negative")
        connection = read_only_connect(database)
        try:
            report["schema"] = schema_report(connection, args.mode)
            if args.check_images and not report["schema"]["problems"]:
                root = (args.dataset_root or database.parent).expanduser().resolve()
                report["images"] = image_report(connection, root, args.minimum_tag_count)
        finally:
            connection.close()
    except (OSError, sqlite3.Error, ValueError) as exc:
        report["error"] = str(exc)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    failed = bool(report["schema"]["problems"])
    if report["images"] is not None:
        failed = failed or bool(report["images"]["missing_paths"] or report["images"]["malformed_rows"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        schema = report["schema"]
        status = "FAIL" if failed else "PASS"
        print(f"{status}: {database} ({args.mode}, rows={schema['row_count']})")
        for problem in schema["problems"]:
            print(f"  schema: {problem}")
        for warning in schema["warnings"]:
            print(f"  warning: {warning}")
        if report["images"] is not None:
            images = report["images"]
            print(
                "  images: eligible={eligible_rows}, missing={missing}, malformed={malformed}, skipped_extensions={skipped_ext}, skipped_threshold={skipped_threshold}".format(
                    eligible_rows=images["eligible_rows"],
                    missing=len(images["missing_paths"]),
                    malformed=len(images["malformed_rows"]),
                    skipped_ext=images["skipped_extension_rows"],
                    skipped_threshold=images["skipped_threshold_rows"],
                )
            )
            for path in images["missing_paths"][:20]:
                print(f"    missing: {path}")
            for row in images["malformed_rows"][:20]:
                print(f"    malformed: id={row['id']} ({row['reason']})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
