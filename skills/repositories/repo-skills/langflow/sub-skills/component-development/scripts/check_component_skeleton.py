#!/usr/bin/env python3
"""Static and optional import checks for Langflow component skeletons."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PASCALISH_RE = re.compile(r"^[A-Z][A-Za-z0-9_]*$")
REQUIRED_CLASS_ATTRS = ("display_name", "description", "icon", "inputs", "outputs")


@dataclass
class Finding:
    level: str
    message: str


@dataclass
class ClassReport:
    name: str
    findings: list[Finding] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.findings.append(Finding("ERROR", message))

    def warning(self, message: str) -> None:
        self.findings.append(Finding("WARN", message))

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "ERROR"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "WARN"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Langflow Component subclass for required class metadata, inputs/outputs, "
            "and statically visible Output(method=...) references."
        )
    )
    parser.add_argument("component_file", type=Path, help="Python file containing a Langflow Component subclass.")
    parser.add_argument("--class", dest="class_name", help="Specific component class to check when a file has many classes.")
    parser.add_argument(
        "--import-module",
        action="store_true",
        help="Import the target module and inspect runtime class attributes. This may import optional provider SDKs.",
    )
    parser.add_argument(
        "--module-name",
        default=None,
        help="Module name to use with --import-module. Defaults to a temporary name based on the file stem.",
    )
    parser.add_argument(
        "--add-path",
        action="append",
        default=[],
        type=Path,
        help="Path to prepend to sys.path before --import-module. Can be passed more than once.",
    )
    parser.add_argument(
        "--allow-inherited-output-methods",
        action="store_true",
        help="Warn instead of failing when a static Output(method=...) is not defined directly on the class.",
    )
    parser.add_argument("--fail-on-warnings", action="store_true", help="Exit non-zero when warnings are present.")
    return parser.parse_args()


def base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return base_name(node.value)
    return None


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return base_name(node.func)
    return None


def is_component_subclass(node: ast.ClassDef) -> bool:
    return any(base_name(base) == "Component" for base in node.bases)


def assigned_class_attrs(node: ast.ClassDef) -> dict[str, ast.AST]:
    attrs: dict[str, ast.AST] = {}
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    attrs[target.id] = item.value
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            attrs[item.target.id] = item.value if item.value is not None else item
    return attrs


def class_methods(node: ast.ClassDef) -> set[str]:
    return {item.name for item in node.body if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)}


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def is_none_literal(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def keyword_value(call: ast.Call, name: str) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def iter_static_calls(value: ast.AST | None) -> tuple[list[ast.Call], bool]:
    if isinstance(value, ast.List | ast.Tuple):
        calls = [elt for elt in value.elts if isinstance(elt, ast.Call)]
        fully_static = len(calls) == len(value.elts)
        return calls, fully_static
    return [], False


def extract_named_calls(value: ast.AST | None) -> tuple[list[tuple[str | None, ast.Call]], bool]:
    calls, fully_static = iter_static_calls(value)
    named: list[tuple[str | None, ast.Call]] = []
    for call in calls:
        named.append((literal_string(keyword_value(call, "name")), call))
    return named, fully_static


def check_static_class(node: ast.ClassDef, args: argparse.Namespace) -> ClassReport:
    report = ClassReport(node.name)
    attrs = assigned_class_attrs(node)
    methods = class_methods(node)

    if not PASCALISH_RE.match(node.name):
        report.warning("Class name should be PascalCase so saved-flow component types stay readable.")
    if not node.name.endswith("Component"):
        report.warning("Class name does not end with 'Component'; this is allowed but should be intentional.")

    for attr in REQUIRED_CLASS_ATTRS:
        if attr not in attrs:
            report.error(f"Missing required class attribute: {attr}")

    for attr in ("display_name", "description", "icon"):
        if attr in attrs:
            value = literal_string(attrs[attr])
            if value is None:
                report.warning(f"{attr} is not a static string; make sure it resolves to a non-empty string.")
            elif not value.strip():
                report.error(f"{attr} must not be empty.")

    if "name" in attrs:
        name_value = literal_string(attrs["name"])
        if name_value is None:
            report.warning("name is not a static string; keep released internal names stable.")
        elif not name_value.strip():
            report.error("name must not be an empty string when provided.")

    input_entries, inputs_static = extract_named_calls(attrs.get("inputs"))
    output_entries, outputs_static = extract_named_calls(attrs.get("outputs"))

    if "inputs" in attrs and not inputs_static:
        report.warning("inputs is not a fully static list/tuple of input constructor calls; manual review needed.")
    if "outputs" in attrs and not outputs_static:
        report.warning("outputs is not a fully static list/tuple of Output constructor calls; manual review needed.")

    input_names = {name for name, _call in input_entries if name}
    output_names = {name for name, _call in output_entries if name}
    if "inputs" in attrs and inputs_static and not input_entries:
        report.warning("inputs is empty; confirm the component intentionally needs no user/config inputs.")
    if "outputs" in attrs and outputs_static and not output_entries:
        report.error("outputs is empty; normal Langflow components need at least one Output.")

    overlap = sorted(input_names & output_names)
    if overlap:
        report.error(f"Input and output names overlap: {', '.join(overlap)}")

    for index, (output_name, call) in enumerate(output_entries, start=1):
        if call_name(call) != "Output":
            report.warning(f"outputs[{index}] is not an Output(...) call; static method check skipped.")
            continue
        if not output_name:
            report.error(f"outputs[{index}] is missing a static non-empty name=... value.")
        method_node = keyword_value(call, "method")
        method = literal_string(method_node)
        if method_node is None or is_none_literal(method_node):
            report.error(f"Output {output_name or index!r} is missing method=... .")
            continue
        if method is None:
            report.warning(f"Output {output_name or index!r} method is not a static string; manual review needed.")
            continue
        if method not in methods:
            message = f"Output {output_name or index!r} references method '{method}', but it is not defined on {node.name}."
            if args.allow_inherited_output_methods:
                report.warning(message)
            else:
                report.error(message)

    return report


def find_static_component_classes(tree: ast.Module, class_name: str | None) -> list[ast.ClassDef]:
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and is_component_subclass(node)]
    if class_name:
        return [node for node in classes if node.name == class_name]
    return classes


def import_target_module(path: Path, module_name: str | None, add_paths: list[Path]) -> Any:
    for add_path in reversed(add_paths):
        sys.path.insert(0, str(add_path.resolve()))
    sys.path.insert(0, str(path.parent.resolve()))
    name = module_name or f"_langflow_component_check_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_runtime_classes(module: Any, class_names: list[str], args: argparse.Namespace) -> list[ClassReport]:
    try:
        from lfx.custom.custom_component.component import Component
    except Exception as exc:  # noqa: BLE001
        report = ClassReport("runtime-import")
        report.error(f"Could not import lfx Component for runtime subclass checks: {exc}")
        return [report]

    reports: list[ClassReport] = []
    for class_name in class_names:
        report = ClassReport(f"{class_name} runtime")
        cls = getattr(module, class_name, None)
        if cls is None:
            report.error(f"Class {class_name!r} was not found after importing the module.")
            reports.append(report)
            continue
        if not isinstance(cls, type) or not issubclass(cls, Component):
            report.error(f"{class_name!r} is not a runtime subclass of lfx Component.")
            reports.append(report)
            continue

        for attr in REQUIRED_CLASS_ATTRS:
            if not hasattr(cls, attr):
                report.error(f"Runtime class is missing attribute {attr}.")

        for attr in ("display_name", "description", "icon"):
            value = getattr(cls, attr, None)
            if not isinstance(value, str) or not value.strip():
                report.error(f"Runtime {attr} must be a non-empty string.")

        inputs = getattr(cls, "inputs", []) or []
        outputs = getattr(cls, "outputs", []) or []
        input_names = {getattr(input_obj, "name", None) for input_obj in inputs if getattr(input_obj, "name", None)}
        output_names = {getattr(output_obj, "name", None) for output_obj in outputs if getattr(output_obj, "name", None)}
        overlap = sorted(input_names & output_names)
        if overlap:
            report.error(f"Runtime input and output names overlap: {', '.join(overlap)}")
        if not outputs:
            report.error("Runtime outputs list is empty.")

        for output in outputs:
            output_name = getattr(output, "name", "<unnamed>")
            method = getattr(output, "method", None)
            if not method:
                report.error(f"Runtime Output {output_name!r} is missing method.")
            elif not hasattr(cls, method):
                report.error(f"Runtime Output {output_name!r} references missing method '{method}'.")

        reports.append(report)
    return reports


def print_reports(reports: list[ClassReport]) -> None:
    for report in reports:
        print(f"\n{report.name}")
        if not report.findings:
            print("  OK: no issues found")
            continue
        for finding in report.findings:
            print(f"  {finding.level}: {finding.message}")


def main() -> int:
    args = parse_args()
    component_file = args.component_file
    if not component_file.exists():
        print(f"ERROR: file does not exist: {component_file}", file=sys.stderr)
        return 2
    if not component_file.is_file():
        print(f"ERROR: path is not a file: {component_file}", file=sys.stderr)
        return 2

    try:
        source = component_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(component_file))
    except SyntaxError as exc:
        print(f"ERROR: syntax error in {component_file}: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: could not read {component_file}: {exc}", file=sys.stderr)
        return 2

    static_classes = find_static_component_classes(tree, args.class_name)
    if not static_classes:
        if args.class_name:
            print(f"ERROR: no Component subclass named {args.class_name!r} found in {component_file}", file=sys.stderr)
        else:
            print(f"ERROR: no class inheriting from Component found in {component_file}", file=sys.stderr)
        return 1

    reports = [check_static_class(node, args) for node in static_classes]

    if args.import_module:
        try:
            module = import_target_module(component_file, args.module_name, args.add_path)
        except Exception as exc:  # noqa: BLE001
            report = ClassReport("module import")
            report.error(f"Failed to import target module: {exc}")
            reports.append(report)
        else:
            reports.extend(check_runtime_classes(module, [node.name for node in static_classes], args))

    print_reports(reports)

    error_count = sum(len(report.errors) for report in reports)
    warning_count = sum(len(report.warnings) for report in reports)
    print(f"\nSummary: {error_count} error(s), {warning_count} warning(s)")
    if error_count:
        return 1
    if args.fail_on_warnings and warning_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
