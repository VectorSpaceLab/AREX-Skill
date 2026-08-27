#!/usr/bin/env python3
"""Quick non-mutating Mycodo probe.

Use this helper to check whether a Python process can import Mycodo from an
installed package or explicit checkout root and to print stable routing facts.
It does not contact REST/Pyro services, run hardware, start Docker, or mutate
files.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print a non-mutating Mycodo package/source summary.")
    parser.add_argument("--repo-root", help="Optional Mycodo checkout/install root to add to sys.path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser


def add_repo_root(path: str | None) -> None:
    if path:
        sys.path.insert(0, str(Path(path).expanduser().resolve()))


def collect() -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "mycodo_imported": False,
    }
    try:
        mycodo = importlib.import_module("mycodo")
        config = importlib.import_module("mycodo.config")
        client = importlib.import_module("mycodo.mycodo_client")
        dc = client.DaemonControl
        data.update(
            {
                "mycodo_imported": True,
                "mycodo_file": getattr(mycodo, "__file__", None),
                "version": getattr(config, "MYCODO_VERSION", None),
                "alembic_version": getattr(config, "ALEMBIC_VERSION", None),
                "daemon_control_signature": str(inspect.signature(dc)),
                "selected_methods": {
                    name: str(inspect.signature(getattr(dc, name)))
                    for name in ["output_on", "output_off", "output_on_off", "input_force_measurements", "pid_pause", "pid_resume", "pid_set"]
                    if hasattr(dc, name)
                },
            }
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        data["error"] = f"{type(exc).__name__}: {exc}"
    data["verification_limits"] = [
        "No service, REST/Pyro, Docker, InfluxDB, backup/restore, installer, or hardware operation was performed.",
        "Use sub-skill troubleshooting before mutating a live Mycodo host.",
    ]
    return data


def print_text(data: Dict[str, Any]) -> None:
    print("Mycodo quick probe (non-mutating)")
    print(f"Python: {data['python']} on {data['machine']}")
    if data.get("mycodo_imported"):
        print(f"Mycodo version: {data.get('version')}")
        print(f"Alembic version: {data.get('alembic_version')}")
        print(f"DaemonControl: {data.get('daemon_control_signature')}")
        for name, signature in data.get("selected_methods", {}).items():
            print(f"  {name}{signature}")
    else:
        print(f"Mycodo import unavailable: {data.get('error')}")
    for warning in data["verification_limits"]:
        print(f"WARNING: {warning}")


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    add_repo_root(args.repo_root)
    data = collect()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_text(data)
    return 0 if data.get("mycodo_imported") else 1


if __name__ == "__main__":
    raise SystemExit(main())
