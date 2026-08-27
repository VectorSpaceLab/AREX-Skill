#!/usr/bin/env python3
"""Safe Bindu installation surface check.

This helper performs local import, metadata, and CLI-surface checks. It does not
start servers, contact networks, print secrets, or require a Bindu checkout.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, entry_points, metadata, version
from typing import Any

MODULES = [
    "bindu",
    "bindu.penguin.bindufy",
    "bindu.server.applications",
    "bindu.server.task_manager",
    "bindu.grpc.client",
    "bindu.runtime.config",
]
OBJECTS = [
    ("bindu.penguin.bindufy", "bindufy"),
    ("bindu.penguin.manifest", "create_manifest"),
    ("bindu.server.applications", "BinduApplication"),
    ("bindu.grpc.client", "GrpcAgentClient"),
    ("bindu.runtime.config", "RuntimeConfig"),
]


def check() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": True, "python": sys.version.split()[0]}
    try:
        result["version"] = version("bindu")
        result["summary"] = metadata("bindu").get("Summary")
    except PackageNotFoundError as exc:
        result["ok"] = False
        result["metadata_error"] = str(exc)

    imports: dict[str, str] = {}
    for mod_name in MODULES:
        try:
            importlib.import_module(mod_name)
            imports[mod_name] = "ok"
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            result["ok"] = False
            imports[mod_name] = f"ERROR {type(exc).__name__}: {exc}"
    result["imports"] = imports

    signatures: dict[str, str] = {}
    for mod_name, attr in OBJECTS:
        try:
            obj = getattr(importlib.import_module(mod_name), attr)
            signatures[f"{mod_name}.{attr}"] = str(inspect.signature(obj))
        except Exception as exc:  # noqa: BLE001
            result["ok"] = False
            signatures[f"{mod_name}.{attr}"] = f"ERROR {type(exc).__name__}: {exc}"
    result["signatures"] = signatures

    console = [f"{ep.name}={ep.value}" for ep in entry_points(group="console_scripts") if ep.name == "bindu"]
    result["console_scripts"] = console
    result["bindu_executable_on_path"] = bool(shutil.which("bindu"))

    if shutil.which("bindu"):
        try:
            proc = subprocess.run(["bindu", "--help"], text=True, capture_output=True, timeout=10, check=False)
            result["bindu_help_exit_code"] = proc.returncode
            result["bindu_help_first_line"] = (proc.stdout or proc.stderr).splitlines()[:1]
            if proc.returncode != 0:
                result["ok"] = False
        except Exception as exc:  # noqa: BLE001
            result["ok"] = False
            result["bindu_help_error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()
    data = check()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Bindu install ok: {data['ok']}")
        print(f"Python: {data['python']}")
        print(f"Version: {data.get('version', '<missing>')}")
        print(f"Console script: {', '.join(data.get('console_scripts') or []) or '<missing>'}")
        for mod, status in data["imports"].items():
            print(f"{mod}: {status}")
    return 0 if data["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
