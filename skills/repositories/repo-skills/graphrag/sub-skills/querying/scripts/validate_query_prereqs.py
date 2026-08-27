#!/usr/bin/env python3
"""Validate GraphRAG query prerequisites without running model or vector calls."""

from __future__ import annotations

import argparse
import json
import sys
from numbers import Number
from pathlib import Path
from typing import Any

METHOD_TABLES = {
    "global": {
        "required": ["entities", "communities", "community_reports"],
        "optional": [],
        "vectors": [],
    },
    "local": {
        "required": [
            "entities",
            "communities",
            "community_reports",
            "text_units",
            "relationships",
        ],
        "optional": ["covariates"],
        "vectors": ["entity_description"],
    },
    "drift": {
        "required": [
            "entities",
            "communities",
            "community_reports",
            "text_units",
            "relationships",
        ],
        "optional": [],
        "vectors": ["entity_description", "community_full_content"],
    },
    "basic": {
        "required": ["text_units"],
        "optional": [],
        "vectors": ["text_unit_text"],
    },
}

TABLE_COLUMNS = {
    "entities": {
        "required": ["id", "title", "human_readable_id", "description", "degree", "text_unit_ids"],
        "recommended": ["type", "description_embedding"],
    },
    "communities": {
        "required": ["id", "community", "level", "title", "entity_ids", "parent", "children"],
        "recommended": [],
    },
    "community_reports": {
        "required": ["id", "community", "level", "title", "summary", "full_content", "rank"],
        "recommended": ["full_content_embedding"],
    },
    "text_units": {
        "required": ["id", "text", "entity_ids", "relationship_ids", "n_tokens", "document_id"],
        "recommended": ["covariate_ids"],
    },
    "relationships": {
        "required": [
            "id",
            "human_readable_id",
            "source",
            "target",
            "description",
            "combined_degree",
            "weight",
            "text_unit_ids",
        ],
        "recommended": [],
    },
    "covariates": {
        "required": ["id", "human_readable_id", "subject_id", "type"],
        "recommended": ["object_id", "status", "start_date", "end_date", "description"],
    },
}

SUPPORTED_VECTOR_NAMES = {"text_unit_text", "entity_description", "community_full_content"}


def issue(severity: str, code: str, message: str, detail: Any = None) -> dict[str, Any]:
    item = {"severity": severity, "code": code, "message": message}
    if detail is not None:
        item["detail"] = detail
    return item


