#!/usr/bin/env python3
"""Validate a Snakemake config file or sample table with snakemake.utils.validate.

Examples:
  python validate_config_schema.py --data config.yaml --schema config.schema.yaml
  python validate_config_schema.py --data samples.tsv --schema samples.schema.yaml --table tsv --index sample
  python validate_config_schema.py --data samples.csv --schema samples.schema.yaml --table csv --dump-normalized samples.normalized.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any


def _load_mapping(path: Path) -> dict[str, Any]:
    import yaml

    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() == ".json":
            data = json.load(handle)
        else:
            data = yaml.safe_load(handle)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a top-level JSON/YAML mapping")
    return data


def _load_table(path: Path, table_format: str, index: str | None):
    import pandas as pd

    if table_format == "csv":
        data = pd.read_csv(path)
    elif table_format == "tsv":
        data = pd.read_csv(path, sep="\t")
    else:
        raise ValueError(f"Unsupported table format: {table_format}")
    if index:
        if index not in data.columns:
            raise KeyError(f"Index column {index!r} is not present in {path}")
        data = data.set_index(index, drop=False)
    return data


def _dump_normalized(data: Any, destination: Path, table_format: str | None) -> None:
    if table_format:
        separator = "," if table_format == "csv" else "\t"
        data.to_csv(destination, sep=separator, index=False)
    else:
        import yaml

        with destination.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False)


def _schema_path_for_validation(schema_path: Path) -> tuple[str, tempfile.TemporaryDirectory[str] | None]:
    """Return a schema path usable by Snakemake 9.23.1 validation.

    Snakemake's validator relies on the `referencing` package, which needs a
    JSON Schema draft declaration. Many compact workflow schemas omit `$schema`,
    so this helper writes a temporary normalized schema in the same directory
    shape without mutating the user's original file.
    """
    schema = _load_mapping(schema_path)
    if "$schema" in schema:
        return str(schema_path), None

    schema = dict(schema)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    temporary_directory = tempfile.TemporaryDirectory(prefix="snakemake-schema-")
    normalized_path = Path(temporary_directory.name) / schema_path.name
    import yaml

    with normalized_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(schema, handle, sort_keys=False)
    return str(normalized_path), temporary_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Snakemake config mapping or sample table against a JSON/YAML "
            "schema using snakemake.utils.validate. Defaults from the schema are "
            "applied unless --no-defaults is set."
        )
    )
    parser.add_argument("--data", required=True, type=Path, help="Config YAML/JSON file or sample table to validate.")
    parser.add_argument("--schema", required=True, type=Path, help="JSON/YAML schema file.")
    parser.add_argument("--table", choices=("csv", "tsv"), help="Treat --data as a sample table instead of a mapping.")
    parser.add_argument("--index", help="Optional sample table column to set as the pandas index before validation.")
    parser.add_argument("--no-defaults", action="store_true", help="Disable schema default insertion by passing set_default=False.")
    parser.add_argument("--dump-normalized", type=Path, help="Write data after validation/default insertion to this path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        from snakemake.utils import validate

        data = (
            _load_table(args.data, args.table, args.index)
            if args.table
            else _load_mapping(args.data)
        )
        schema_path, temporary_directory = _schema_path_for_validation(args.schema)
        try:
            validate(data, schema_path, set_default=not args.no_defaults)
        finally:
            if temporary_directory is not None:
                temporary_directory.cleanup()
        if args.dump_normalized:
            _dump_normalized(data, args.dump_normalized, args.table)
        print(f"OK: {args.data} validates against {args.schema}")
        return 0
    except Exception as error:  # noqa: BLE001 - CLI preflight should surface any validation/import/load failure.
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
