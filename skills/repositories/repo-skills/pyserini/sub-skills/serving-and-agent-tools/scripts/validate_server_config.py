#!/usr/bin/env python3
"""Validate a Pyserini REST/MCP server YAML config without starting a server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_INDEX_TYPES = {"tf", "impact", "lucene_flat", "lucene_hnsw", "faiss"}
ENCODER_REQUIRED_TYPES = {"impact", "faiss", "lucene_flat", "lucene_hnsw"}


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _as_nonempty_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _parse_alias(alias: Any, raw: Any, config_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    alias_name = str(alias).strip() if alias is not None else ""
    if not alias_name:
        _error(errors, "Index aliases in config must be non-empty")
        return None

    if isinstance(raw, str):
        path_value = raw
        index_type = "tf"
        base_index = None
        encoder = None
        ef_search = None
    elif isinstance(raw, dict):
        path_value = raw.get("path")
        index_type = raw.get("index_type", "tf")
        base_index = raw.get("base_index")
        encoder = raw.get("encoder")
        ef_search = raw.get("ef_search")
    else:
        _error(errors, f'Index alias "{alias_name}" must map to a path string or object with path/index_type fields')
        return None

    path_string = _as_nonempty_string(path_value)
    if path_string is None:
        _error(errors, f'Index alias "{alias_name}" must map to a non-empty path')
        return None

    if not isinstance(index_type, str) or not index_type.strip():
        _error(errors, f'Index alias "{alias_name}" has invalid "index_type" (must be a non-empty string)')
        index_type = ""
    else:
        index_type = index_type.strip()
        if index_type not in VALID_INDEX_TYPES:
            _error(errors, f'Index alias "{alias_name}" has unsupported index_type "{index_type}"')

    if base_index is not None:
        base_index = _as_nonempty_string(base_index)
        if base_index is None:
            _error(errors, f'Index alias "{alias_name}" has invalid "base_index" (must be a non-empty string when set)')

    if encoder is not None:
        encoder = _as_nonempty_string(encoder)
        if encoder is None:
            _error(errors, f'Index alias "{alias_name}" has invalid "encoder" (must be a non-empty string when set)')
    if index_type in ENCODER_REQUIRED_TYPES and not encoder:
        _error(errors, f'Index alias "{alias_name}" requires "encoder" when index_type is "{index_type}"')

    if ef_search is not None and (not isinstance(ef_search, int) or ef_search <= 0):
        _error(errors, f'Index alias "{alias_name}" has invalid "ef_search" (must be a positive integer when set)')

    resolved_path = Path(path_string)
    if not resolved_path.is_absolute():
        resolved_path = (config_dir / resolved_path).resolve()
    exists = resolved_path.is_dir()
    if not exists:
        _error(errors, f'Index alias "{alias_name}" points to missing path: {resolved_path}')

    return {
        "name": alias_name,
        "path": path_string,
        "resolved_path": str(resolved_path),
        "path_exists": exists,
        "index_type": index_type,
        "base_index": base_index,
        "encoder": encoder,
        "ef_search": ef_search,
    }


def validate_config(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.is_file():
        return {"ok": False, "errors": [f"Config file not found: {path}"], "warnings": [], "indexes": []}

    try:
        import yaml
    except ImportError:
        return {
            "ok": False,
            "errors": ["PyYAML is required: install pyyaml or use an environment with Pyserini server dependencies."],
            "warnings": [],
            "indexes": [],
        }

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - parser-specific exceptions are environment dependent
        return {"ok": False, "errors": [f"YAML parse error: {exc}"], "warnings": [], "indexes": []}

    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return {"ok": False, "errors": ["Config root must be a mapping/object"], "warnings": [], "indexes": []}

    api_keys_raw = payload.get("api_keys")
    api_key_count = 0
    if api_keys_raw is not None:
        if not isinstance(api_keys_raw, list):
            _error(errors, 'Config "api_keys" must be a list of strings')
        else:
            for index, item in enumerate(api_keys_raw):
                if not isinstance(item, str) or not item.strip():
                    _error(errors, f"Config api_keys entry #{index} must be a non-empty string")
                else:
                    api_key_count += 1

    indexes_raw = payload.get("indexes")
    aliases: list[dict[str, Any]] = []
    if indexes_raw is None:
        warnings.append("No indexes mapping found; --no-prebuilt-indexes would be invalid.")
    elif not isinstance(indexes_raw, dict) or not indexes_raw:
        warnings.append("indexes is empty or not a mapping; --no-prebuilt-indexes would be invalid.")
        if not isinstance(indexes_raw, dict):
            _error(errors, 'Config "indexes" must be a non-empty mapping when present')
    else:
        for alias, raw in indexes_raw.items():
            parsed = _parse_alias(alias, raw, path.resolve().parent, errors)
            if parsed is not None:
                aliases.append(parsed)

    alias_by_name = {alias["name"]: alias for alias in aliases}
    for alias in aliases:
        base_index = alias.get("base_index")
        if not base_index:
            continue
        target = alias_by_name.get(base_index)
        if target is None:
            _error(errors, f'Index alias "{alias["name"]}" references unknown base_index "{base_index}"')
        elif target.get("index_type") != "tf":
            _error(errors, f'Index alias "{alias["name"]}" must reference a TF base_index, got "{base_index}"')

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "api_key_count": api_key_count,
        "indexes": aliases,
        "no_prebuilt_indexes_ready": bool(aliases) and not errors,
    }


def _print_text_report(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"Pyserini server config validation: {status}")
    print(f"API keys: {report.get('api_key_count', 0)}")
    print(f"Indexes: {len(report.get('indexes', []))}")
    print(f"Ready for --no-prebuilt-indexes: {'yes' if report.get('no_prebuilt_indexes_ready') else 'no'}")

    for alias in report.get("indexes", []):
        details = [alias["index_type"], "exists" if alias["path_exists"] else "missing"]
        if alias.get("base_index"):
            details.append(f"base={alias['base_index']}")
        if alias.get("encoder"):
            details.append("encoder=yes")
        if alias.get("ef_search") is not None:
            details.append(f"ef_search={alias['ef_search']}")
        print(f"- {alias['name']}: {', '.join(details)} -> {alias['resolved_path']}")

    for warning in report.get("warnings", []):
        print(f"WARNING: {warning}")
    for error in report.get("errors", []):
        print(f"ERROR: {error}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to a Pyserini REST/MCP server YAML config")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report")
    args = parser.parse_args(argv)

    report = validate_config(args.config)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
