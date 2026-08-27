#!/usr/bin/env python3
"""Check that the public Graphify package is usable in the current Python.

The PyPI distribution is ``graphifyy`` and the import package is ``graphify``.
This helper performs only local package/import/CLI-help checks. It does not read
a project repository, create ``graphify-out/``, contact provider APIs, use
credentials, or require the original Graphify source checkout.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _run_help(argv: list[str], timeout: float) -> tuple[bool, str]:
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return False, "command not found"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout:g}s"
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        return False, output[-1000:] or f"exit code {proc.returncode}"
    first = output.splitlines()[0] if output else "help command exited 0"
    return True, first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Graphify package/import/CLI availability.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Seconds for each CLI help check.")
    args = parser.parse_args(argv)

    checks: list[Check] = []
    version: str | None = None

    try:
        version = metadata.version("graphifyy")
        checks.append(Check("distribution graphifyy", True, f"version {version}"))
    except metadata.PackageNotFoundError:
        checks.append(Check("distribution graphifyy", False, "not installed in this Python"))

    try:
        graphify = importlib.import_module("graphify")
        checks.append(Check("import graphify", True, "import succeeded"))
        for module_name in ("graphify.cli", "graphify.detect", "graphify.extract", "graphify.build", "graphify.export", "graphify.serve"):
            try:
                importlib.import_module(module_name)
                checks.append(Check(f"import {module_name}", True, "import succeeded"))
            except Exception as exc:  # noqa: BLE001 - diagnostic boundary
                checks.append(Check(f"import {module_name}", False, f"{type(exc).__name__}: {exc}"))
        package_version = getattr(graphify, "__version__", None)
        if package_version:
            checks.append(Check("graphify.__version__", True, str(package_version)))
    except Exception as exc:  # noqa: BLE001 - diagnostic boundary
        checks.append(Check("import graphify", False, f"{type(exc).__name__}: {exc}"))

    module_ok, module_detail = _run_help([sys.executable, "-m", "graphify", "--help"], args.timeout)
    checks.append(Check("python -m graphify --help", module_ok, module_detail))

    console = shutil.which("graphify")
    if console:
        console_ok, console_detail = _run_help([console, "--help"], args.timeout)
        checks.append(Check("graphify --help", console_ok, console_detail))
    else:
        checks.append(Check("graphify --help", False, "console script not found on PATH; try python -m graphify"))

    mcp_console = shutil.which("graphify-mcp")
    if mcp_console:
        mcp_ok, mcp_detail = _run_help([mcp_console, "--help"], args.timeout)
        checks.append(Check("graphify-mcp --help", mcp_ok, mcp_detail))
    else:
        checks.append(Check("graphify-mcp --help", False, "console script not found on PATH; install/use MCP extra when needed"))

    required = {"distribution graphifyy", "import graphify", "python -m graphify --help"}
    ok = all(check.ok for check in checks if check.name in required)
    payload: dict[str, Any] = {
        "ok": ok,
        "distribution": "graphifyy",
        "import_package": "graphify",
        "version": version,
        "python": sys.version.split()[0],
        "checks": [asdict(check) for check in checks],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Graphify install check: {'PASS' if ok else 'FAIL'}")
        if version:
            print(f"graphifyy version: {version}")
        for check in checks:
            marker = "PASS" if check.ok else "WARN" if check.name in {"graphify --help", "graphify-mcp --help"} else "FAIL"
            print(f"[{marker}] {check.name}: {check.detail}")
        if not ok:
            print("Install the public package in the selected Python, for example: python -m pip install graphifyy", file=sys.stderr)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
