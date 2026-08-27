#!/usr/bin/env python3
"""Validate a verl @function_tool file and emit a JSON report.

This helper imports the target Python file through verl's function-tool loader.
Importing a Python file executes top-level code, so use it only with trusted
local tool modules. No network or external service calls are made by this
script itself.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import a verl function_tool_path file and report registered tool schemas as JSON.",
    )
    parser.add_argument("tool_file", help="Python file containing @function_tool declarations")
    parser.add_argument(
        "--tool",
        action="append",
        default=None,
        help="Expected tool name. May be passed multiple times; reports missing names.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Include traceback text on import/schema failures",
    )
    return parser


def _tool_to_dict(tool: Any) -> dict[str, Any]:
    schema = tool.tool_schema.model_dump(exclude_unset=True, exclude_none=True)
    function = schema.get("function", {})
    parameters = function.get("parameters", {}) or {}
    properties = parameters.get("properties", {}) or {}
    required = parameters.get("required", []) or []
    return {
        "name": tool.name,
        "is_async": bool(getattr(tool, "is_async", False)),
        "description": function.get("description"),
        "parameters": sorted(properties),
        "required": sorted(required),
        "schema": schema,
    }


def _validate(path: Path, expected: list[str] | None, include_traceback: bool) -> tuple[int, dict[str, Any]]:
    report: dict[str, Any] = {
        "ok": False,
        "tool_file": str(path),
        "tools": [],
        "missing_expected_tools": [],
        "warnings": [],
        "error": None,
    }

    if not path.exists():
        report["error"] = f"file does not exist: {path}"
        return 2, report
    if not path.is_file():
        report["error"] = f"not a file: {path}"
        return 2, report

    try:
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        from verl.tools import function_tool as function_tool_mod
        from verl.tools.function_tool import load_function_tools_from_path

        function_tool_mod.FUNCTION_TOOL_REGISTRY.clear()
        function_tool_mod._LOADED_FUNCTION_TOOL_PATHS.clear()
        tools = load_function_tools_from_path(str(path))
        report["tools"] = [_tool_to_dict(tool) for tool in tools]
    except Exception as exc:  # noqa: BLE001 - report schema/import errors as JSON
        report["error"] = f"{type(exc).__name__}: {exc}"
        if include_traceback:
            report["traceback"] = traceback.format_exc()
        return 1, report

    names = {tool["name"] for tool in report["tools"]}
    if expected:
        report["missing_expected_tools"] = sorted(set(expected) - names)
    if not report["tools"]:
        report["warnings"].append("No @function_tool declarations were loaded from this file.")

    report["ok"] = not report["missing_expected_tools"] and report["error"] is None
    return (0 if report["ok"] else 1), report


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    exit_code, report = _validate(Path(args.tool_file).expanduser(), args.tool, args.traceback)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
