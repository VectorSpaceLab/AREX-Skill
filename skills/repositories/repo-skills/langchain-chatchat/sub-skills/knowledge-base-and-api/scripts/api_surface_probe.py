#!/usr/bin/env python3
"""List Langchain-Chatchat FastAPI routes without starting a service.

The server route modules read knowledge-base metadata while importing. This
probe sets up a temporary or user-supplied CHATCHAT_ROOT, creates required local
directories/tables, imports the FastAPI app, and prints route metadata. It does
not bind a port, call model providers, rebuild vectors, or upload documents.

Examples:
  python api_surface_probe.py --json
  python api_surface_probe.py --chatchat-root /path/to/initialized/root --json
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def collect_routes(root: Path):
    os.environ["CHATCHAT_ROOT"] = str(root)
    root.mkdir(parents=True, exist_ok=True)

    from chatchat.settings import Settings

    Settings.basic_settings.make_dirs()
    from chatchat.server.knowledge_base.migrate import create_tables

    create_tables()
    from chatchat.server.api_server.server_app import create_app

    app = create_app()
    routes = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = sorted(getattr(route, "methods", []) or [])
        name = getattr(route, "name", None)
        if path and methods:
            routes.append({"path": path, "methods": methods, "name": name})
    return sorted(routes, key=lambda r: (r["path"], r["methods"], r.get("name") or ""))


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Langchain-Chatchat API routes without starting a server.")
    parser.add_argument("--chatchat-root", help="Existing or disposable CHATCHAT_ROOT to use for route import.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    if args.chatchat_root:
        root = Path(args.chatchat_root).expanduser().resolve()
        temp_dir = None
    else:
        temp_dir = tempfile.TemporaryDirectory(prefix="chatchat-route-probe-")
        root = Path(temp_dir.name)

    try:
        routes = collect_routes(root)
        groups = {}
        for route in routes:
            group = route["path"].strip("/").split("/", 1)[0] or "/"
            groups[group] = groups.get(group, 0) + 1
        report = {
            "ok": True,
            "route_count": len(routes),
            "groups": groups,
            "routes": routes,
            "used_temp_root": temp_dir is not None,
            "notes": [
                "This probe imports route definitions and creates local metadata tables only.",
                "It does not verify a running API process or external model providers."
            ],
        }
    except Exception as exc:
        report = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if report.get("ok"):
            print(f"Discovered {report['route_count']} routes")
            for group, count in sorted(report["groups"].items()):
                print(f"{group}: {count}")
        else:
            print(f"Route probe failed: {report['error']}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
