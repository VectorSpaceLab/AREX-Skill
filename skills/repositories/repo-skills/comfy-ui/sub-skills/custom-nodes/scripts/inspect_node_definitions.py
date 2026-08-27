#!/usr/bin/env python3
"""Statically inspect classic ComfyUI custom node definitions."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REQUIRED_ATTRS = ("INPUT_TYPES", "RETURN_TYPES", "FUNCTION", "CATEGORY")
KNOWN_HIDDEN = {"PROMPT", "UNIQUE_ID", "EXTRA_PNGINFO", "DYNPROMPT"}


@dataclass
class Issue:
    level: str
    message: str
    node: str | None = None


@dataclass
class NodeSummary:
    class_name: str
    mapping_id: str | None = None
    display_name: str | None = None
    category: str | None = None
    function: str | None = None
    return_count: int | None = None
    return_types: list[str] = field(default_factory=list)
    hidden_values: list[str] = field(default_factory=list)
    uses_any: bool = False
    issues: list[Issue] = field(default_factory=list)


def literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def class_attr_map(cls: ast.ClassDef) -> dict[str, ast.AST]:
    attrs: dict[str, ast.AST] = {}
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    attrs[target.id] = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            attrs[stmt.target.id] = stmt.value
    return attrs


def method_names(cls: ast.ClassDef) -> set[str]:
    return {stmt.name for stmt in cls.body if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))}


def find_input_types_method(cls: ast.ClassDef) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for stmt in cls.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "INPUT_TYPES":
            return stmt
    return None


def find_return_expr(function: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.AST | None:
    for stmt in ast.walk(function):
        if isinstance(stmt, ast.Return):
            return stmt.value
    return None


def mapping_dicts(tree: ast.Module) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign) or not isinstance(stmt.value, ast.Dict):
            continue
        for target in stmt.targets:
            if not isinstance(target, ast.Name) or not target.id.endswith("NODE_CLASS_MAPPINGS"):
                continue
            mapping: dict[str, str] = {}
            for key_node, val_node in zip(stmt.value.keys, stmt.value.values):
                key = literal(key_node) if key_node is not None else None
                if not isinstance(key, str):
                    continue
                if isinstance(val_node, ast.Name):
                    mapping[key] = val_node.id
                else:
                    value = literal(val_node)
                    if isinstance(value, str):
                        mapping[key] = value
            if mapping:
                result[target.id] = mapping
    return result


def display_mapping(tree: ast.Module, mapping_name: str) -> dict[str, str]:
    display_name = mapping_name.replace("NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS")
    result: dict[str, str] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == display_name for target in stmt.targets):
            continue
        value = literal(stmt.value)
        if isinstance(value, dict):
            result.update({str(k): str(v) for k, v in value.items() if isinstance(k, str) and isinstance(v, str)})
    return result


def contains_any(value: Any) -> bool:
    if value == "*":
        return True
    if isinstance(value, str) and value.upper() == "ANY":
        return True
    if isinstance(value, (list, tuple, set)):
        return any(contains_any(item) for item in value)
    if isinstance(value, dict):
        return any(contains_any(key) or contains_any(val) for key, val in value.items())
    return False


def extract_hidden(input_types: Any) -> list[str]:
    if not isinstance(input_types, dict):
        return []
    hidden = input_types.get("hidden")
    if not isinstance(hidden, dict):
        return []
    values: list[str] = []
    for value in hidden.values():
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, (tuple, list)) and value and isinstance(value[0], str):
            values.append(value[0])
    return values


def return_tuple_count(expr: ast.AST | None) -> int | None:
    if isinstance(expr, ast.Tuple):
        return len(expr.elts)
    if isinstance(expr, ast.Dict):
        for key, value in zip(expr.keys, expr.values):
            if literal(key) == "result" and isinstance(value, ast.Tuple):
                return len(value.elts)
        return None
    return None


def inspect_file(path: Path) -> tuple[list[NodeSummary], list[Issue]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    all_mappings = mapping_dicts(tree)
    file_issues: list[Issue] = []
    summaries: list[NodeSummary] = []

    if not all_mappings:
        file_issues.append(Issue("ERROR", "missing or non-literal NODE_CLASS_MAPPINGS"))
        all_mappings = {"<unmapped classes>": {class_name: class_name for class_name in classes}}

    preferred_names = ["NODE_CLASS_MAPPINGS"] + sorted(name for name in all_mappings if name != "NODE_CLASS_MAPPINGS")
    for mapping_name in preferred_names:
        if mapping_name not in all_mappings:
            continue
        mappings = all_mappings[mapping_name]
        displays = display_mapping(tree, mapping_name)
        candidate_classes = {class_name: classes[class_name] for class_name in mappings.values() if class_name in classes}
        for mapping_id, class_name in mappings.items():
            if class_name not in classes:
                file_issues.append(Issue("ERROR", f"mapping {mapping_id!r} points to missing class {class_name!r}"))

        reverse_mapping = {class_name: mapping_id for mapping_id, class_name in mappings.items()}

        for class_name, cls in candidate_classes.items():
            attrs = class_attr_map(cls)
            methods = method_names(cls)
            summary = NodeSummary(class_name=class_name, mapping_id=reverse_mapping.get(class_name))
            summary.display_name = displays.get(summary.mapping_id or "")

            for attr in REQUIRED_ATTRS:
                if attr == "INPUT_TYPES":
                    if find_input_types_method(cls) is None:
                        summary.issues.append(Issue("ERROR", "missing INPUT_TYPES classmethod", summary.mapping_id or class_name))
                elif attr not in attrs:
                    summary.issues.append(Issue("ERROR", f"missing {attr}", summary.mapping_id or class_name))

            return_types = literal(attrs.get("RETURN_TYPES")) if "RETURN_TYPES" in attrs else None
            if isinstance(return_types, str):
                summary.issues.append(Issue("ERROR", "RETURN_TYPES must be a tuple/list, not a string", summary.mapping_id or class_name))
            elif isinstance(return_types, (tuple, list)):
                summary.return_count = len(return_types)
                summary.return_types = [str(item) for item in return_types]
                if contains_any(return_types):
                    summary.uses_any = True
                    summary.issues.append(Issue("WARN", "RETURN_TYPES uses ANY/'*'; prefer concrete types when possible", summary.mapping_id or class_name))
            elif "RETURN_TYPES" in attrs:
                summary.issues.append(Issue("WARN", "RETURN_TYPES is dynamic; static length check skipped", summary.mapping_id or class_name))

            for aligned_attr in ("RETURN_NAMES", "OUTPUT_IS_LIST", "OUTPUT_TOOLTIPS"):
                value = literal(attrs.get(aligned_attr)) if aligned_attr in attrs else None
                if isinstance(value, (tuple, list)) and summary.return_count is not None and len(value) != summary.return_count:
                    summary.issues.append(Issue("ERROR", f"{aligned_attr} length {len(value)} does not match RETURN_TYPES length {summary.return_count}", summary.mapping_id or class_name))

            function_name = literal(attrs.get("FUNCTION")) if "FUNCTION" in attrs else None
            if isinstance(function_name, str):
                summary.function = function_name
                if function_name not in methods:
                    summary.issues.append(Issue("ERROR", f"FUNCTION names missing method {function_name!r}", summary.mapping_id or class_name))
                else:
                    func = next(stmt for stmt in cls.body if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == function_name)
                    observed = return_tuple_count(find_return_expr(func))
                    if observed is not None and summary.return_count is not None and observed != summary.return_count:
                        summary.issues.append(Issue("ERROR", f"probable return tuple length {observed} does not match RETURN_TYPES length {summary.return_count}", summary.mapping_id or class_name))
            elif "FUNCTION" in attrs:
                summary.issues.append(Issue("ERROR", "FUNCTION must be a literal method name string", summary.mapping_id or class_name))

            category = literal(attrs.get("CATEGORY")) if "CATEGORY" in attrs else None
            if isinstance(category, str):
                summary.category = category

            input_method = find_input_types_method(cls)
            if input_method is not None:
                return_expr = find_return_expr(input_method)
                input_literal = literal(return_expr) if return_expr is not None else None
                if isinstance(input_literal, dict):
                    if contains_any(input_literal):
                        summary.uses_any = True
                        summary.issues.append(Issue("WARN", "INPUT_TYPES uses ANY/'*'; prefer concrete types when possible", summary.mapping_id or class_name))
                    summary.hidden_values = extract_hidden(input_literal)
                    for hidden in summary.hidden_values:
                        if hidden not in KNOWN_HIDDEN:
                            summary.issues.append(Issue("WARN", f"unknown hidden input value {hidden!r}", summary.mapping_id or class_name))
                else:
                    summary.issues.append(Issue("WARN", "INPUT_TYPES return is dynamic; static input checks skipped", summary.mapping_id or class_name))

            summaries.append(summary)

    return summaries, file_issues


def print_report(path: Path, summaries: list[NodeSummary], file_issues: list[Issue]) -> int:
    exit_code = 0
    print(f"{path}:")
    for issue in file_issues:
        print(f"  [{issue.level}] {issue.message}")
        if issue.level == "ERROR":
            exit_code = 1
    for summary in summaries:
        label = summary.mapping_id or summary.class_name
        if summary.return_count == 0:
            outputs = "none"
        else:
            outputs = ", ".join(summary.return_types) if summary.return_types else "unknown"
        print(f"  node {label} ({summary.class_name})")
        print(f"    display: {summary.display_name or '-'}")
        print(f"    category: {summary.category or '-'}")
        print(f"    function: {summary.function or '-'}")
        print(f"    outputs: {outputs}")
        if summary.hidden_values:
            print(f"    hidden: {', '.join(summary.hidden_values)}")
        if summary.uses_any:
            print("    any: yes")
        for issue in summary.issues:
            print(f"    [{issue.level}] {issue.message}")
            if issue.level == "ERROR":
                exit_code = 1
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Statically inspect classic ComfyUI custom-node Python files.")
    parser.add_argument("paths", nargs="+", type=Path, help="Python files to inspect")
    args = parser.parse_args()

    exit_code = 0
    for path in args.paths:
        try:
            summaries, file_issues = inspect_file(path)
        except SyntaxError as exc:
            print(f"{path}: [ERROR] syntax error: {exc}")
            exit_code = 1
            continue
        except OSError as exc:
            print(f"{path}: [ERROR] cannot read file: {exc}")
            exit_code = 1
            continue
        exit_code = max(exit_code, print_report(path, summaries, file_issues))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
