#!/usr/bin/env python3
"""Inspect an installed EverOS package without starting the server.

Safe by default: imports public modules, checks distribution metadata, locates the
`everos` console script, reads packaged config templates, and builds the FastAPI
OpenAPI schema with `lifespan_providers=[]` so no SQLite/LanceDB/LLM startup runs.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import shutil
import subprocess
import sys
from importlib import resources
from typing import Any


def _ok(value: Any = True, **extra: Any) -> dict[str, Any]:
    out = {"ok": bool(value)}
    out.update(extra)
    return out


def inspect() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "distribution": {},
        "imports": {},
        "cli": {},
        "templates": {},
        "openapi": {},
    }
    try:
        dist_version = metadata.version("everos")
        report["distribution"] = _ok(True, name="everos", version=dist_version)
    except metadata.PackageNotFoundError as exc:
        report["distribution"] = _ok(False, error=str(exc))

    for mod in [
        "everos",
        "everos.entrypoints.cli.main",
        "everos.entrypoints.api.app",
        "everos.config",
        "everos.service.memorize",
        "everos.service.search",
    ]:
        try:
            importlib.import_module(mod)
            report["imports"][mod] = _ok(True)
        except Exception as exc:  # diagnostics should continue
            report["imports"][mod] = _ok(False, error=repr(exc))

    exe = shutil.which("everos")
    report["cli"]["path_found"] = bool(exe)
    if exe:
        try:
            proc = subprocess.run(
                [exe, "--help"], text=True, capture_output=True, timeout=20, check=False
            )
            report["cli"].update(
                exit_code=proc.returncode,
                has_init="init" in proc.stdout,
                has_server="server" in proc.stdout,
                has_cascade="cascade" in proc.stdout,
            )
        except Exception as exc:
            report["cli"]["error"] = repr(exc)

    try:
        cfg = resources.files("everos.config")
        for name in ["default.toml", "default_ome.toml"]:
            text = cfg.joinpath(name).read_text(encoding="utf-8")
            report["templates"][name] = _ok(True, bytes=len(text.encode()))
    except Exception as exc:
        report["templates"]["error"] = repr(exc)

    try:
        os.environ.setdefault("ENV", "DEV")
        from everos.entrypoints.api.app import create_app

        schema = create_app(lifespan_providers=[]).openapi()
        report["openapi"] = _ok(
            True,
            title=schema.get("info", {}).get("title"),
            version=schema.get("info", {}).get("version"),
            path_count=len(schema.get("paths", {})),
            has_health="/health" in schema.get("paths", {}),
            has_memory_add="/api/v2/memory/add" in schema.get("paths", {}),
        )
    except Exception as exc:
        report["openapi"] = _ok(False, error=repr(exc))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args()
    report = inspect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python_version']}")
        dist = report["distribution"]
        print(f"everos distribution: {'OK ' + dist.get('version', '') if dist.get('ok') else 'MISSING'}")
        print(f"everos CLI on PATH: {report['cli'].get('path_found')}")
        print(f"OpenAPI no-lifespan build: {report['openapi'].get('ok')}")
        if report["openapi"].get("ok"):
            print(f"OpenAPI paths: {report['openapi'].get('path_count')}")
    required = [report["distribution"].get("ok"), report["openapi"].get("ok")]
    required.extend(v.get("ok") for v in report["imports"].values())
    return 0 if all(required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
