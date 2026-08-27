#!/usr/bin/env python3
"""Safe Kiln package/checkouts diagnostics.

Examples:
  python check_kiln_environment.py
  python check_kiln_environment.py --json
  python check_kiln_environment.py --repo-root /path/to/Kiln
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


DISTRIBUTIONS = ["kiln-ai", "kiln-server", "kiln-studio-desktop"]
IMPORTS = [
    "kiln_ai",
    "kiln_ai.datamodel",
    "kiln_ai.adapters.adapter_registry",
    "kiln_ai.tools",
    "kiln_server.server",
    "kiln_server.mcp.mcp",
]
CLIS = ["kiln_ai", "kiln_server", "kiln_mcp"]


def dist_versions() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for dist in DISTRIBUTIONS:
        try:
            out.append({"name": dist, "version": version(dist), "status": "ok"})
        except PackageNotFoundError:
            out.append({"name": dist, "version": "", "status": "missing"})
    return out


def import_checks() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for name in IMPORTS:
        try:
            importlib.import_module(name)
            out.append({"module": name, "status": "ok", "error": ""})
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            out.append({"module": name, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return out


def cli_checks(timeout: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for cli in CLIS:
        exe = shutil.which(cli)
        if exe is None:
            out.append({"cli": cli, "status": "missing", "detail": "not on PATH"})
            continue
        try:
            proc = subprocess.run(
                [exe, "--help"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            out.append({"cli": cli, "status": "error", "detail": f"{type(exc).__name__}: {exc}"})
            continue
        first = (proc.stdout or proc.stderr).splitlines()[:2]
        out.append({"cli": cli, "status": "ok" if proc.returncode == 0 else "error", "detail": " | ".join(first)})
    return out


def repo_checks(repo_root: Path | None) -> dict[str, Any] | None:
    if repo_root is None:
        return None
    root = repo_root.resolve()
    checks = {
        "root": str(root),
        "looks_like_kiln_checkout": (root / "checks.sh").is_file() and (root / "pyproject.toml").is_file(),
        "paths": {
            "libs/core": (root / "libs" / "core" / "kiln_ai").is_dir(),
            "libs/server": (root / "libs" / "server" / "kiln_server").is_dir(),
            "app/desktop": (root / "app" / "desktop").is_dir(),
            "app/web_ui": (root / "app" / "web_ui" / "package.json").is_file(),
            "checks.sh": (root / "checks.sh").is_file(),
        },
    }
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe Kiln package and checkout diagnostics.")
    parser.add_argument("--repo-root", type=Path, help="Optional Kiln checkout root for file-layout probes.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--cli-timeout", type=int, default=20, help="Seconds per CLI --help check.")
    args = parser.parse_args()

    result = {
        "python": sys.version.split()[0],
        "distributions": dist_versions(),
        "imports": import_checks(),
        "cli_help": cli_checks(args.cli_timeout),
        "repo": repo_checks(args.repo_root),
    }

    failed = any(item["status"] != "ok" for item in result["imports"])
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        print("Distributions:")
        for item in result["distributions"]:
            print(f"  {item['name']}: {item['status']} {item['version']}")
        print("Imports:")
        for item in result["imports"]:
            detail = f" ({item['error']})" if item["error"] else ""
            print(f"  {item['module']}: {item['status']}{detail}")
        print("CLI help:")
        for item in result["cli_help"]:
            print(f"  {item['cli']}: {item['status']} {item['detail']}")
        if result["repo"] is not None:
            print("Checkout probe:")
            print(f"  root: {result['repo']['root']}")
            print(f"  looks_like_kiln_checkout: {result['repo']['looks_like_kiln_checkout']}")
            for path, ok in result["repo"]["paths"].items():
                print(f"  {path}: {ok}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
