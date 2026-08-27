#!/usr/bin/env python3
"""Summarize Stable Diffusion WebUI CLI flags and API routes without imports."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            cur: ast.AST | None = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            return ".".join(reversed(parts))
        if isinstance(node, ast.Call):
            return ast.unparse(node) if hasattr(ast, "unparse") else "<call>"
        return None


def extract_flags(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    flags: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
            continue
        names = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
        if not names:
            continue
        kwargs = {kw.arg: literal(kw.value) for kw in node.keywords if kw.arg}
        flags.append({"names": names, "help": kwargs.get("help"), "default": kwargs.get("default"), "action": kwargs.get("action"), "choices": kwargs.get("choices")})
    return flags


def extract_routes(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    routes: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_api_route":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        methods: list[str] = []
        response_model = None
        endpoint = ast.unparse(node.args[1]) if len(node.args) > 1 and hasattr(ast, "unparse") else None
        for kw in node.keywords:
            if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                methods = [elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant)]
            elif kw.arg == "response_model":
                response_model = ast.unparse(kw.value) if hasattr(ast, "unparse") else literal(kw.value)
        routes.append({"path": node.args[0].value, "methods": methods, "endpoint": endpoint, "response_model": response_model})
    return routes


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect Stable Diffusion WebUI source files with AST only")
    parser.add_argument("--repo", type=Path, default=Path("."), help="Path to a stable-diffusion-webui checkout")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    args = parser.parse_args()

    repo = args.repo
    cmd_args = repo / "modules" / "cmd_args.py"
    api_file = repo / "modules" / "api" / "api.py"
    result = {
        "repo": str(repo),
        "flags": extract_flags(cmd_args) if cmd_args.exists() else [],
        "routes": extract_routes(api_file) if api_file.exists() else [],
        "missing": [str(path.relative_to(repo) if path.is_relative_to(repo) else path) for path in (cmd_args, api_file) if not path.exists()],
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"# Stable Diffusion WebUI Source Summary\n")
    print(f"- CLI flags parsed: {len(result['flags'])}")
    print(f"- API routes parsed: {len(result['routes'])}")
    if result["missing"]:
        print(f"- Missing files: {', '.join(result['missing'])}")
    print("\n## API Routes\n")
    for route in result["routes"]:
        methods = ", ".join(route["methods"] or ["?"])
        print(f"- `{methods} {route['path']}` -> `{route.get('endpoint')}`")
    print("\n## CLI Flag Sample\n")
    for flag in result["flags"][:40]:
        names = ", ".join(f"`{name}`" for name in flag["names"])
        help_text = flag.get("help") or ""
        print(f"- {names}: {help_text}")
    if len(result["flags"]) > 40:
        print(f"- ... {len(result['flags']) - 40} additional flags omitted; rerun with `--json` for all fields.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
