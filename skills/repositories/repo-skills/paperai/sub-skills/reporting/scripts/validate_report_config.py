#!/usr/bin/env python3
"""Validate paperai report YAML shape without importing paperai or loading models.

Usage:
    python validate_report_config.py report.yml
    cat report.yml | python validate_report_config.py -

The validator intentionally checks structure, not txtai options, model
availability, SQLite schema, query relevance, or PDF readability.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

RESERVED = {"id", "name", "options", "fields"}
RENDERERS = {"md", "csv", "ant"}
DTYPES = {"int", "days", "weeks", "months", "years"}
STANDARD_COLUMNS = {"Id", "Date", "Study", "Study Link", "Journal", "Source", "Entry", "Matches"}


def issue(message: str, *, level: str = "error", path: str | None = None) -> dict[str, str]:
    item = {"level": level, "message": message}
    if path:
        item["path"] = path
    return item


def is_mapping(value: Any) -> bool:
    return isinstance(value, dict)


def flatten_one_level(columns: list[Any]) -> list[Any]:
    flattened: list[Any] = []
    for column in columns:
        flattened.extend(column if isinstance(column, list) else [column])
    return flattened


def validate(source: Any) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    queries: list[dict[str, Any]] = []

    if not is_mapping(source):
        errors.append(issue("root YAML value must be a mapping", path="<root>"))
        return {"valid": False, "errors": errors, "warnings": warnings, "queries": queries}

    name = source.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(issue("root requires a non-empty string 'name'", path="name"))

    options = source.get("options")
    if options is not None and not is_mapping(options):
        errors.append(issue("options must be a mapping when present", path="options"))
    elif is_mapping(options):
        render = options.get("render")
        if render is not None and render not in RENDERERS:
            errors.append(issue("render must be one of md, csv, ant", path="options.render"))
        for key in ("topn", "threshold"):
            if key in options and not isinstance(options[key], (int, float)):
                errors.append(issue(f"{key} should be numeric", path=f"options.{key}"))

    for query_name, query in source.items():
        if query_name in RESERVED:
            continue
        query_path = str(query_name)
        record: dict[str, Any] = {"name": str(query_name)}
        if not is_mapping(query):
            errors.append(issue("query must be a mapping", path=query_path))
            queries.append(record)
            continue

        if not isinstance(query.get("query"), str) or not query.get("query", "").strip():
            errors.append(issue("query requires a non-empty string 'query'", path=f"{query_path}.query"))
        columns = query.get("columns")
        if not isinstance(columns, list):
            errors.append(issue("query requires a list 'columns'", path=f"{query_path}.columns"))
            queries.append(record)
            continue

        flattened = flatten_one_level(columns)
        if not flattened:
            errors.append(issue("columns must contain at least one column", path=f"{query_path}.columns"))
        record["column_count"] = len(flattened)
        record["standard_columns"] = []
        record["generated_columns"] = []
        record["constant_columns"] = []
        for index, column in enumerate(flattened):
            column_path = f"{query_path}.columns[{index}]"
            if not is_mapping(column):
                errors.append(issue("column must be a mapping with a name", path=column_path))
                continue
            column_name = column.get("name")
            if not isinstance(column_name, str) or not column_name.strip():
                errors.append(issue("column requires a non-empty string 'name'", path=f"{column_path}.name"))
                continue
            if "constant" in column and "query" in column:
                errors.append(issue("column cannot define both constant and query", path=column_path))
            if "constant" in column:
                record["constant_columns"].append(column_name)
            elif "query" in column:
                if not isinstance(column["query"], str) or not column["query"].strip():
                    errors.append(issue("generated column query must be a non-empty string", path=f"{column_path}.query"))
                if "question" in column and not isinstance(column["question"], str):
                    errors.append(issue("question must be a string when present", path=f"{column_path}.question"))
                dtype = column.get("dtype")
                if isinstance(dtype, str) and dtype not in DTYPES:
                    warnings.append(issue("unknown dtype is passed through but will not be converted by paperai", level="warning", path=f"{column_path}.dtype"))
                elif dtype is not None and not isinstance(dtype, (str, list)):
                    errors.append(issue("dtype must be a string or label list", path=f"{column_path}.dtype"))
                if isinstance(dtype, list) and not all(isinstance(label, str) for label in dtype):
                    errors.append(issue("categorical dtype labels must be strings", path=f"{column_path}.dtype"))
                record["generated_columns"].append(column_name)
            else:
                record["standard_columns"].append(column_name)
                if column_name not in STANDARD_COLUMNS:
                    warnings.append(issue("unknown standard field is not copied from SQLite and may fail row construction", level="warning", path=column_path))
        queries.append(record)

    if not queries:
        errors.append(issue("at least one top-level query mapping is required", path="<root>"))

    return {
        "valid": not errors,
        "name": name if isinstance(name, str) else None,
        "query_count": len(queries),
        "queries": queries,
        "errors": errors,
        "warnings": warnings,
    }


def load(source: str) -> Any:
    if source == "-":
        return yaml.safe_load(sys.stdin.read())
    with Path(source).open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="YAML file path, or '-' to read stdin")
    args = parser.parse_args()
    try:
        result = validate(load(args.source))
    except (OSError, yaml.YAMLError) as exc:
        result = {"valid": False, "errors": [issue(f"cannot parse YAML: {exc}", path=args.source)], "warnings": [], "queries": []}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
