#!/usr/bin/env python3
"""Extract SuperAGI FastAPI route decorators without importing main.py.

Example:
  python inspect_superagi_routes.py --repo-root /path/to/SuperAGI
  python inspect_superagi_routes.py --json | head
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def extract_routes(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [{"file": str(path), "error": str(exc)}]
    routes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in {"get", "post", "put", "delete", "patch"}:
                    route = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else None
                    routes.append(
                        {
                            "file": str(path),
                            "method": dec.func.attr.upper(),
                            "path": route,
                            "function": node.name,
                        }
                    )
    return routes


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect SuperAGI FastAPI routes statically")
    parser.add_argument("--repo-root", default=".", help="Checkout root to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    controllers = sorted((root / "superagi" / "controllers").glob("**/*.py"))
    controllers += [root / "main.py"] if (root / "main.py").exists() else []
    routes = []
    for path in controllers:
        if path.name == "__init__.py":
            continue
        routes.extend(extract_routes(path))
    result = {"repo_root": str(root), "route_count": len([r for r in routes if "method" in r]), "routes": routes}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for item in routes:
            if "error" in item:
                print(f"{item['file']}: ERROR {item['error']}")
            else:
                print(f"{item['method']:>6} {item['path'] or ''}  {item['function']}  [{item['file']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
