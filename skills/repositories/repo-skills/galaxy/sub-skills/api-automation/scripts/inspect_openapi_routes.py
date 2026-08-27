#!/usr/bin/env python3
"""Inspect an exported Galaxy OpenAPI schema or print offline route guidance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROUTE_HINTS = {
    "histories": "Create/list histories and inspect history contents.",
    "history_contents": "Inspect datasets and collections inside histories.",
    "tools": "Upload data, fetch data, inspect tools, and run tools.",
    "workflows": "Import, update, export, invoke, and inspect workflows.",
    "jobs": "Inspect async job state and outputs.",
    "configuration": "Version, whoami, exposable config, and admin-only config helpers.",
    "users": "Current user, user details, API key management, admin user operations.",
    "libraries": "Data libraries and library datasets, often permission-sensitive.",
}


def load_schema(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".json", ""}:
        return json.loads(text)
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on optional PyYAML
        raise SystemExit(f"YAML schema requires PyYAML or use JSON export instead: {exc}")
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise SystemExit("OpenAPI schema did not parse to an object")
    return loaded


def route_tags(operation: dict[str, Any]) -> list[str]:
    tags = operation.get("tags") or []
    return [str(tag) for tag in tags]


def operation_requires_admin(operation: dict[str, Any]) -> bool:
    text = json.dumps(operation, sort_keys=True).lower()
    return "require_admin" in text or "admin" in text and "403" in text


def summarize_schema(schema: dict[str, Any], tag_filter: str | None, path_filter: str | None) -> int:
    paths = schema.get("paths")
    if not isinstance(paths, dict):
        raise SystemExit("Schema does not contain an OpenAPI paths object")
    rows: list[tuple[str, str, str, str, bool]] = []
    for path, methods in sorted(paths.items()):
        if path_filter and path_filter.lower() not in path.lower():
            continue
        if not isinstance(methods, dict):
            continue
        for method, operation in sorted(methods.items()):
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            tags = route_tags(operation)
            if tag_filter and tag_filter.lower() not in " ".join(tags).lower():
                continue
            summary = str(operation.get("summary") or operation.get("operationId") or "")
            rows.append((method.upper(), path, ",".join(tags), summary, operation_requires_admin(operation)))
    if not rows:
        print("No matching routes found.")
        return 1
    print(f"Found {len(rows)} matching route operations.\n")
    widths = [max(len(row[index]) for row in rows + [("METHOD", "PATH", "TAGS", "SUMMARY", False)]) for index in range(4)]
    print(f"{'METHOD'.ljust(widths[0])}  {'PATH'.ljust(widths[1])}  {'TAGS'.ljust(widths[2])}  ADMIN?  SUMMARY")
    print(f"{'-' * widths[0]}  {'-' * widths[1]}  {'-' * widths[2]}  ------  {'-' * max(widths[3], 7)}")
    for method, path, tags, summary, admin_hint in rows:
        admin = "maybe" if admin_hint else ""
        print(f"{method.ljust(widths[0])}  {path.ljust(widths[1])}  {tags.ljust(widths[2])}  {admin.ljust(6)}  {summary}")
    return 0


def print_offline_guidance() -> None:
    print("Galaxy OpenAPI route inspection")
    print("===============================")
    print("No schema file was supplied, so this script is in offline guidance mode.\n")
    print("How Galaxy exposes schema:")
    print("- Galaxy's FastAPI application can generate an OpenAPI schema for route discovery.")
    print("- Schema export is useful for methods, paths, tags, request bodies, response models, and admin/public hints.")
    print("- Schema export does not prove that a live user can access a specific object ID.\n")
    print("Useful API route families:")
    for tag, description in ROUTE_HINTS.items():
        print(f"- {tag}: {description}")
    print("\nIf you already have a schema file:")
    print("  python inspect_openapi_routes.py --schema openapi.json --tag workflows")
    print("  python inspect_openapi_routes.py --schema openapi.json --path /api/histories")
    print("\nIf you need to export a schema from a Galaxy checkout, use the repository's OpenAPI export tooling in an inspection environment, then inspect the exported file here.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize Galaxy OpenAPI routes from an exported JSON/YAML schema, or print offline guidance.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--schema", type=Path, help="Path to an exported OpenAPI JSON/YAML schema.")
    parser.add_argument("--tag", help="Filter by OpenAPI tag, e.g. workflows or histories.")
    parser.add_argument("--path", help="Filter by path substring, e.g. /api/workflows.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.schema:
        print_offline_guidance()
        return 0
    if not args.schema.exists():
        parser.error(f"schema file does not exist: {args.schema}")
    schema = load_schema(args.schema)
    return summarize_schema(schema, args.tag, args.path)


if __name__ == "__main__":
    sys.exit(main())
