#!/usr/bin/env python3
"""Statically inspect built-in SuperAGI tools and toolkits.

This helper avoids marketplace downloads and does not import the package.

Example:
  python inspect_builtin_toolkits.py --repo-root /path/to/SuperAGI
  python inspect_builtin_toolkits.py --json | jq '.toolkits[:3]'
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


def inspect_file(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [{"file": str(path), "error": str(exc)}]
    rows = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            attrs = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and isinstance(item.value, ast.Constant):
                    attrs[item.target.id] = item.value.value
                elif isinstance(item, ast.Assign) and isinstance(item.value, ast.Constant):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attrs[target.id] = item.value.value
            if attrs.get("name") or node.name.endswith(("Tool", "Toolkit", "ToolKit")):
                rows.append(
                    {
                        "file": str(path),
                        "class": node.name,
                        "name": attrs.get("name"),
                        "description": attrs.get("description"),
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect built-in SuperAGI tool and toolkit classes")
    parser.add_argument("--repo-root", default=".", help="Checkout root to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    rows = []
    for path in sorted((root / "superagi" / "tools").glob("**/*.py")):
        if path.name == "__init__.py" or "prompts" in path.parts:
            continue
        rows.extend(inspect_file(path))
    toolkits = [row for row in rows if "Toolkit" in row.get("class", "")]
    tools = [row for row in rows if row not in toolkits]
    result = {"repo_root": str(root), "toolkit_count": len(toolkits), "tool_count": len(tools), "toolkits": toolkits, "tools": tools}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Toolkit count: {result['toolkit_count']}")
        print(f"Tool count: {result['tool_count']}")
        for row in toolkits[:20]:
            print(f"[toolkit] {row.get('name') or row['class']} <- {row['file']}")
        if len(toolkits) > 20:
            print(f"... {len(toolkits)-20} more toolkits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
