#!/usr/bin/env python3
"""Safely inspect Galaxy tool-util entry points and optional local artifacts.

This helper is intentionally read-only by default. It reports expected
`galaxy-tool-util` CLI entry points, can check imports/help parsers, and can
validate user-supplied XML or YAML test files without contacting a Galaxy server
or external package/container services.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Callable
import xml.etree.ElementTree as StdlibElementTree

EXPECTED_ENTRY_POINTS = {
    "galaxy-tool-format": "galaxy.tool_util.format:main",
    "galaxy-tool-test": "galaxy.tool_util.verify.script:main",
    "galaxy-tool-test-case-validation": "galaxy.tool_util.parameters.scripts.validate_test_cases:main",
    "galaxy-tool-upgrade-advisor": "galaxy.tool_util.upgrade.script:main",
    "validate-test-format": "galaxy.tool_util.validate_test_format:main",
    "mulled-build": "galaxy.tool_util.deps.mulled.mulled_build:main",
    "mulled-build-channel": "galaxy.tool_util.deps.mulled.mulled_build_channel:main",
    "mulled-build-files": "galaxy.tool_util.deps.mulled.mulled_build_files:main",
    "mulled-build-tool": "galaxy.tool_util.deps.mulled.mulled_build_tool:main",
    "mulled-hash": "galaxy.tool_util.deps.mulled.mulled_hash:main",
    "mulled-list": "galaxy.tool_util.deps.mulled.mulled_list:main",
    "mulled-search": "galaxy.tool_util.deps.mulled.mulled_search:main",
    "mulled-update-singularity-containers": "galaxy.tool_util.deps.mulled.mulled_update_singularity_containers:main",
}

PARSER_FACTORIES = {
    "galaxy-tool-format": "galaxy.tool_util.format:arg_parser",
    "galaxy-tool-test": "galaxy.tool_util.verify.script:arg_parser",
    "galaxy-tool-upgrade-advisor": "galaxy.tool_util.upgrade.script:arg_parser",
    "validate-test-format": "galaxy.tool_util.validate_test_format:arg_parser",
}


def import_object(spec: str) -> Any:
    module_name, object_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def expected_entry_points() -> list[dict[str, Any]]:
    return [
        {"command": command, "target": target, "ok": True, "error": None}
        for command, target in EXPECTED_ENTRY_POINTS.items()
    ]


def check_imports() -> list[dict[str, Any]]:
    results = []
    for command, spec in EXPECTED_ENTRY_POINTS.items():
        try:
            imported = import_object(spec)
            results.append({"command": command, "target": spec, "ok": callable(imported), "error": None})
        except Exception as exc:  # pragma: no cover - diagnostic path
            results.append({"command": command, "target": spec, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return results


def check_help_parsers() -> list[dict[str, Any]]:
    results = []
    for command, spec in PARSER_FACTORIES.items():
        try:
            factory: Callable[[], argparse.ArgumentParser] = import_object(spec)
            parser = factory()
            help_text = parser.format_help()
            results.append(
                {
                    "command": command,
                    "target": spec,
                    "ok": bool(help_text and "usage:" in help_text),
                    "description": parser.description,
                    "error": None,
                }
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            results.append({"command": command, "target": spec, "ok": False, "description": None, "error": f"{type(exc).__name__}: {exc}"})
    return results


def parse_tool_xml(path: Path) -> dict[str, Any]:
    try:
        tree = StdlibElementTree.parse(path)
        root = tree.getroot()
    except StdlibElementTree.ParseError as exc:
        return {"path": str(path), "ok": False, "error": f"XML parse error: {exc}"}
    except OSError as exc:
        return {"path": str(path), "ok": False, "error": f"I/O error: {exc}"}

    if root.tag != "tool":
        return {"path": str(path), "ok": False, "error": f"expected root <tool>, found <{root.tag}>"}

    tests = root.find("tests")
    requirements = root.find("requirements")
    outputs = root.find("outputs")
    inputs = root.find("inputs")
    return {
        "path": str(path),
        "ok": True,
        "id": root.attrib.get("id"),
        "name": root.attrib.get("name"),
        "version": root.attrib.get("version"),
        "profile": root.attrib.get("profile"),
        "tool_type": root.attrib.get("tool_type"),
        "has_command": root.find("command") is not None,
        "input_count": len(list(inputs)) if inputs is not None else 0,
        "output_count": len(list(outputs)) if outputs is not None else 0,
        "test_count": len(tests.findall("test")) if tests is not None else 0,
        "requirement_count": len(requirements.findall("requirement")) if requirements is not None else 0,
    }


def validate_test_file(path: Path) -> dict[str, Any]:
    try:
        validate_test_format = import_object("galaxy.tool_util.validate_test_format:validate_test_file")
        validate_test_format(str(path))
        return {"path": str(path), "ok": True, "error": None}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"path": str(path), "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Galaxy tool-util CLI entry points and optional local tool/test files.")
    parser.add_argument("--check-imports", action="store_true", help="Import expected galaxy-tool-util entry point targets.")
    parser.add_argument("--help-checks", action="store_true", help="Build known argparse parsers and verify help text is available.")
    parser.add_argument("--tool-xml", action="append", type=Path, default=[], help="Parse a Galaxy tool XML file and summarize basic structure.")
    parser.add_argument("--test-file", action="append", type=Path, default=[], help="Validate a YAML test file with galaxy.tool_util.validate_test_format.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable text report.")
    return parser


def print_section(title: str, rows: list[dict[str, Any]]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not rows:
        print("(not requested)")
        return
    for row in rows:
        status = "ok" if row.get("ok") else "FAIL"
        label = row.get("command") or row.get("path") or row.get("target")
        print(f"{status}: {label}")
        for key in sorted(row):
            if key in {"ok", "command", "path"} or row[key] in {None, ""}:
                continue
            print(f"  {key}: {row[key]}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    metadata_only = not (args.check_imports or args.help_checks or args.tool_xml or args.test_file)

    report = {
        "entry_points": check_imports() if args.check_imports else expected_entry_points() if metadata_only else [],
        "help_parsers": check_help_parsers() if args.help_checks else [],
        "tool_xml": [parse_tool_xml(path) for path in args.tool_xml],
        "test_files": [validate_test_file(path) for path in args.test_file],
    }

    failures = [row for rows in report.values() for row in rows if not row.get("ok")]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_section("Entry Points", report["entry_points"])
        print_section("Help Parsers", report["help_parsers"])
        print_section("Tool XML", report["tool_xml"])
        print_section("Test Files", report["test_files"])

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
