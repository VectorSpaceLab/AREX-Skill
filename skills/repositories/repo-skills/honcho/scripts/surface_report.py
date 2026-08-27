#!/usr/bin/env python3
"""Summarize the Honcho runtime surface.

This helper is read-only. It prints a compact view of the API route families,
selected SDK method signatures, and the installed CLI help if available.

Run it from a Honcho checkout or any environment that can import the project
package and the `honcho` SDK.
"""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "src").exists():
            return candidate
    return start


def _ensure_repo_on_path() -> Path:
    root = _find_repo_root(Path(__file__).resolve())
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def _route_summary() -> list[dict[str, Any]]:
    try:
        from src.main import app
    except Exception as exc:  # pragma: no cover - inspection helper
        return [{"error": f"could not import src.main: {exc}"}]

    grouped: dict[str, list[str]] = defaultdict(list)
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not methods:
            continue
        if path in {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}:
            continue
        family = path.split("/")[2] if path.startswith("/v3/") else path.strip("/")
        grouped[family].append(f"{','.join(sorted(methods))} {path}")

    return [
        {"family": family, "routes": sorted(routes)}
        for family, routes in sorted(grouped.items())
    ]


def _sdk_summary() -> dict[str, Any]:
    try:
        from honcho import Honcho, Peer, Session
    except Exception as exc:  # pragma: no cover - inspection helper
        return {"error": f"could not import honcho SDK: {exc}"}

    def sig_map(obj: Any, names: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for name in names:
            if hasattr(obj, name):
                result[name] = str(inspect.signature(getattr(obj, name)))
        return result

    return {
        "Honcho": sig_map(Honcho, ["peer", "session", "search", "queue_status"]),
        "Peer": sig_map(
            Peer,
            ["chat", "context", "representation", "card", "search", "message"],
        ),
        "Session": sig_map(
            Session,
            [
                "add_messages",
                "add_peers",
                "context",
                "search",
                "messages",
                "peers",
                "representation",
                "summaries",
                "clone",
                "delete",
            ],
        ),
    }


def _cli_executable() -> str | None:
    cmd = shutil.which("honcho")
    if cmd:
        return cmd
    sibling = Path(sys.executable).with_name("honcho")
    if sibling.exists():
        return str(sibling)
    return None


def _cli_help() -> dict[str, Any]:
    cmd = _cli_executable()
    if not cmd:
        return {
            "available": False,
            "reason": "honcho executable not found on PATH or beside sys.executable",
        }

    try:
        result = subprocess.run(
            [cmd, "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # pragma: no cover - inspection helper
        return {"available": True, "error": str(exc)}

    lines = [line.rstrip() for line in result.stdout.splitlines() if line.strip()]
    return {
        "available": True,
        "first_lines": lines[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    project_root = _ensure_repo_on_path()
    report = {
        "routes": _route_summary(),
        "sdk": _sdk_summary(),
        "cli": _cli_help(),
        "python": sys.version.split()[0],
        "project_root": str(project_root),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Honcho surface report")
        print(f"Python: {report['python']}")
        print("\nRoute families:")
        for family in report["routes"]:
            if "error" in family:
                print(f"- {family['error']}")
                continue
            print(f"- {family['family']}: {len(family['routes'])} routes")
        print("\nSDK signatures:")
        sdk = report["sdk"]
        for label, mapping in sdk.items():
            print(f"- {label}: {', '.join(sorted(mapping)) if isinstance(mapping, dict) else mapping}")
        print("\nCLI help available:", report["cli"].get("available"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
