#!/usr/bin/env python3
"""Read-only MCP entry-point smoke checks for MemMachine."""

from __future__ import annotations

import argparse
import importlib
import inspect
import shutil
import subprocess
from typing import Iterable

COMMANDS = ["memmachine-mcp-stdio", "memmachine-mcp-http", "memmachine-server"]


def check_imports() -> int:
    failures = 0
    for module_name in [
        "memmachine_server.server.mcp_stdio",
        "memmachine_server.server.mcp_http",
        "memmachine_server.server.api_v2.mcp",
    ]:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            print(f"[import] {module_name}: failed ({type(exc).__name__}: {exc})")
            failures += 1
        else:
            print(f"[import] {module_name}: ok")
            if module_name.endswith("api_v2.mcp") and hasattr(module, "Params"):
                print("[params]", sorted(module.Params.model_fields))
            for name in ("main", "run_mcp_http", "run_mcp_stdio", "mcp_add_memory", "mcp_search_memory"):
                if hasattr(module, name):
                    try:
                        print(f"[signature] {module_name}.{name}{inspect.signature(getattr(module, name))}")
                    except Exception:
                        pass
    return failures


def check_help(timeout: float) -> int:
    failures = 0
    for command in COMMANDS:
        exe = shutil.which(command)
        if not exe:
            print(f"[command] {command}: not found")
            continue
        proc = subprocess.run([exe, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        print(f"[help] {command}: exit={proc.returncode}; {' '.join(proc.stdout.splitlines()[:2])}")
        failures += 0 if proc.returncode == 0 else 1
    return failures


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect MemMachine MCP modules and --help without launching long-running servers.")
    parser.add_argument("--check-imports", action="store_true")
    parser.add_argument("--check-help", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args(argv)
    if not args.check_imports and not args.check_help:
        args.check_imports = True
    failures = 0
    if args.check_imports:
        failures += check_imports()
    if args.check_help:
        failures += check_help(args.timeout)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
