#!/usr/bin/env python3
"""Read-only MemMachine Python package and entry-point checker.

Run from any environment where MemMachine may be installed. The script imports
public modules, prints distribution versions, inspects key signatures, and checks
whether public console commands are discoverable. It does not contact a server.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable

DISTS = ["memmachine", "memmachine-client", "memmachine-common", "memmachine-server"]
MODULES = ["memmachine_common", "memmachine_client", "memmachine_server"]
COMMANDS = ["mem-cli", "memmachine", "memmachine-server", "memmachine-mcp-http"]


def dist_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def import_status(module: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return False, f"{type(exc).__name__}: {exc}"
    return True, getattr(mod, "__name__", module)


def print_signatures() -> None:
    try:
        from memmachine_client import Config, MemMachineClient, Memory, Project
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        print(f"[signatures] unavailable: {type(exc).__name__}: {exc}")
        return

    targets = [
        ("MemMachineClient", MemMachineClient),
        ("MemMachineClient.create_project", MemMachineClient.create_project),
        ("Project.memory", Project.memory),
        ("Memory.add", Memory.add),
        ("Memory.search", Memory.search),
        ("Memory.list", Memory.list),
        ("Config.get_resources", Config.get_resources),
        ("Config.update_long_term_memory_config", Config.update_long_term_memory_config),
    ]
    for label, obj in targets:
        try:
            sig = inspect.signature(obj)
        except Exception as exc:  # noqa: BLE001
            sig = f"<unavailable: {type(exc).__name__}: {exc}>"
        print(f"[signature] {label}{sig}")


def find_command(command: str) -> str | None:
    """Find a command on PATH or next to the current Python executable."""
    exe = shutil.which(command)
    if exe:
        return exe
    sibling = Path(sys.executable).parent / command
    return str(sibling) if sibling.exists() else None


def run_help(command: str, timeout: float) -> tuple[bool, str]:
    exe = find_command(command)
    if not exe:
        return False, "not-on-PATH-or-python-bin"
    try:
        proc = subprocess.run(
            [exe, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    first = " ".join(proc.stdout.strip().splitlines()[:2])[:240]
    return proc.returncode == 0, f"exit={proc.returncode}; {first}"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check installed MemMachine packages without contacting a server.")
    parser.add_argument("--summary", action="store_true", help="Print distribution/import/command summary.")
    parser.add_argument("--signatures", action="store_true", help="Print key Python SDK signatures.")
    parser.add_argument("--check-help", action="store_true", help="Run --help for console commands found on PATH.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout for each --help command.")
    args = parser.parse_args(argv)

    if not (args.summary or args.signatures or args.check_help):
        args.summary = True
        args.signatures = True

    failures = 0
    if args.summary:
        print(f"[python] {sys.version.split()[0]}")
        for dist in DISTS:
            print(f"[dist] {dist}: {dist_version(dist)}")
        for module in MODULES:
            ok, detail = import_status(module)
            print(f"[import] {module}: {'ok' if ok else 'failed'} ({detail})")
            failures += 0 if ok or module == "memmachine_server" else 1
        for command in COMMANDS:
            print(f"[command] {command}: {find_command(command) or 'not-on-PATH-or-python-bin'}")

    if args.signatures:
        print_signatures()

    if args.check_help:
        for command in COMMANDS:
            ok, detail = run_help(command, args.timeout)
            print(f"[help] {command}: {'ok' if ok else 'failed'} ({detail})")
            # Missing server commands should not fail client-only installations.

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
