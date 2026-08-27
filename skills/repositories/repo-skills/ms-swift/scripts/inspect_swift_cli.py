#!/usr/bin/env python3
"""Inspect ms-swift CLI routes and optionally run safe --help checks."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
from typing import Any

DEFAULT_ROUTES = ["pt", "sft", "infer", "deploy", "export", "eval", "rlhf", "sample", "app", "web-ui"]


def load_route_mapping() -> dict[str, str]:
    try:
        module = importlib.import_module("swift.cli.main")
        return dict(getattr(module, "ROUTE_MAPPING"))
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def help_check(route: str, timeout: int) -> dict[str, Any]:
    swift = shutil.which("swift")
    if swift is None:
        return {"route": route, "ok": False, "error": "swift command not found"}
    try:
        proc = subprocess.run(
            [swift, route, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        return {"route": route, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "route": route,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_first_lines": proc.stdout.splitlines()[:8],
        "stderr_first_lines": proc.stderr.splitlines()[:8],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--help-check", action="store_true", help="Run `swift <route> --help` for selected routes.")
    parser.add_argument("--route", action="append", default=[], help="Route to check; defaults to common routes.")
    parser.add_argument("--timeout", type=int, default=30, help="Seconds per help command.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args()

    routes = args.route or DEFAULT_ROUTES
    result: dict[str, Any] = {"route_mapping": load_route_mapping(), "help": []}
    if args.help_check:
        result["help"] = [help_check(route, args.timeout) for route in routes]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Route mapping:")
        for name, module in sorted(result["route_mapping"].items()):
            print(f"  {name}: {module}")
        for item in result["help"]:
            status = "ok" if item["ok"] else item.get("error", f"exit {item.get('returncode')}")
            print(f"swift {item['route']} --help: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
