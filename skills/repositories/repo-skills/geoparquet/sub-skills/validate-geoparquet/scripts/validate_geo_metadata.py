#!/usr/bin/env python3
"""Validate GeoParquet 2.0 metadata and optionally a Parquet footer.

The default path is local and offline.  It checks the GeoParquet metadata
shape, the safe local shape of inline PROJJSON, native Geometry/Geography
columns, WKB physical layout, and row-group geospatial statistics when a
Parquet file is supplied.  It never downloads a schema or resolves a CRS
registry.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft7Validator
except ImportError as exc:  # pragma: no cover - depends on the host environment
    Draft7Validator = None  # type: ignore[assignment]
    _JSONSCHEMA_IMPORT_ERROR = exc
else:
    _JSONSCHEMA_IMPORT_ERROR = None


LOCAL_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GeoParquet",
    "type": "object",
    "required": ["version", "primary_column", "columns"],
    "properties": {
        "version": {"type": "string", "const": "2.0.0"},
        "primary_column": {"type": "string", "minLength": 1},
        "columns": {
            "type": "object",
            "minProperties": 1,
            "patternProperties": {
                r".+": {
                    "type": "object",
                    "required": ["encoding", "geometry_types"],
                    "properties": {
                        "encoding": {"type": "string", "const": "WKB"},
                        "geometry_types": {
                            "type": "array",
                            "uniqueItems": True,
                            "items": {
                                "type": "string",
                                "pattern": r"^(GeometryCollection|(Multi)?(Point|LineString|Polygon))( Z| M| ZM)?$",
                            },
                        },
                        # The complete PROJJSON schema is intentionally not
                        # embedded.  The semantic check below requires an
                        # object with a string `type` and rejects strings.
                        "crs": {"oneOf": [{"type": "object"}, {"type": "null"}]},
                        "edges": {
                            "type": "string",
                            "enum": [
                                "planar",
                                "spherical",
                                "vincenty",
                                "thomas",
                                "andoyer",
                                "karney",
                            ],
                        },
                        "orientation": {"type": "string", "const": "counterclockwise"},
                        "bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                            "oneOf": [
                                {"minItems": 4, "maxItems": 4},
                                {"minItems": 6, "maxItems": 6},
                                {"minItems": 8, "maxItems": 8},
                            ],
                        },
                        "epoch": {"type": "number"},
                    },
                }
            },
            "additionalProperties": False,
        },
    },
}

GEOMETRY_TYPE_RE = re.compile(
    r"^(GeometryCollection|(Multi)?(Point|LineString|Polygon))( Z| M| ZM)?$"
)
BASE_CODES = {
    "Point": 1,
    "LineString": 2,
    "Polygon": 3,
    "MultiPoint": 4,
    "MultiLineString": 5,
    "MultiPolygon": 6,
    "GeometryCollection": 7,
}
DIMENSION_OFFSETS = {"": 0, " Z": 1000, " M": 2000, " ZM": 3000}
STAT_AXIS_NAMES = ("x", "y", "z", "m")


def _path(parts: Iterable[Any]) -> str:
    result = "metadata"
    for part in parts:
        result += f"[{part!r}]" if isinstance(part, str) else f"[{part}]"
    return result


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _read_json(path: Path) -> Any:
    if str(path) == "-":
        return json.load(sys.stdin)
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def extract_geo(value: Any) -> tuple[Any, str]:
    """Accept either bare metadata or an example-style ``{"geo": ...}``."""
    if isinstance(value, dict) and "geo" in value:
        return value["geo"], "geo wrapper"
    return value, "bare metadata"


def _localize_remote_refs(node: Any) -> Any:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(("http://", "https://")):
            return {"type": "object"}
        return {key: _localize_remote_refs(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_localize_remote_refs(value) for value in node]
    return node


def _load_schema(path: str | None) -> dict[str, Any]:
    if path is None:
        return LOCAL_SCHEMA
    value = _read_json(Path(path))
    if not isinstance(value, dict):
        raise ValueError("schema must be a JSON object")
    return _localize_remote_refs(value)


def metadata_errors(metadata: Any, schema_path: str | None = None) -> list[str]:
    """Return field-level local metadata errors."""
    if Draft7Validator is None:
        return [f"jsonschema is required: {_JSONSCHEMA_IMPORT_ERROR}"]
    try:
        schema = _load_schema(schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot load schema: {exc}"]

    errors: list[str] = []
    try:
        validator = Draft7Validator(schema)
        for error in sorted(validator.iter_errors(metadata), key=lambda item: list(item.path)):
            errors.append(f"{_path(error.path)}: {error.message}")
    except Exception as exc:
        return [f"cannot apply metadata schema: {exc}"]

    if not isinstance(metadata, dict):
        return errors

    columns = metadata.get("columns")
    primary = metadata.get("primary_column")
    if isinstance(columns, dict) and isinstance(primary, str) and primary not in columns:
        errors.append(
            f"metadata.primary_column: {primary!r} is not present in metadata.columns"
        )

    if not isinstance(columns, dict):
        return errors

    for name, column in columns.items():
        if not isinstance(column, dict):
            continue
        types = column.get("geometry_types")
        if isinstance(types, list):
            seen: set[str] = set()
            for index, value in enumerate(types):
                if isinstance(value, str):
                    if value in seen:
                        errors.append(
                            f"metadata.columns[{name!r}].geometry_types[{index}]: "
                            f"duplicate geometry type {value!r}"
                        )
                    seen.add(value)
                    if GEOMETRY_TYPE_RE.fullmatch(value) is None:
                        errors.append(
                            f"metadata.columns[{name!r}].geometry_types[{index}]: "
                            f"invalid GeoParquet type {value!r}"
                        )

        if "crs" in column:
            crs = column["crs"]
            if crs is not None:
                if not isinstance(crs, dict):
                    errors.append(
                        f"metadata.columns[{name!r}].crs: must be inline PROJJSON "
                        f"or null, not {type(crs).__name__}"
                    )
                elif not isinstance(crs.get("type"), str):
                    errors.append(
                        f"metadata.columns[{name!r}].crs: inline PROJJSON must "
                        "contain a string 'type'"
                    )

        if "bbox" in column and isinstance(column["bbox"], list):
            bbox = column["bbox"]
            if len(bbox) not in (4, 6, 8):
                errors.append(
                    f"metadata.columns[{name!r}].bbox: length {len(bbox)} is invalid; "
                    "use 4 (XY), 6 (XYZ), or 8 (XYZM)"
                )
            for index, value in enumerate(bbox):
                if not _finite_number(value):
                    errors.append(
                        f"metadata.columns[{name!r}].bbox[{index}]: "
                        "must be a finite JSON number"
                    )

        if "epoch" in column and not _finite_number(column["epoch"]):
            errors.append(
                f"metadata.columns[{name!r}].epoch: must be a finite number "
                "(decimal year)"
            )
    return errors


def logical_type_name(column: Any) -> str | None:
    """Return the native logical type name exposed by PyArrow."""
    try:
        logical = column.logical_type
        if logical is None:
            return None
        encoded = logical.to_json()
        value = json.loads(encoded) if isinstance(encoded, str) else encoded
        if isinstance(value, dict) and isinstance(value.get("Type"), str):
            name = value["Type"]
            return name if name in ("Geometry", "Geography") else None
        text = str(logical)
        if text.startswith("Geometry"):
            return "Geometry"
        if text.startswith("Geography"):
            return "Geography"
    except Exception:
        pass
    return None


def logical_type_json(column: Any) -> Any:
    try:
        logical = column.logical_type
        if logical is None:
            return None
        encoded = logical.to_json()
        return json.loads(encoded) if isinstance(encoded, str) else encoded
    except Exception:
        return str(getattr(column, "logical_type", None))


def stats_dict(stats: Any) -> dict[str, Any] | None:
    if stats is None:
        return None
    try:
        value = stats.to_dict()
        if isinstance(value, dict):
            return value
    except Exception:
        pass
    result: dict[str, Any] = {}
    for key in ("geospatial_types", "xmin", "xmax", "ymin", "ymax", "zmin", "zmax", "mmin", "mmax"):
        if hasattr(stats, key):
            result[key] = getattr(stats, key)
    return result or None


def _expected_stat_codes(types: Any) -> set[int] | None:
    if not isinstance(types, list) or not types:
        return None
    expected: set[int] = set()
    for value in types:
        if not isinstance(value, str):
            return None
        match = re.fullmatch(r"(.+?)( Z| M| ZM)?", value)
        if not match or match.group(1) not in BASE_CODES:
            return None
        expected.add(BASE_CODES[match.group(1)] + DIMENSION_OFFSETS[match.group(2) or ""])
    return expected


def _within(value: Any, lower: Any, upper: Any) -> bool:
    return (
        _finite_number(value)
        and _finite_number(lower)
        and _finite_number(upper)
        and lower <= value <= upper
    )


def parquet_errors(
    path: Path,
    metadata: dict[str, Any],
    require_statistics: bool = True,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a Parquet footer and its geo metadata."""
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        return [f"pyarrow is required for Parquet inspection: {exc}"], []
    try:
        parquet = pq.ParquetFile(path)
    except Exception as exc:
        return [f"cannot read Parquet footer {path}: {exc}"], []

    errors: list[str] = []
    warnings: list[str] = []
    metadata_columns = metadata.get("columns", {})
    if not isinstance(metadata_columns, dict):
        return ["metadata.columns is not an object"], warnings

    schema_columns = {column.name: column for column in parquet.schema}
    native_columns = {
        column.name
        for column in parquet.schema
        if logical_type_name(column) in ("Geometry", "Geography")
    }

    for name, geo_column in metadata_columns.items():
        if name not in schema_columns:
            errors.append(f"Parquet schema: geo metadata column {name!r} is absent")
            continue
        column = schema_columns[name]
        path_name = str(getattr(column, "path", name))
        if path_name != name:
            errors.append(
                f"Parquet schema column {name!r}: geometry must be root-level, "
                f"got path {path_name!r}"
            )
        if str(getattr(column, "physical_type", "")) != "BYTE_ARRAY":
            errors.append(
                f"Parquet schema column {name!r}: WKB geometry must be BYTE_ARRAY, "
                f"got {getattr(column, 'physical_type', None)}"
            )
        if getattr(column, "max_repetition_level", 0) != 0:
            errors.append(
                f"Parquet schema column {name!r}: geometry columns MUST NOT be repeated"
            )
        if getattr(column, "max_definition_level", 0) > 1:
            errors.append(
                f"Parquet schema column {name!r}: nested geometry has definition "
                f"level {column.max_definition_level}"
            )
        native_name = logical_type_name(column)
        if native_name not in ("Geometry", "Geography"):
            errors.append(
                f"Parquet schema column {name!r}: geo metadata is present but native "
                f"logical type is {native_name or 'absent'}; this is not conformant "
                "GeoParquet 2.0"
            )

        index = parquet.schema.names.index(name)
        row_group_stats: list[dict[str, Any] | None] = []
        for row_group_index in range(parquet.metadata.num_row_groups):
            chunk = parquet.metadata.row_group(row_group_index).column(index)
            is_set = bool(getattr(chunk, "is_geo_stats_set", False))
            stats = stats_dict(getattr(chunk, "geo_statistics", None)) if is_set else None
            row_group_stats.append(stats)
            if not is_set:
                message = (
                    f"Parquet row group {row_group_index}, column {name!r}: "
                    "native geo statistics are missing"
                )
                if require_statistics:
                    errors.append(message)
                else:
                    warnings.append(message)

        expected_codes = _expected_stat_codes(
            geo_column.get("geometry_types") if isinstance(geo_column, dict) else None
        )
        if expected_codes is not None:
            for row_group_index, stats in enumerate(row_group_stats):
                if stats is None:
                    continue
                actual = stats.get("geospatial_types")
                if isinstance(actual, (list, tuple)) and set(actual) != expected_codes:
                    errors.append(
                        f"Parquet row group {row_group_index}, column {name!r}: "
                        f"geospatial_types {actual!r} do not match metadata "
                        f"geometry_types {geo_column.get('geometry_types')!r}"
                    )

        bbox = geo_column.get("bbox") if isinstance(geo_column, dict) else None
        if isinstance(bbox, list) and len(bbox) in (4, 6, 8):
            midpoint = len(bbox) // 2
            lower = bbox[:midpoint]
            upper = bbox[midpoint:]
            axis_names = STAT_AXIS_NAMES[:midpoint]
            for row_group_index, stats in enumerate(row_group_stats):
                if stats is None:
                    continue
                for axis_index, axis in enumerate(axis_names):
                    minimum = stats.get(f"{axis}min")
                    maximum = stats.get(f"{axis}max")
                    if minimum is not None and not _within(
                        minimum, lower[axis_index], upper[axis_index]
                    ):
                        errors.append(
                            f"Parquet row group {row_group_index}, column {name!r}: "
                            f"{axis}min={minimum} lies outside metadata bbox {bbox!r}"
                        )
                    if maximum is not None and not _within(
                        maximum, lower[axis_index], upper[axis_index]
                    ):
                        errors.append(
                            f"Parquet row group {row_group_index}, column {name!r}: "
                            f"{axis}max={maximum} lies outside metadata bbox {bbox!r}"
                        )

    missing_metadata = sorted(native_columns - set(metadata_columns))
    if missing_metadata:
        errors.append(
            "Parquet schema: native geometry columns missing from geo metadata: "
            f"{missing_metadata}"
        )
    primary = metadata.get("primary_column")
    if isinstance(primary, str) and primary not in native_columns:
        errors.append(
            f"metadata.primary_column: {primary!r} is not a native "
            "Geometry/Geography column"
        )
    return errors, warnings


