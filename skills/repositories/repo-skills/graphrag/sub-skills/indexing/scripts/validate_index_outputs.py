#!/usr/bin/env python3
"""Validate GraphRAG output/BYOG table presence and basic table contracts."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "documents": {"id", "title", "text"},
    "text_units": {"id", "text", "document_id"},
    "entities": {"id", "title"},
    "relationships": {"id", "source", "target"},
    "communities": {"id", "community", "level"},
    "community_reports": {"id", "community", "title", "summary"},
    "covariates": {"covariate_type", "subject_id", "text_unit_id"},
}

USE_TABLES: dict[str, set[str]] = {
    "global": {"entities", "relationships", "communities", "community_reports"},
    "local": {"entities", "relationships", "communities", "community_reports", "text_units"},
    "drift": {"entities", "relationships", "communities", "community_reports", "text_units"},
    "basic": {"text_units"},
    "byog": {"entities", "relationships"},
}

WORKFLOW_INPUTS: dict[str, set[str]] = {
    "create_communities": {"entities", "relationships"},
    "create_community_reports": {"entities", "relationships", "communities"},
    "create_community_reports_text": {"entities", "relationships", "communities", "text_units"},
    "generate_text_embeddings": set(),
}

EMBEDDING_TABLES: dict[str, str] = {
    "text_unit_text": "text_units",
    "entity_description": "entities",
    "community_full_content": "community_reports",
}

EXTENSIONS = [".parquet", ".csv", ".json"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that a GraphRAG output directory has tables needed for a use case."
    )
    parser.add_argument("--output", required=True, help="Directory containing GraphRAG output tables.")
    parser.add_argument(
        "--use",
        choices=sorted(USE_TABLES),
        default="global",
        help="Search/indexing use case to validate.",
    )
    parser.add_argument(
        "--byog-workflows",
        nargs="*",
        default=[],
        help="Optional BYOG/custom workflows to validate source tables for.",
    )
    parser.add_argument(
        "--embedding-name",
        action="append",
        choices=sorted(EMBEDDING_TABLES),
        help="Embedding target that should have its source table present. Repeatable.",
    )
    parser.add_argument(
        "--allow-csv",
        action="store_true",
        help="Accept CSV tables as well as parquet/json when checking file-backed outputs.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    return parser.parse_args()


def find_table(output_dir: Path, table: str, allow_csv: bool) -> Path | None:
    extensions = EXTENSIONS if allow_csv else [".parquet", ".json"]
    candidates = [output_dir / f"{table}{ext}" for ext in extensions]
    candidates.extend(output_dir.glob(f"**/{table}.parquet"))
    if allow_csv:
        candidates.extend(output_dir.glob(f"**/{table}.csv"))
    candidates.extend(output_dir.glob(f"**/{table}.json"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def read_columns(path: Path) -> tuple[set[str], str | None]:
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            return set(next(reader, [])), None
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return set(data[0]), None
        if isinstance(data, dict):
            return set(data), None
        return set(), "JSON table is not an object or list of objects"
    if path.suffix == ".parquet":
        try:
            import pandas as pd
        except Exception:
            return set(), "Install pandas/pyarrow to inspect parquet columns, or rely on presence-only validation."
        try:
            frame = pd.read_parquet(path)
        except Exception as exc:
            return set(), f"Could not read parquet: {exc}"
        return set(frame.columns), None
    return set(), f"Unsupported table extension: {path.suffix}"


def expected_tables(args: argparse.Namespace) -> set[str]:
    tables = set(USE_TABLES[args.use])
    for workflow in args.byog_workflows:
        tables.update(WORKFLOW_INPUTS.get(workflow, set()))
    for embedding_name in args.embedding_name or []:
        tables.add(EMBEDDING_TABLES[embedding_name])
    return tables


def validate(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output).expanduser()
    report: dict[str, Any] = {
        "ok": True,
        "output": str(output_dir),
        "use": args.use,
        "tables": {},
        "errors": [],
        "warnings": [],
    }

    if not output_dir.exists():
        report["ok"] = False
        report["errors"].append(f"Output directory does not exist: {output_dir}")
        return report

    for table in sorted(expected_tables(args)):
        path = find_table(output_dir, table, args.allow_csv)
        table_report: dict[str, Any] = {"found": path is not None}
        if path is None:
            report["ok"] = False
            report["errors"].append(f"Missing required table: {table}")
            report["tables"][table] = table_report
            continue

        table_report["path"] = str(path)
        columns, warning = read_columns(path)
        if warning:
            table_report["warning"] = warning
            report["warnings"].append(f"{table}: {warning}")
        if columns:
            table_report["columns"] = sorted(columns)
            missing_columns = sorted(REQUIRED_COLUMNS.get(table, set()) - columns)
            if missing_columns:
                report["ok"] = False
                report["errors"].append(
                    f"Table {table} is missing columns: {', '.join(missing_columns)}"
                )
                table_report["missing_columns"] = missing_columns
        report["tables"][table] = table_report

    if args.use == "byog" and "relationships" in report["tables"]:
        report["warnings"].append(
            "BYOG validation checks table presence/columns only; separately verify relationship endpoints match entity titles."
        )

    return report


def print_text(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"GraphRAG output validation: {status}")
    print(f"Output: {report['output']}")
    print(f"Use: {report['use']}")
    for table, table_report in report["tables"].items():
        marker = "found" if table_report.get("found") else "missing"
        path = f" ({table_report['path']})" if table_report.get("path") else ""
        print(f"- {table}: {marker}{path}")
        if table_report.get("missing_columns"):
            print(f"  missing columns: {', '.join(table_report['missing_columns'])}")
        if table_report.get("warning"):
            print(f"  warning: {table_report['warning']}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    report = validate(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
