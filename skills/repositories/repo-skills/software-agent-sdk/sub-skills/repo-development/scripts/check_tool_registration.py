#!/usr/bin/env python3
"""Check that ToolDefinition subclasses are registered."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def _get_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return _get_name(node.value)
    return ""


def check_tool_registration(
    file_path: Path, is_special_file: bool = False
) -> list[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except Exception as exc:
        return [f"Error reading file: {exc}"]

    tool_classes: set[str] = set()
    registered_tools: set[str] = set()
    imports_register_tool = False

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and "openhands.sdk.tool" in node.module
        ):
            for alias in node.names:
                if alias.name == "register_tool":
                    imports_register_tool = True
        elif isinstance(node, ast.ClassDef):
            if any("ToolDefinition" in _get_name(base) for base in node.bases):
                tool_classes.add(node.name)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value
            if (
                isinstance(func.func, ast.Name)
                and func.func.id == "register_tool"
                and len(func.args) >= 2
            ):
                if isinstance(func.args[1], ast.Name):
                    registered_tools.add(func.args[1].id)

    if not tool_classes:
        return []

    errors: list[str] = []
    if not is_special_file and not imports_register_tool:
        errors.append(
            "File defines Tool classes but does not import register_tool from "
            "openhands.sdk.tool"
        )
    missing = tool_classes - registered_tools
    if is_special_file:
        if not registered_tools:
            errors.append("File defines Tool classes but none are registered.")
    else:
        for tool in sorted(missing):
            errors.append(
                f"Tool '{tool}' is defined but not registered. Add: "
                f"register_tool({tool}.name, {tool})"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    tools_path = repo_root / "openhands-tools" / "openhands" / "tools"
    skip_patterns = {"__init__.py", "preset", "impl.py", "executor.py"}
    special_files = {"browser_use/definition.py", "delegate/definition.py"}

    if args.files:
        files_to_check = [
            Path(f).resolve()
            for f in args.files
            if str(tools_path) in str(Path(f).resolve())
            and Path(f).name.endswith(".py")
        ]
    else:
        files_to_check = list(tools_path.rglob("*.py"))
    files_to_check = [
        f
        for f in files_to_check
        if not any(pattern in str(f) for pattern in skip_patterns)
    ]

    all_errors: list[str] = []
    for file_path in files_to_check:
        rel = file_path.relative_to(repo_root).as_posix()
        is_special = any(special in rel for special in special_files)
        errors = check_tool_registration(file_path, is_special_file=is_special)
        if errors:
            print(f"[ERROR] Tool registration issues in {rel}:")
            for error in errors:
                print(f"  {error}")
            all_errors.extend(errors)
    if all_errors:
        print("All Tool subclasses must be registered with register_tool().")
        return 1
    print("All Tool subclasses are properly registered!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
