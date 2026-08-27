#!/usr/bin/env python3
"""Inspect BiSheng workflow node type registration without importing app code."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def node_types(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "NodeType":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        out[target.id] = str(stmt.value.value)
    return out


def class_map_keys(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    keys: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "NODE_CLASS_MAP" and isinstance(node.value, ast.Dict):
                    for key in node.value.keys:
                        if isinstance(key, ast.Attribute):
                            keys.append(ast.unparse(key) if hasattr(ast, "unparse") else key.attr)
                        elif isinstance(key, ast.Constant):
                            keys.append(str(key.value))
                        else:
                            keys.append(ast.unparse(key) if hasattr(ast, "unparse") else "<expr>")
    return sorted(keys)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect workflow node enum and factory registration.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    enum_path = repo / "src/backend/bisheng/workflow/common/node.py"
    map_path = repo / "src/backend/bisheng/workflow/nodes/node_manage.py"
    result: dict[str, Any] = {
        "enum_path_exists": enum_path.exists(),
        "map_path_exists": map_path.exists(),
        "node_types": node_types(enum_path) if enum_path.exists() else {},
        "node_class_map_keys": class_map_keys(map_path) if map_path.exists() else [],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("BiSheng workflow node registration")
        print("==================================")
        for key, value in result["node_types"].items():
            print(f"{key:24} {value}")
        print("\nclass map keys:")
        for key in result["node_class_map_keys"]:
            print(f"  - {key}")
    return 0 if result["enum_path_exists"] and result["map_path_exists"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