def load_input(path: Path) -> tuple[dict[str, Any], Path | None, str]:
    if path.suffix.lower() == ".parquet":
        try:
            import pyarrow.parquet as pq

            footer = pq.ParquetFile(path).metadata.metadata or {}
            raw = footer.get(b"geo") or footer.get("geo")
            if raw is None:
                raise ValueError("Parquet footer has no 'geo' key")
            value = json.loads(
                raw.decode("utf-8") if isinstance(raw, bytes) else raw
            )
            if not isinstance(value, dict):
                raise ValueError("Parquet footer 'geo' value is not a JSON object")
            return value, path, "Parquet footer"
        except json.JSONDecodeError as exc:
            raise ValueError(f"Parquet 'geo' value is not JSON: {exc}") from exc
    value, source = extract_geo(_read_json(path))
    if not isinstance(value, dict):
        raise ValueError(f"{source} must contain a JSON object")
    return value, None, source


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="metadata JSON (bare or {geo: ...}) or a .parquet file",
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        help="Parquet file to check alongside metadata JSON",
    )
    parser.add_argument(
        "--schema",
        help="optional local schema JSON; remote $ref values are not fetched",
    )
    parser.add_argument(
        "--allow-missing-statistics",
        action="store_true",
        help="warn rather than fail when native geo statistics are absent",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON")
    args = parser.parse_args(argv)

    try:
        metadata, parquet_path, source = load_input(args.input)
        parquet_path = args.parquet or parquet_path
    except (OSError, ValueError, json.JSONDecodeError, ImportError) as exc:
        report = {"valid": False, "errors": [str(exc)], "warnings": []}
        print(
            json.dumps(report, indent=2, sort_keys=True)
            if args.as_json
            else f"NON-CONFORMANT: {exc}"
        )
        return 1

    errors = metadata_errors(metadata, args.schema)
    warnings: list[str] = []
    if parquet_path is not None and not errors:
        footer_errors, warnings = parquet_errors(
            parquet_path,
            metadata,
            require_statistics=not args.allow_missing_statistics,
        )
        errors.extend(footer_errors)

    report = {
        "valid": not errors,
        "source": source,
        "metadata": metadata,
        "errors": errors,
        "warnings": warnings,
    }
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif errors:
        print("NON-CONFORMANT GeoParquet 2.0")
        for error in errors:
            print(f"- {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
    else:
        suffix = " and Parquet footer" if parquet_path else " (metadata only)"
        print(f"VALID GeoParquet 2.0 metadata{suffix}")
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
