#!/usr/bin/env python3
"""Safe ContextForge import, metadata, and CLI discovery probe.

This helper does not start a server, contact a network endpoint, or print secret
values. Run it in the Python environment where ContextForge is installed.

Examples:
  python contextforge_quick_probe.py
  python contextforge_quick_probe.py --json
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, entry_points, version

COMMANDS = ["mcpgateway", "mcpgateway-server", "cforge", "init-secrets"]
MODULES = [
    "mcpgateway",
    "mcpgateway.schemas",
    "mcpgateway.config",
    "mcpgateway.transports.streamablehttp_transport",
    "mcpgateway.services.gateway_service",
]


def command_help(cmd: str, timeout: float) -> dict[str, object]:
    path = shutil.which(cmd)
    if not path:
        return {"command": cmd, "found": False, "status": "missing"}
    try:
        proc = subprocess.run([cmd, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        first = (proc.stdout or proc.stderr).splitlines()[:3]
        return {"command": cmd, "found": True, "returncode": proc.returncode, "first_lines": first}
    except subprocess.TimeoutExpired:
        return {"command": cmd, "found": True, "status": "timeout", "note": "entry point may start a server or wait for runtime setup"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ContextForge package metadata, imports, and CLI entry points safely.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--cli-timeout", type=float, default=5.0, help="Seconds to allow each command --help probe.")
    args = parser.parse_args()

    result: dict[str, object] = {"python": sys.version.split()[0]}
    try:
        result["distribution_version"] = version("mcp-contextforge-gateway")
    except PackageNotFoundError:
        result["distribution_version"] = None
        result.setdefault("warnings", []).append("mcp-contextforge-gateway distribution not found")  # type: ignore[union-attr]

    imports: dict[str, str] = {}
    for module in MODULES:
        try:
            imported = importlib.import_module(module)
            imports[module] = "ok"
            if module == "mcpgateway":
                result["package_version"] = getattr(imported, "__version__", None)
        except Exception as exc:  # pragma: no cover - depends on target env
            imports[module] = f"failed: {type(exc).__name__}: {exc}"
    result["imports"] = imports

    eps = []
    for ep in entry_points(group="console_scripts"):
        if ep.name in COMMANDS:
            eps.append({"name": ep.name, "value": ep.value})
    result["console_scripts"] = eps
    result["cli_help"] = [command_help(cmd, args.cli_timeout) for cmd in COMMANDS]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        print(f"Distribution version: {result.get('distribution_version')}")
        print(f"Package version: {result.get('package_version')}")
        print("Imports:")
        for module, status in imports.items():
            print(f"  {module}: {status}")
        print("Console scripts:")
        for ep in eps:
            print(f"  {ep['name']} -> {ep['value']}")
        print("CLI help probes:")
        for item in result["cli_help"]:  # type: ignore[index]
            print(f"  {item}")
    failed = [module for module, status in imports.items() if status != "ok"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
