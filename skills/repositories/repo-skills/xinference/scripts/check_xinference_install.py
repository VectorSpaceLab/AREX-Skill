#!/usr/bin/env python3
"""Check a Xinference installation without starting services or downloading models.

Examples:
  python scripts/check_xinference_install.py
  python scripts/check_xinference_install.py --run-cli-help --json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any

ENTRY_POINTS = [
    "xinference",
    "xinference-local",
    "xinference-supervisor",
    "xinference-worker",
    "xinference-migrate-auth",
    "xinference-reset-auth-password",
]


def _result(status: str, detail: str, **extra: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"status": status, "detail": detail}
    data.update(extra)
    return data


def check_imports() -> dict[str, Any]:
    try:
        import xinference  # type: ignore
        from xinference.client import (  # type: ignore
            AsyncClient,
            AsyncRESTfulClient,
            Client,
            RESTfulClient,
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        return _result("fail", f"import failed: {type(exc).__name__}: {exc}")

    try:
        version = metadata.version("xinference")
    except metadata.PackageNotFoundError:
        version = getattr(xinference, "__version__", "unknown")

    aliases = {
        "RESTfulClient_is_Client": RESTfulClient is Client,
        "AsyncRESTfulClient_is_AsyncClient": AsyncRESTfulClient is AsyncClient,
    }
    ok = all(aliases.values())
    return _result(
        "pass" if ok else "warn",
        "xinference imports and client aliases resolved",
        version=version,
        aliases=aliases,
    )


def check_entry_points(run_help: bool) -> dict[str, Any]:
    commands: dict[str, Any] = {}
    for name in ENTRY_POINTS:
        path = shutil.which(name)
        if path is None:
            commands[name] = {"status": "missing", "detail": "not found on PATH"}
            continue
        commands[name] = {"status": "found"}
        if run_help:
            proc = subprocess.run(
                [name, "--help"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
            commands[name].update(
                {
                    "help_exit_code": proc.returncode,
                    "help_first_line": (proc.stdout or proc.stderr).splitlines()[:1],
                }
            )
    status = "pass" if all(v["status"] == "found" for v in commands.values()) else "warn"
    return _result(status, "console entry point availability checked", commands=commands)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Xinference importability and console entry points safely."
    )
    parser.add_argument(
        "--run-cli-help",
        action="store_true",
        help="Also run each console command with --help. This does not start services.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    results = {"imports": check_imports(), "entry_points": check_entry_points(args.run_cli_help)}
    failed = any(section["status"] == "fail" for section in results.values())

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for section, data in results.items():
            print(f"[{data['status'].upper()}] {section}: {data['detail']}")
            for key, value in data.items():
                if key not in {"status", "detail"}:
                    print(f"  {key}: {value}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
