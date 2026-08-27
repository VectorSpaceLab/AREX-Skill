#!/usr/bin/env python3
"""Generate a small Wren v5 project from a dlt-produced DuckDB file.

The helper is intentionally conservative: it creates source YAML but does not
contact SaaS APIs, write into an existing non-empty output directory, create a
profile, or run a database query.

Usage:
  python introspect_dlt_project.py --duckdb-path source.duckdb --output-dir analytics --project-name analytics
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


INTERNAL_TABLE_PREFIXES = ("_dlt_",)
INTERNAL_COLUMNS = {"_dlt_id", "_dlt_parent_id", "_dlt_load_id", "_dlt_list_idx"}


def slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return text or "model"


def normalize_type(raw: str) -> str:
    try:
        from wren.type_mapping import parse_type

        return parse_type(raw, "duckdb")
    except Exception:
        # A caller should inspect and correct any unsupported type before build.
        return raw.upper() or "VARCHAR"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckdb-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--project-name", required=True)
    args = parser.parse_args()

    db_path = args.duckdb_path.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    if not db_path.is_file():
        parser.error(f"DuckDB file not found: {db_path}")
    if output.exists() and any(output.iterdir()):
        parser.error(f"output directory is not empty: {output}; this helper does not merge projects")

    try:
        import duckdb
        import yaml
    except ImportError as exc:
        print(f"Missing dependency: {exc}. Install wrenai (and DuckDB support) before retrying.")
        return 2

    output.mkdir(parents=True, exist_ok=True)
    catalog = db_path.stem
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
            """
        ).fetchall()
        tables = [
            (schema, table)
            for schema, table in rows
            if not any(table.startswith(prefix) for prefix in INTERNAL_TABLE_PREFIXES)
        ]
        if not tables:
            print("No non-dlt base tables found; no project was generated.")
            return 1

        project = {
            "schema_version": 5,
            "name": args.project_name,
            "catalog": "wren",
            "schema": "public",
            "data_source": "duckdb",
        }
        (output / "wren_project.yml").write_text(yaml.safe_dump(project, sort_keys=False))
        (output / "relationships.yml").write_text("relationships: []\n")
        (output / "knowledge" / "rules").mkdir(parents=True, exist_ok=True)
        (output / "knowledge" / "sql").mkdir(parents=True, exist_ok=True)
        (output / "knowledge" / "knowledge.yml").write_text("schema_version: 1\n")

        used_names: set[str] = set()
        for schema, table in tables:
            name = slug(table)
            base = name
            suffix = 2
            while name in used_names:
                name = f"{base}_{suffix}"
                suffix += 1
            used_names.add(name)
            columns = con.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = ? AND table_name = ?
                ORDER BY ordinal_position
                """,
                [schema, table],
            ).fetchall()
            mdl_columns = [
                {
                    "name": col_name,
                    "type": normalize_type(raw_type),
                    **({"not_null": True} if nullable == "NO" else {}),
                }
                for col_name, raw_type, nullable in columns
                if col_name not in INTERNAL_COLUMNS
            ]
            model = {
                "name": name,
                "table_reference": {"catalog": catalog, "schema": schema, "table": table},
                "columns": mdl_columns,
                "properties": {
                    "description": "Generated from a local DuckDB table; review names, keys, relationships, and business meaning before production use."
                },
            }
            model_dir = output / "models" / name
            model_dir.mkdir(parents=True, exist_ok=True)
            (model_dir / "metadata.yml").write_text(yaml.safe_dump(model, sort_keys=False, allow_unicode=True))
    finally:
        con.close()

    print(f"Generated {len(tables)} model(s) in {output}")
    print("Next: review YAML, then run `wren context validate` and `wren context build` from the output directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
