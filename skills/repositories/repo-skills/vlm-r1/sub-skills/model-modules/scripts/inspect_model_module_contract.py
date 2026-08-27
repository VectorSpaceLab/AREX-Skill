#!/usr/bin/env python3
"""Static VLM-R1 model-module contract checker.

This script imports only the Python standard library. It parses model-module
source files with ``ast`` and reports classes that look like VLM-R1 modules,
missing base-contract methods, and missing GRPO runtime hooks.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

BASE_REQUIRED_METHODS = [
    "get_vlm_key",
    "get_model_class",
    "get_processing_class",
    "get_vision_modules_keywords",
    "get_custom_multimodal_keywords",
    "get_non_generate_params",
    "get_custom_processing_keywords",
    "prepare_prompt",
    "prepare_model_inputs",
]

# Called by the GRPO JSONL entry point for every selected module class.
RUNTIME_REQUIRED_METHODS = ["get_question_template"]

# Defaults may exist or hooks may be optional, but new integrated modules should
# make these decisions explicitly. ``--strict`` makes these fail the run.
RECOMMENDED_METHODS = ["post_model_init", "is_embeds_input", "select_reward_func"]

ALL_CONTRACT_METHODS = BASE_REQUIRED_METHODS + RUNTIME_REQUIRED_METHODS + RECOMMENDED_METHODS


@dataclass
class ClassReport:
    file: str
    class_name: str
    bases: list[str]
    detected_key: str | None
    methods: list[str]
    missing_required: list[str]
    missing_runtime: list[str]
    missing_recommended: list[str]

    @property
    def ok_core(self) -> bool:
        return not self.missing_required and not self.missing_runtime

    @property
    def ok_strict(self) -> bool:
        return self.ok_core and not self.missing_recommended


@dataclass
class ScanReport:
    paths: list[str]
    classes: list[ClassReport]
    parse_errors: list[dict[str, str]]
    routing_functions: list[dict[str, object]]
    expect_key: str | None
    expect_key_found_in_class: bool
    expect_key_found_in_routing_literals: bool


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def iter_py_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob("*.py")):
                if "__pycache__" in child.parts:
                    continue
                files.append(child)
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"No such file or directory: {path}")
    seen: set[Path] = set()
    unique: list[Path] = []
    for file in files:
        resolved = file.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(file)
    return unique


def base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = base_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Subscript):
        return base_name(node.value)
    if isinstance(node, ast.Call):
        return base_name(node.func)
    return ""


def class_method_names(node: ast.ClassDef) -> list[str]:
    names = [item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return sorted(set(names))


def looks_like_vlm_module(node: ast.ClassDef, methods: set[str], bases: list[str]) -> bool:
    if node.name == "VLMBaseModule":
        return False
    if any(base.endswith("VLMBaseModule") for base in bases):
        return True
    # Heuristic for a pasted module with omitted base in the snippet.
    identity = {"get_vlm_key", "get_model_class", "prepare_model_inputs"}
    return identity.issubset(methods) or len(methods.intersection(BASE_REQUIRED_METHODS)) >= 6


def detect_simple_vlm_key(node: ast.ClassDef) -> str | None:
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "get_vlm_key":
            for child in ast.walk(item):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
                    return child.value.value
    return None


def string_literals(tree: ast.AST) -> list[str]:
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def routing_function_reports(tree: ast.AST, file: Path) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "get_vlm_module":
            reports.append(
                {
                    "file": display_path(file),
                    "function": node.name,
                    "line": node.lineno,
                    "string_literals": sorted(set(string_literals(node))),
                }
            )
    return reports


def scan(paths: list[Path], expect_key: str | None = None) -> ScanReport:
    files = iter_py_files(paths)
    classes: list[ClassReport] = []
    parse_errors: list[dict[str, str]] = []
    routing_functions: list[dict[str, object]] = []
    routing_literals: list[str] = []

    for file in files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        except SyntaxError as exc:
            parse_errors.append({"file": display_path(file), "error": f"SyntaxError: {exc}"})
            continue
        except UnicodeDecodeError as exc:
            parse_errors.append({"file": display_path(file), "error": f"UnicodeDecodeError: {exc}"})
            continue

        file_routing = routing_function_reports(tree, file)
        routing_functions.extend(file_routing)
        for report in file_routing:
            routing_literals.extend(str(x) for x in report.get("string_literals", []))

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods = set(class_method_names(node))
            bases = [base_name(base) for base in node.bases]
            if not looks_like_vlm_module(node, methods, bases):
                continue
            missing_required = [name for name in BASE_REQUIRED_METHODS if name not in methods]
            missing_runtime = [name for name in RUNTIME_REQUIRED_METHODS if name not in methods]
            missing_recommended = [name for name in RECOMMENDED_METHODS if name not in methods]
            classes.append(
                ClassReport(
                    file=display_path(file),
                    class_name=node.name,
                    bases=bases,
                    detected_key=detect_simple_vlm_key(node),
                    methods=sorted(methods.intersection(ALL_CONTRACT_METHODS)),
                    missing_required=missing_required,
                    missing_runtime=missing_runtime,
                    missing_recommended=missing_recommended,
                )
            )

    expect = expect_key.lower() if expect_key else None
    expect_key_found_in_class = False
    expect_key_found_in_routing_literals = False
    if expect:
        expect_key_found_in_class = any((report.detected_key or "").lower() == expect for report in classes)
        expect_key_found_in_routing_literals = any(expect in literal.lower() for literal in routing_literals)

    return ScanReport(
        paths=[display_path(path) for path in paths],
        classes=classes,
        parse_errors=parse_errors,
        routing_functions=routing_functions,
        expect_key=expect_key,
        expect_key_found_in_class=expect_key_found_in_class,
        expect_key_found_in_routing_literals=expect_key_found_in_routing_literals,
    )


def report_to_dict(report: ScanReport) -> dict[str, object]:
    return {
        "paths": report.paths,
        "classes": [asdict(item) for item in report.classes],
        "parse_errors": report.parse_errors,
        "routing_functions": report.routing_functions,
        "expect_key": report.expect_key,
        "expect_key_found_in_class": report.expect_key_found_in_class,
        "expect_key_found_in_routing_literals": report.expect_key_found_in_routing_literals,
    }


def print_text_report(report: ScanReport, strict: bool) -> None:
    mode = "strict" if strict else "core"
    print(f"VLM-R1 model-module contract scan ({mode})")
    print("Paths:")
    for path in report.paths:
        print(f"  - {path}")

    if report.parse_errors:
        print("\nParse errors:")
        for error in report.parse_errors:
            print(f"  - {error['file']}: {error['error']}")

    if not report.classes:
        print("\nNo VLM module classes detected.")
    else:
        print("\nDetected module classes:")
        for item in report.classes:
            status = "PASS" if (item.ok_strict if strict else item.ok_core) else "FAIL"
            print(f"  - {status} {item.class_name} ({item.file})")
            print(f"    bases: {', '.join(item.bases) if item.bases else '(none)'}")
            print(f"    detected_key: {item.detected_key or '(not statically detected)'}")
            if item.missing_required:
                print(f"    missing_required: {', '.join(item.missing_required)}")
            if item.missing_runtime:
                print(f"    missing_runtime: {', '.join(item.missing_runtime)}")
            if item.missing_recommended:
                label = "missing_recommended"
                if strict:
                    label += " (strict failure)"
                print(f"    {label}: {', '.join(item.missing_recommended)}")

    if report.routing_functions:
        print("\nDetected routing functions:")
        for routing in report.routing_functions:
            literals = ", ".join(routing.get("string_literals", [])) or "(no string literals)"
            print(f"  - {routing['function']} at {routing['file']}:{routing['line']} strings=[{literals}]")

    if report.expect_key:
        print("\nExpected key check:")
        print(f"  - key: {report.expect_key}")
        print(f"  - class_get_vlm_key_match: {report.expect_key_found_in_class}")
        if report.routing_functions:
            print(f"  - routing_literal_match: {report.expect_key_found_in_routing_literals}")
        else:
            print("  - routing_literal_match: not checked (no get_vlm_module function scanned)")


def should_fail(report: ScanReport, strict: bool) -> bool:
    if report.parse_errors:
        return True
    if not report.classes:
        return True
    if any(item.missing_required or item.missing_runtime for item in report.classes):
        return True
    if strict and any(item.missing_recommended for item in report.classes):
        return True
    if report.expect_key and not report.expect_key_found_in_class:
        return True
    if report.expect_key and report.routing_functions and not report.expect_key_found_in_routing_literals:
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Statically validate VLM-R1 model-module source files without importing the repository."
    )
    parser.add_argument("paths", nargs="+", help="Python module file(s) or directory/directories to scan.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail when recommended hooks such as post_model_init, is_embeds_input, or select_reward_func are missing.",
    )
    parser.add_argument(
        "--expect-key",
        help="Require a scanned module class to have a simple get_vlm_key() return value matching this key. If a routing function is scanned, also require the key to appear in routing string literals.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    args = parser.parse_args(argv)

    try:
        report = scan([Path(path) for path in args.paths], expect_key=args.expect_key)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report_to_dict(report), indent=2, sort_keys=True))
    else:
        print_text_report(report, strict=args.strict)

    return 1 if should_fail(report, strict=args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
