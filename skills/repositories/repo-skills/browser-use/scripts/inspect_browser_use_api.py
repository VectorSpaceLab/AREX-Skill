#!/usr/bin/env python3
"""Inspect a Browser Use installation without requiring the source checkout.

Example:
    python inspect_browser_use_api.py --check-cli
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import shutil
import subprocess
import sys
from typing import Any


def describe(name: str, obj: Any) -> None:
    print(f"\n## {name}")
    try:
        print(inspect.signature(obj))
    except Exception as exc:
        print(f"signature unavailable: {type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Browser Use imports, signatures, and CLI availability.")
    parser.add_argument("--check-cli", action="store_true", help="Also run browser-use --help without launching a browser.")
    args = parser.parse_args()

    try:
        version = metadata.version("browser-use")
    except metadata.PackageNotFoundError:
        print("browser-use distribution metadata not found", file=sys.stderr)
        return 2

    print(f"browser-use distribution: {version}")

    try:
        from browser_use import ActionResult, Agent, Browser, BrowserProfile, ChatBrowserUse, Tools
    except Exception as exc:
        print(f"failed to import public Browser Use API: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    for name, obj in {
        "Agent": Agent,
        "Browser": Browser,
        "BrowserProfile": BrowserProfile,
        "Tools": Tools,
        "ActionResult": ActionResult,
        "ChatBrowserUse": ChatBrowserUse,
    }.items():
        describe(name, obj)

    try:
        from browser_use import sandbox
        describe("sandbox", sandbox)
    except Exception as exc:
        print(f"sandbox import warning: {type(exc).__name__}: {exc}")

    try:
        from browser_use.beta import Agent as BetaAgent
        describe("browser_use.beta.Agent", BetaAgent)
    except Exception as exc:
        print(f"beta import warning: {type(exc).__name__}: {exc}")

    if args.check_cli:
        exe = shutil.which("browser-use") or shutil.which("bu")
        if exe is None:
            print("browser-use CLI not found on PATH", file=sys.stderr)
            return 4
        proc = subprocess.run([exe, "--help"], text=True, capture_output=True, timeout=30, check=False)
        print(proc.stdout.splitlines()[0] if proc.stdout else "CLI produced no stdout")
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return proc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
