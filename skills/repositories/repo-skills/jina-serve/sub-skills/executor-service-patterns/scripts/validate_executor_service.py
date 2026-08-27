#!/usr/bin/env python3
"""Lightweight static validation for a Jina Executor module or YAML file."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


def check_py(path: Path) -> list[str]:
    warnings: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = {getattr(base, "id", None) or getattr(base, "attr", None) for base in node.bases}
            if "Executor" in bases:
                init = next((item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"), None)
                if init and init.args.kwarg is None:
                    warnings.append(f"{node.name}.__init__ should accept **kwargs")
                decorators = [getattr(dec, "id", None) or getattr(dec, "attr", None) for item in node.body if isinstance(item, ast.FunctionDef) for dec in item.decorator_list]
                if "requests" not in decorators:
                    warnings.append(f"{node.name} has no obvious @requests endpoint")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Executor Python file or YAML file to check.")
    args = parser.parse_args()
    path = Path(args.path)
    result = {"path": str(path), "warnings": []}
    if path.suffix == ".py":
        result["warnings"] = check_py(path)
    elif path.suffix.lower() in {".yml", ".yaml", ".jaml"}:
        text = path.read_text(encoding="utf-8")
        for key in ["jtype", "py_modules", "with", "requests"]:
            if key in text:
                result.setdefault("found_keys", []).append(key)
    else:
        result["warnings"].append("unknown file suffix; expected .py/.yml/.yaml/.jaml")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
