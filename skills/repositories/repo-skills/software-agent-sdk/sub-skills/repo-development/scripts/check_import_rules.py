#!/usr/bin/env python3
"""Check package import layering for the OpenHands monorepo."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def get_imports_from_file(file_path: Path) -> set[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except Exception:
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _check(paths: list[Path], forbidden: list[str]) -> list[tuple[Path, str]]:
    violations: list[tuple[Path, str]] = []
    for py_file in paths:
        for imp in get_imports_from_file(py_file):
            if any(imp == f or imp.startswith(f + ".") for f in forbidden):
                violations.append((py_file, imp))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    sdk_path = repo_root / "openhands-sdk" / "openhands" / "sdk"
    tools_path = repo_root / "openhands-tools" / "openhands" / "tools"
    agent_server_path = (
        repo_root / "openhands-agent-server" / "openhands" / "agent_server"
    )

    if args.files:
        files = [Path(f).resolve() for f in args.files]
        check_sdk = any(sdk_path in f.parents or f == sdk_path for f in files)
        check_tools = any(tools_path in f.parents or f == tools_path for f in files)
        check_agent_server = any(
            agent_server_path in f.parents or f == agent_server_path for f in files
        )
    else:
        files = []
        check_sdk = check_tools = check_agent_server = True

    exit_code = 0
    if check_sdk and sdk_path.exists():
        for file_path, imp in _check(
            list(sdk_path.rglob("*.py")),
            ["openhands.tools", "openhands.workspace", "openhands.agent_server"],
        ):
            print(f"[ERROR] {file_path.relative_to(repo_root)} imports {imp}")
            exit_code = 1
    if check_tools and tools_path.exists():
        for file_path, imp in _check(
            list(tools_path.rglob("*.py")),
            ["openhands.workspace", "openhands.agent_server"],
        ):
            print(f"[ERROR] {file_path.relative_to(repo_root)} imports {imp}")
            exit_code = 1
    if check_agent_server and agent_server_path.exists():
        for file_path, imp in _check(
            list(agent_server_path.rglob("*.py")), ["openhands.workspace"]
        ):
            print(f"[ERROR] {file_path.relative_to(repo_root)} imports {imp}")
            exit_code = 1
    if exit_code == 0:
        print("All import dependency rules satisfied!")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
