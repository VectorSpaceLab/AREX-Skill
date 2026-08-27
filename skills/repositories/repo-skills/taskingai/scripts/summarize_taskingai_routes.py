#!/usr/bin/env python3
"""Statically summarize TaskingAI FastAPI route decorators.

This helper reads Python source files from a user-supplied TaskingAI checkout. It
never imports TaskingAI modules, starts services, opens network connections, or
reads credentials.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

SERVICE_ROUTE_DIRS = {
    "backend": Path("backend/app/routes"),
    "inference": Path("inference/app/routes"),
    "plugin": Path("plugin/app/routes"),
}


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _keyword(call: ast.Call, name: str) -> Any:
    for kw in call.keywords:
        if kw.arg == name:
            return _literal(kw.value)
    return None


def _decorator_path(call: ast.Call) -> str:
    if call.args:
        value = _literal(call.args[0])
        if isinstance(value, str):
            return value
    value = _keyword(call, "path")
    return value if isinstance(value, str) else ""


def _service_mount_guess(service: str, file: Path) -> str:
    text = file.as_posix()
    if service == "backend":
        return "/v1 or /api/v1"
    if service == "inference":
        return "/images" if "/images/" in text else "/v1"
    if service == "plugin":
        return "/images" if text.endswith("/image.py") else "/v1"
    return ""


def iter_routes(repo_root: Path, service: str) -> Iterable[Dict[str, Any]]:
    route_dir = repo_root / SERVICE_ROUTE_DIRS[service]
    if not route_dir.is_dir():
        return []
    rows: List[Dict[str, Any]] = []
    for file in sorted(route_dir.rglob("*.py")):
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            rows.append({"service": service, "file": file.relative_to(repo_root).as_posix(), "method": "PARSE_ERROR", "path": str(exc), "summary": "", "handler": ""})
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                    continue
                method = dec.func.attr.upper()
                if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    continue
                path = _decorator_path(dec)
                rows.append(
                    {
                        "service": service,
                        "file": file.relative_to(repo_root).as_posix(),
                        "method": method,
                        "path": path,
                        "mount": _service_mount_guess(service, file),
                        "summary": _keyword(dec, "summary") or "",
                        "tags": _keyword(dec, "tags") or [],
                        "handler": node.name,
                    }
                )
    rows.sort(key=lambda r: (r["service"], r["file"], r["path"], r["method"], r["handler"]))
    return rows


def inspect_routes(repo_root: Path, services: Sequence[str]) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    routes: List[Dict[str, Any]] = []
    for service in services:
        routes.extend(iter_routes(repo_root, service))
    by_service = {service: sum(1 for route in routes if route["service"] == service) for service in services}
    return {"summary": {"route_count": len(routes), "by_service": by_service}, "routes": routes}


def print_human(report: Dict[str, Any]) -> None:
    print("TaskingAI static route summary")
    print("No TaskingAI modules imported; no services started.")
    print(f"Total route decorators: {report['summary']['route_count']}")
    for service, count in report["summary"]["by_service"].items():
        print(f"  - {service}: {count}")
    print()
    for route in report["routes"]:
        path = route["path"] or "<decorator path omitted or keyword-derived>"
        tags = ",".join(route["tags"]) if isinstance(route["tags"], list) else route["tags"]
        print(f"{route['service']:9} {route['method']:6} {route['mount']} {path:45} {route['summary']} [{tags}] {route['file']}::{route['handler']}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize TaskingAI FastAPI route decorators statically")
    parser.add_argument("--repo-root", required=True, help="Path to a TaskingAI repository root")
    parser.add_argument("--service", action="append", choices=sorted(SERVICE_ROUTE_DIRS), help="Service to inspect; repeat for multiple. Defaults to all.")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)
    services = args.service or sorted(SERVICE_ROUTE_DIRS)
    try:
        report = inspect_routes(Path(args.repo_root), services)
    except Exception as exc:
        print(f"summarize_taskingai_routes.py: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
