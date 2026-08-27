#!/usr/bin/env python3
"""Validate smolagents tool schema objects in a local Python file.

This helper imports a user-provided module, locates one or more Tool instances or
Tool subclasses, checks required metadata, optionally validates call arguments,
and can print the discovered schema as JSON.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any

try:
    from smolagents import Tool
    from smolagents.tools import AUTHORIZED_TYPES, validate_tool_arguments
except Exception as exc:  # pragma: no cover - intentionally user-facing
    raise SystemExit(f"Could not import smolagents tool APIs: {exc}") from exc


REQUIRED_INPUT_KEYS = {"type", "description"}


def import_module_from_path(module_path: Path):
    if not module_path.exists():
        raise FileNotFoundError(f"No such file: {module_path}")
    module_name = f"_smolagents_tool_check_{module_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def instantiate_if_needed(candidate: Any) -> Tool:
    if isinstance(candidate, Tool):
        return candidate
    if inspect.isclass(candidate) and issubclass(candidate, Tool):
        return candidate()
    raise TypeError(f"Object {candidate!r} is not a smolagents Tool instance or subclass")


def discover_tools(module, object_names: list[str] | None) -> list[tuple[str, Tool]]:
    if object_names:
        discovered = []
        for object_name in object_names:
            if not hasattr(module, object_name):
                raise AttributeError(f"Module has no object named {object_name!r}")
            discovered.append((object_name, instantiate_if_needed(getattr(module, object_name))))
        return discovered

    discovered = []
    for name, value in vars(module).items():
        if name.startswith("_"):
            continue
        if isinstance(value, Tool):
            discovered.append((name, value))
        elif inspect.isclass(value) and issubclass(value, Tool) and value is not Tool:
            discovered.append((name, instantiate_if_needed(value)))
    return discovered


def validate_schema(tool: Tool) -> list[str]:
    errors: list[str] = []
    for attribute_name, expected_type in {
        "name": str,
        "description": str,
        "inputs": dict,
        "output_type": str,
    }.items():
        value = getattr(tool, attribute_name, None)
        if not isinstance(value, expected_type):
            errors.append(f"{tool!r}: {attribute_name} must be {expected_type.__name__}")

    if getattr(tool, "output_type", None) not in AUTHORIZED_TYPES:
        errors.append(f"{tool.name}: output_type {tool.output_type!r} is not authorized")

    for input_name, input_schema in getattr(tool, "inputs", {}).items():
        if not isinstance(input_schema, dict):
            errors.append(f"{tool.name}.{input_name}: input schema must be a dict")
            continue
        missing = REQUIRED_INPUT_KEYS - set(input_schema)
        if missing:
            errors.append(f"{tool.name}.{input_name}: missing keys {sorted(missing)}")
        input_type = input_schema.get("type")
        if isinstance(input_type, str):
            input_types = [input_type]
        elif isinstance(input_type, list):
            input_types = input_type
        else:
            errors.append(f"{tool.name}.{input_name}: type must be a string or list of strings")
            input_types = []
        for type_name in input_types:
            if type_name not in AUTHORIZED_TYPES:
                errors.append(f"{tool.name}.{input_name}: unauthorized type {type_name!r}")
        if "description" in input_schema and not isinstance(input_schema["description"], str):
            errors.append(f"{tool.name}.{input_name}: description must be a string")
        if "nullable" in input_schema and not isinstance(input_schema["nullable"], bool):
            errors.append(f"{tool.name}.{input_name}: nullable must be a boolean when present")

    output_schema = getattr(tool, "output_schema", None)
    if output_schema is not None and not isinstance(output_schema, dict):
        errors.append(f"{tool.name}: output_schema must be a dict when present")
    return errors


def schema_summary(tool: Tool) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "inputs": tool.inputs,
        "output_type": tool.output_type,
        "output_schema": getattr(tool, "output_schema", None),
    }


def parse_json_object(raw_json: str | None) -> Any:
    if raw_json is None:
        return None
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--call-json must be valid JSON: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate smolagents Tool schemas in a Python file.")
    parser.add_argument("module", type=Path, help="Python file containing Tool objects or subclasses.")
    parser.add_argument(
        "--object",
        dest="objects",
        action="append",
        help="Object name to validate. Repeat for multiple. Defaults to discovering all public tools.",
    )
    parser.add_argument(
        "--call-json",
        help="Optional JSON arguments to validate with validate_tool_arguments for every selected tool.",
    )
    parser.add_argument("--print-schema", action="store_true", help="Print selected tool schemas as JSON.")
    args = parser.parse_args()

    module = import_module_from_path(args.module.resolve())
    tools = discover_tools(module, args.objects)
    if not tools:
        print("No smolagents Tool instances or subclasses found.", file=sys.stderr)
        return 1

    call_arguments = parse_json_object(args.call_json)
    all_errors: list[str] = []
    summaries = []
    for object_name, tool in tools:
        errors = validate_schema(tool)
        if call_arguments is not None:
            try:
                validate_tool_arguments(tool, call_arguments)
            except Exception as exc:  # pragma: no cover - user-facing details vary
                errors.append(f"{tool.name}: call arguments failed validation: {exc}")
        if errors:
            all_errors.extend(f"{object_name}: {error}" for error in errors)
        summaries.append(schema_summary(tool))

    if args.print_schema:
        print(json.dumps(summaries, indent=2, sort_keys=True))

    if all_errors:
        print("Tool validation failed:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(tools)} tool(s): " + ", ".join(tool.name for _, tool in tools))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
