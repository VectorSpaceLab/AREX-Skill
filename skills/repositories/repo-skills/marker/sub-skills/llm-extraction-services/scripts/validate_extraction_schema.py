#!/usr/bin/env python3
"""Validate a Marker ExtractionConverter schema without calling any LLM service."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel
except Exception as exc:  # pragma: no cover - import guard
    print(f"ERROR: pydantic is required: {exc}", file=sys.stderr)
    sys.exit(2)


def load_json_schema(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON schema root must be an object")
    return data


def load_python_schema(path: Path, root_class: str | None) -> tuple[dict[str, Any], str]:
    spec = importlib.util.spec_from_file_location("marker_skill_schema", path)
    if spec is None or spec.loader is None:
        raise ValueError("Could not import Python schema file")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    candidates: dict[str, type[BaseModel]] = {}
    for name, value in vars(module).items():
        if isinstance(value, type) and issubclass(value, BaseModel) and value is not BaseModel:
            candidates[name] = value

    if root_class:
        if root_class not in candidates:
            raise ValueError(
                f"Root class {root_class!r} not found among Pydantic models: {sorted(candidates)}"
            )
        model_cls = candidates[root_class]
        return model_cls.model_json_schema(), root_class

    if len(candidates) == 1:
        name, model_cls = next(iter(candidates.items()))
        return model_cls.model_json_schema(), name

    if not candidates:
        raise ValueError("No Pydantic BaseModel subclasses found")
    raise ValueError(
        "Multiple Pydantic models found; pass --root-class. "
        f"Candidates: {', '.join(sorted(candidates))}"
    )


def validate_schema_shape(schema: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    schema_type = schema.get("type")
    properties = schema.get("properties")
    any_of = schema.get("anyOf") or schema.get("oneOf")

    if schema_type != "object" and not properties and not any_of:
        warnings.append(
            "schema does not declare type=object/properties/anyOf; Marker can pass it through, "
            "but extraction works best with an object root"
        )
    if properties is not None and not isinstance(properties, dict):
        raise ValueError("schema properties must be an object")
    required = schema.get("required")
    if required is not None and not isinstance(required, list):
        raise ValueError("schema required must be a list when present")
    if not schema.get("title"):
        warnings.append("schema has no title; add one for clearer LLM prompts")
    if properties == {}:
        warnings.append("schema properties is empty")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Pydantic or JSON schema for Marker structured extraction."
    )
    parser.add_argument("schema_file", help="Path to a .py Pydantic schema or .json schema file")
    parser.add_argument("--root-class", help="Pydantic root class name when the Python file has multiple models")
    parser.add_argument("--print-json", action="store_true", help="Print the rendered JSON schema")
    args = parser.parse_args()

    path = Path(args.schema_file)
    if not path.exists():
        print(f"ERROR: schema file not found: {path}", file=sys.stderr)
        return 2

    try:
        if path.suffix.lower() == ".py":
            schema, root_name = load_python_schema(path, args.root_class)
            source = f"pydantic:{root_name}"
        else:
            schema = load_json_schema(path)
            source = "json"
        warnings = validate_schema_shape(schema)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: loaded {source} schema with top-level keys: {', '.join(sorted(schema.keys()))}")
    props = schema.get("properties")
    if isinstance(props, dict):
        print(f"Properties: {', '.join(sorted(props)) if props else '(none)'}")
    required = schema.get("required")
    if isinstance(required, list):
        print(f"Required: {', '.join(map(str, required)) if required else '(none)'}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if args.print_json:
        print(json.dumps(schema, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
