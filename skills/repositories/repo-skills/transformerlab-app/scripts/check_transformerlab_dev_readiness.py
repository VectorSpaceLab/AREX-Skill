#!/usr/bin/env python3
"""Read-only Transformer Lab checkout readiness probe.

This helper is bundled with the repo skill. It accepts a target checkout via
--repo-root and reports expected files, package metadata, tool versions, port
occupancy, and optional HTTP reachability. It does not install packages, start
services, kill processes, log in, run tests, or call cloud providers.

Examples:
  python check_transformerlab_dev_readiness.py --repo-root /path/to/transformerlab-app
  python check_transformerlab_dev_readiness.py --repo-root . --check-url http://localhost:8338/server/health
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REQUIRED_PATHS = [
    "package.json",
    "README.md",
    "api/api.py",
    "api/pyproject.toml",
    "api/transformerlab",
    "cli/pyproject.toml",
    "cli/src/transformerlab_cli/main.py",
    "lab-sdk/pyproject.toml",
    "lab-sdk/src/lab/__init__.py",
    "src/renderer/App.tsx",
    "src/renderer/components/MainAppPanel.tsx",
    "src/renderer/lib/authContext.ts",
    "docs/task-execution/README.md",
]


def run_version(command: list[str], timeout: float = 5.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"command": command, "found": False, "ok": False, "output": "not found"}
    except subprocess.TimeoutExpired:
        return {"command": command, "found": True, "ok": False, "output": "timed out"}
    output = (proc.stdout or proc.stderr or "").strip().splitlines()
    return {
        "command": command,
        "found": True,
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "output": output[:3],
    }


def port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_pyproject_name_version(path: Path) -> dict[str, str | None]:
    result: dict[str, str | None] = {"name": None, "version": None}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return result
    in_project = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "[project]":
            in_project = True
            continue
        if line.startswith("[") and line != "[project]":
            in_project = False
        if not in_project or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if key in result:
            result[key] = value.strip('"')
    return result


def check_url(url: str, timeout: float = 3.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec: user-supplied diagnostic URL
            body = response.read(160).decode("utf-8", errors="replace")
            return {"url": url, "ok": True, "status": response.status, "body_prefix": body}
    except urllib.error.HTTPError as exc:
        return {"url": url, "ok": False, "status": exc.code, "error": str(exc)}
    except Exception as exc:
        return {"url": url, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Transformer Lab checkout readiness probe")
    parser.add_argument("--repo-root", default=".", help="Path to a Transformer Lab application checkout")
    parser.add_argument("--check-url", action="append", default=[], help="Optional local URL to probe with a GET request")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).expanduser().resolve()
    missing = [rel for rel in REQUIRED_PATHS if not (root / rel).exists()]

    package_json = read_json(root / "package.json") or {}
    package_info = {
        "app_version": package_json.get("version"),
        "app_description": package_json.get("description"),
        "node_engine": package_json.get("engines", {}).get("node"),
        "npm_scripts": sorted((package_json.get("scripts") or {}).keys()),
    }

    pyprojects = {
        "api": read_pyproject_name_version(root / "api/pyproject.toml"),
        "cli": read_pyproject_name_version(root / "cli/pyproject.toml"),
        "lab-sdk": read_pyproject_name_version(root / "lab-sdk/pyproject.toml"),
    }

    tools = {
        "node": run_version(["node", "--version"]),
        "npm": run_version(["npm", "--version"]),
        "python3": run_version(["python3", "--version"]),
        "uv": run_version(["uv", "--version"]),
        "git": run_version(["git", "--version"]),
    }

    ports = {"api_8338_open": port_open(8338), "frontend_1212_open": port_open(1212)}
    urls = [check_url(url) for url in args.check_url]

    warnings: list[str] = []
    node_output = tools["node"].get("output") or []
    node_version = node_output[0] if node_output else ""
    if node_version.startswith("v23") or node_version.startswith("v24") or node_version.startswith("v25"):
        warnings.append("Repo guidance supports Node v22; this host appears to use a newer Node version.")
    if missing:
        warnings.append("Missing required repo paths; --repo-root may not point to a Transformer Lab app checkout.")
    if ports["api_8338_open"]:
        warnings.append("Port 8338 is already open; an API server or another process may be running.")
    if ports["frontend_1212_open"]:
        warnings.append("Port 1212 is already open; a frontend dev server or another process may be running.")

    report = {
        "repo_root": str(root),
        "required_paths_missing": missing,
        "package_json": package_info,
        "pyprojects": pyprojects,
        "tools": tools,
        "ports": ports,
        "url_checks": urls,
        "warnings": warnings,
        "ok": not missing,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Transformer Lab readiness probe")
        print(f"repo_root: {root}")
        print(f"required_paths: {'ok' if not missing else 'missing ' + ', '.join(missing)}")
        print(f"app_version: {package_info.get('app_version')}")
        print(f"node_engine_metadata: {package_info.get('node_engine')}")
        print("pyprojects:")
        for name, data in pyprojects.items():
            print(f"  {name}: {data.get('name')} {data.get('version')}")
        print("tools:")
        for name, data in tools.items():
            status = "ok" if data.get("ok") else "missing/fail"
            output = data.get("output")
            if isinstance(output, list):
                output = " | ".join(str(item) for item in output)
            print(f"  {name}: {status} {output}")
        print(f"ports: api_8338_open={ports['api_8338_open']} frontend_1212_open={ports['frontend_1212_open']}")
        for item in urls:
            print(f"url: {item}")
        if warnings:
            print("warnings:")
            for warning in warnings:
                print(f"  - {warning}")

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