def load_yaml(path: Path, issues: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.exists():
        issues.append(issue("warning", "settings-missing", f"No settings file found at {path}"))
        return {}
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on environment
        issues.append(issue("warning", "yaml-unavailable", "Cannot parse settings YAML because PyYAML is unavailable", str(exc)))
        return {}
    try:
        loaded = yaml.safe_load(path.read_text())
    except Exception as exc:
        issues.append(issue("error", "settings-parse-failed", f"Could not parse {path}", str(exc)))
        return {}
    return loaded if isinstance(loaded, dict) else {}


def first_existing_settings(root: Path) -> Path:
    for name in ("settings.yaml", "settings.yml"):
        candidate = root / name
        if candidate.exists():
            return candidate
    return root / "settings.yaml"


def resolve_data_dir(root: Path, data_arg: str | None, settings: dict[str, Any]) -> Path:
    if data_arg:
        return Path(data_arg).expanduser().resolve()
    output_storage = settings.get("output_storage") if isinstance(settings, dict) else None
    if isinstance(output_storage, dict) and output_storage.get("base_dir"):
        base_dir = Path(str(output_storage["base_dir"])).expanduser()
        return base_dir if base_dir.is_absolute() else (root / base_dir).resolve()
    return (root / "output").resolve()


def table_path(data_dir: Path, table: str) -> Path:
    return data_dir / f"{table}.parquet"


def read_columns(path: Path, issues: list[dict[str, Any]]) -> list[str]:
    try:
        import pandas as pd  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on environment
        issues.append(issue("error", "pandas-unavailable", "Cannot inspect parquet columns because pandas is unavailable", str(exc)))
        return []
    try:
        return list(pd.read_parquet(path).columns)
    except Exception as exc:
        issues.append(issue("error", "parquet-read-failed", f"Could not read {path.name}", str(exc)))
        return []


def read_level_values(path: Path) -> list[Any]:
    try:
        import pandas as pd  # type: ignore[import-not-found]

        frame = pd.read_parquet(path, columns=["level"])
        return sorted(frame["level"].dropna().unique().tolist())
    except Exception:
        return []


def validate_tables(method: str, data_dir: Path, community_level: int | None, issues: list[dict[str, Any]]) -> dict[str, list[str]]:
    found_columns: dict[str, list[str]] = {}
    contract = METHOD_TABLES[method]

    if not data_dir.exists():
        issues.append(issue("error", "data-dir-missing", f"Data directory does not exist: {data_dir}"))
        return found_columns

    for table in contract["required"]:
        path = table_path(data_dir, table)
        if not path.exists():
            issues.append(issue("error", "table-missing", f"Required table is missing: {path.name}"))
            continue
        columns = read_columns(path, issues)
        found_columns[table] = columns
        required = TABLE_COLUMNS[table]["required"]
        recommended = TABLE_COLUMNS[table]["recommended"]
        missing = [column for column in required if column not in columns]
        if missing:
            issues.append(issue("error", "columns-missing", f"{path.name} is missing required columns", missing))
        missing_recommended = [column for column in recommended if column not in columns]
        if missing_recommended:
            issues.append(issue("warning", "columns-recommended-missing", f"{path.name} is missing recommended columns", missing_recommended))

    for table in contract["optional"]:
        path = table_path(data_dir, table)
        if not path.exists():
            issues.append(issue("info", "optional-table-missing", f"Optional table is absent: {path.name}"))
            continue
        columns = read_columns(path, issues)
        found_columns[table] = columns
        missing = [column for column in TABLE_COLUMNS[table]["required"] if column not in columns]
        if missing:
            issues.append(issue("warning", "optional-columns-missing", f"Optional {path.name} is missing columns used by covariate loading", missing))

    if community_level is not None and method in {"global", "local", "drift"}:
        for table in ("communities", "community_reports"):
            path = table_path(data_dir, table)
            if path.exists():
                levels = read_level_values(path)
                numeric_levels = [level for level in levels if isinstance(level, Number)]
                if numeric_levels and not any(level <= community_level for level in numeric_levels):
                    issues.append(issue("error", "community-level-empty", f"{path.name} has no rows at or below requested community level {community_level}", levels))
                elif levels and community_level not in levels:
                    issues.append(issue("warning", "community-level-not-exact", f"{path.name} does not contain exact level {community_level}; GraphRAG will use rows with level <= {community_level}", levels))

    return found_columns


def get_nested_number(settings: dict[str, Any], section: str, key: str) -> float | None:
    value = settings.get(section, {}) if isinstance(settings, dict) else {}
    if not isinstance(value, dict) or key not in value:
        return None
    try:
        return float(value[key])
    except (TypeError, ValueError):
        return None


def validate_config(method: str, root: Path, settings: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if method == "local":
        text_unit_prop = get_nested_number(settings, "local_search", "text_unit_prop")
        community_prop = get_nested_number(settings, "local_search", "community_prop")
        if text_unit_prop is not None and community_prop is not None and text_unit_prop + community_prop > 1:
            issues.append(issue("error", "local-proportions-invalid", "local_search.community_prop + local_search.text_unit_prop must not exceed 1", {"community_prop": community_prop, "text_unit_prop": text_unit_prop}))
    if method == "drift":
        text_unit_prop = get_nested_number(settings, "drift_search", "local_search_text_unit_prop")
        community_prop = get_nested_number(settings, "drift_search", "local_search_community_prop")
        if text_unit_prop is not None and community_prop is not None and text_unit_prop + community_prop > 1:
            issues.append(issue("error", "drift-local-proportions-invalid", "drift_search local community/text-unit proportions must not exceed 1", {"local_search_community_prop": community_prop, "local_search_text_unit_prop": text_unit_prop}))

    vector_store = settings.get("vector_store", {}) if isinstance(settings, dict) else {}
    if not isinstance(vector_store, dict):
        vector_store = {}
    index_schema = vector_store.get("index_schema", {})
    if index_schema is None:
        index_schema = {}
    if not isinstance(index_schema, dict):
        issues.append(issue("error", "vector-schema-invalid", "vector_store.index_schema must be a mapping"))
        index_schema = {}

    unknown = sorted(set(index_schema) - SUPPORTED_VECTOR_NAMES)
    if unknown:
        issues.append(issue("warning", "unknown-vector-schema", "Configured vector schema contains names GraphRAG query methods do not use", unknown))

    for vector_name in METHOD_TABLES[method]["vectors"]:
        schema = index_schema.get(vector_name)
        if schema is None:
            issues.append(issue("info", "vector-schema-default", f"vector_store.index_schema.{vector_name} is not configured; GraphRAG config validation normally defaults it"))
            schema = {"index_name": vector_name}
        if not isinstance(schema, dict):
            issues.append(issue("error", "vector-schema-entry-invalid", f"vector_store.index_schema.{vector_name} must be a mapping"))
            continue
        index_name = str(schema.get("index_name") or vector_name)
        if schema.get("id_field") not in (None, "id"):
            issues.append(issue("warning", "custom-vector-id-field", f"{vector_name} uses a custom id_field; confirm query vectors are keyed by GraphRAG canonical IDs", schema.get("id_field")))
        vector_size = schema.get("vector_size") or vector_store.get("vector_size")
        if vector_size is None:
            issues.append(issue("info", "vector-size-default", f"No vector_size is configured for {vector_name}; GraphRAG defaults may apply"))

        store_type = str(vector_store.get("type") or "lancedb")
        db_uri = vector_store.get("db_uri")
        if store_type == "lancedb" and db_uri:
            db_path = Path(str(db_uri)).expanduser()
            if not db_path.is_absolute():
                db_path = (root / db_path).resolve()
            if not db_path.exists():
                issues.append(issue("warning", "lancedb-missing", f"LanceDB path for vector store does not exist: {db_path}"))
            else:
                likely_table = db_path / f"{index_name}.lance"
                if not likely_table.exists():
                    issues.append(issue("warning", "lancedb-table-not-observed", f"Did not find local LanceDB table directory for {vector_name}", {"expected": str(likely_table), "index_name": index_name}))


def validate_query_text(method: str, query_text: str | None, issues: list[dict[str, Any]]) -> None:
    if method == "drift" and query_text is not None and not query_text.strip():
        issues.append(issue("error", "empty-drift-query", "DRIFT search should not be run with an empty query"))
    elif query_text is not None and not query_text.strip():
        issues.append(issue("warning", "empty-query", "Empty queries produce poor retrieval and may skip entity extraction"))


def print_human(issues: list[dict[str, Any]]) -> None:
    if not issues:
        print("OK: no query prerequisite issues found.")
        return
    by_severity = {"error": [], "warning": [], "info": []}
    for item in issues:
        by_severity.setdefault(item["severity"], []).append(item)
    for severity in ("error", "warning", "info"):
        entries = by_severity.get(severity, [])
        if not entries:
            continue
        print(f"{severity.upper()}S:")
        for item in entries:
            detail = f" ({item['detail']})" if "detail" in item else ""
            print(f"- [{item['code']}] {item['message']}{detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate prerequisites for GraphRAG query methods without contacting models or vector services.")
    parser.add_argument("--root", default=".", help="GraphRAG project root containing settings.yaml or settings.yml.")
    parser.add_argument("--data", help="Directory containing query parquet tables; defaults to output_storage.base_dir or ./output.")
    parser.add_argument("--method", choices=sorted(METHOD_TABLES), required=True, help="Query method to validate.")
    parser.add_argument("--community-level", type=int, help="Community level to check for global, local, or DRIFT queries.")
    parser.add_argument("--query", help="Optional query text to validate for empty-query risks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable output.")
    args = parser.parse_args()

    issues: list[dict[str, Any]] = []
    root = Path(args.root).expanduser().resolve()
    settings_path = first_existing_settings(root)
    settings = load_yaml(settings_path, issues)
    data_dir = resolve_data_dir(root, args.data, settings)

    validate_tables(args.method, data_dir, args.community_level, issues)
    validate_config(args.method, root, settings, issues)
    validate_query_text(args.method, args.query, issues)

    if args.json:
        print(json.dumps({"ok": not any(item["severity"] == "error" for item in issues), "issues": issues}, indent=2, sort_keys=True))
    else:
        print_human(issues)

    return 1 if any(item["severity"] == "error" for item in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
