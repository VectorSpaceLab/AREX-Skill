#!/usr/bin/env python3
"""Statically inspect neural_style.py argparse defaults without importing TensorFlow."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def literal_or_source(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        if hasattr(ast, "unparse"):
            return ast.unparse(node)  # type: ignore[attr-defined]
        return "<expr>"


def inspect_args(script: Path) -> List[Dict[str, Any]]:
    tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    rows: List[Dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"):
            continue
        names = []
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                names.append(arg.value)
            elif arg.__class__.__name__ == "Str":  # Python 3.7 compatibility without ast.Str warnings.
                names.append(getattr(arg, "s"))
        if not names:
            continue
        row: Dict[str, Any] = {"names": names}
        for kw in node.keywords:
            if kw.arg in {"default", "choices", "nargs", "required", "action", "help"}:
                row[kw.arg] = literal_or_source(kw.value)
            elif kw.arg == "type":
                row["type"] = getattr(kw.value, "id", literal_or_source(kw.value))
        rows.append(row)
    return rows


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect neural_style.py argparse flags without importing runtime dependencies.")
    parser.add_argument("--script", default="neural_style.py", help="Path to neural_style.py. Default: %(default)s")
    parser.add_argument("--format", choices=["json", "table", "names"], default="json")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script = Path(args.script).expanduser()
    if not script.is_file():
        print(f"error: script not found: {script}", file=sys.stderr)
        return 2
    rows = inspect_args(script)
    if args.format == "json":
        print(json.dumps(rows, indent=2, sort_keys=True))
    elif args.format == "names":
        for row in rows:
            print(",".join(row["names"]))
    else:
        for row in rows:
            names = ", ".join(row["names"])
            default = row.get("default", "<none>")
            choices = row.get("choices", "")
            required = row.get("required", False)
            print(f"{names:38} default={default!r:28} required={required!r:5} choices={choices!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
