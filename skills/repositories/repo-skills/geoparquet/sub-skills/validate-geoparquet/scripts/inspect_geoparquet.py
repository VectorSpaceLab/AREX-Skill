#!/usr/bin/env python3
"""Inspect a Parquet footer, GeoParquet metadata, native types, and statistics."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _validator_module():
    # Resolve the sibling module from this file, not from the caller's CWD.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import validate_geo_metadata

    return validate_geo_metadata


def _json_logical_type(column: Any) -> Any:
    try:
        logical = column.logical_type
        if logical is None:
            return None
        encoded = logical.to_json()
        return json.loads(encoded) if isinstance(encoded, str) else encoded
    except Exception:
        return str(getattr(column, "logical_type", None))


def _stats_dict(stats: Any) -> Any:
    if stats is None:
        return None
    try:
        value = stats.to_dict()
        if isinstance(value, dict):
            return value
    except Exception:
        pass
    result = {}
    for key in (
        "geospatial_types",
        "xmin",
        "xmax",
        "ymin",
        "ymax",
        "zmin",
        "zmax",
        "mmin",
        "mmax",
    ):
        if hasattr(stats, key):
            result[key] = getattr(stats, key)
    return result or None


def inspect(path: Path, require_statistics: bool = False) -> tuple[dict[str, Any], list[str]]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(f"pyarrow is required: {exc}") from exc
    try:
        parquet = pq.ParquetFile(path)
    except Exception as exc:
        raise RuntimeError(f"cannot read Parquet footer {path}: {exc}") from exc

    footer_metadata = parquet.metadata.metadata or {}
    raw_geo = footer_metadata.get(b"geo") or footer_metadata.get("geo")
    geo: Any = None
    geo_error: str | None = None
    if raw_geo is None:
        geo_error = "footer has no 'geo' key"
    else:
        try:
            geo = json.loads(
                raw_geo.decode("utf-8") if isinstance(raw_geo, bytes) else raw_geo
            )
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            geo_error = f"footer 'geo' value is not valid JSON: {exc}"

    columns: list[dict[str, Any]] = []
    for column in parquet.schema:
        index = parquet.schema.names.index(column.name)
        row_groups: list[dict[str, Any]] = []
        for row_group_index in range(parquet.metadata.num_row_groups):
            chunk = parquet.metadata.row_group(row_group_index).column(index)
            is_set = bool(getattr(chunk, "is_geo_stats_set", False))
            row_groups.append(
                {
                    "geo_statistics_set": is_set,
                    "geo_statistics": _stats_dict(getattr(chunk, "geo_statistics", None))
                    if is_set
                    else None,
                }
            )
        columns.append(
            {
                "name": column.name,
                "path": str(getattr(column, "path", column.name)),
                "physical_type": str(getattr(column, "physical_type", "")),
                "logical_type": _json_logical_type(column),
                "logical_type_name": _validator_module().logical_type_name(column),
                "max_definition_level": getattr(column, "max_definition_level", None),
                "max_repetition_level": getattr(column, "max_repetition_level", None),
                "row_groups": row_groups,
            }
        )

    native_columns = [
        item["name"]
        for item in columns
        if item["logical_type_name"] in ("Geometry", "Geography")
    ]
    report: dict[str, Any] = {
        "file": str(path),
        "num_rows": parquet.metadata.num_rows,
        "num_row_groups": parquet.metadata.num_row_groups,
        "schema_names": parquet.schema.names,
        "metadata_keys": sorted(
            key.decode("utf-8", "replace") if isinstance(key, bytes) else str(key)
            for key in footer_metadata
        ),
        "geo_metadata": geo,
        "geo_metadata_error": geo_error,
        "columns": columns,
        "classification": {
            "has_geo_metadata": isinstance(geo, dict),
            "native_geometry_columns": native_columns,
            "note": (
                "native Parquet Geometry/Geography plus valid geo metadata are "
                "both required for a GeoParquet 2.0 conformance claim; metadata "
                "alone is not sufficient"
            ),
        },
    }

    validator = _validator_module()
    errors: list[str] = []
    if geo_error:
        errors.append(geo_error)
    elif not isinstance(geo, dict):
        errors.append("footer 'geo' value is not a JSON object")
    else:
        errors.extend(validator.metadata_errors(geo))
        if not errors:
            footer_errors, warnings = validator.parquet_errors(
                path, geo, require_statistics=require_statistics
            )
            errors.extend(footer_errors)
            if warnings:
                report["warnings"] = warnings
    return report, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parquet", type=Path, help="Parquet file to inspect")
    parser.add_argument(
        "--require-conformant",
        action="store_true",
        help="fail for any local GeoParquet 2.0 conformance error",
    )
    parser.add_argument(
        "--require-statistics",
        action="store_true",
        help="treat missing native geo statistics as an error",
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)

    try:
        report, errors = inspect(
            args.parquet,
            require_statistics=args.require_statistics or args.require_conformant,
        )
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        print(f"INSPECTION FAILED: {exc}", file=sys.stderr)
        return 1

    report["conformance_errors"] = errors
    report["conformant"] = not errors
    print(
        json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":") if args.compact else None,
            indent=None if args.compact else 2,
        )
    )
    # A diagnostic report is still useful on failure, but invalid metadata or
    # a failed structural check must be visible to shell callers.
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
