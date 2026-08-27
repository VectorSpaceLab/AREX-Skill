#!/usr/bin/env python3
"""Safe LaVague environment probe.

Checks imports, console entry-point availability, optional dependency hints, and
credential variable presence without launching browsers, contacting providers,
starting servers, or reading any original source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Check:
    name: str
    module: str | None = None
    command: str | None = None
    env_vars: tuple[str, ...] = ()


CHECKS = {
    "core": [Check("lavague.core", "lavague.core")],
    "drivers": [
        Check("selenium driver", "lavague.drivers.selenium"),
        Check("playwright driver", "lavague.drivers.playwright"),
    ],
    "contexts": [
        Check("openai context", "lavague.contexts.openai", env_vars=("OPENAI_API_KEY",)),
        Check("anthropic context", "lavague.contexts.anthropic", env_vars=("ANTHROPIC_API_KEY", "OPENAI_API_KEY")),
        Check("gemini context", "lavague.contexts.gemini", env_vars=("GOOGLE_API_KEY", "GEMINI_API_KEY")),
        Check("fireworks context", "lavague.contexts.fireworks", env_vars=("FIREWORKS_API_KEY", "OPENAI_API_KEY")),
        Check("cache context", "lavague.contexts.cache"),
        Check("cohere retriever", "lavague.retrievers.cohere", env_vars=("COHERE_API_KEY",)),
    ],
    "ui": [Check("gradio package", "lavague.gradio"), Check("server package", "lavague.server"), Check("lavague-serve cli", command="lavague-serve")],
    "qa": [Check("qa package", "lavague.qa"), Check("tests package", "lavague.tests"), Check("lavague-qa cli", command="lavague-qa"), Check("lavague-test cli", command="lavague-test")],
}


def import_check(module: str) -> tuple[bool, str]:
    try:
        imported = importlib.import_module(module)
        return True, f"ok ({getattr(imported, '__name__', module)})"
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"FAILED {type(exc).__name__}: {exc}"


def command_help(command: str) -> tuple[bool, str]:
    exe = shutil.which(command)
    if not exe:
        return False, "not found on PATH"
    try:
        proc = subprocess.run([exe, "--help"], text=True, capture_output=True, timeout=20)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"FAILED to run --help: {type(exc).__name__}: {exc}"
    first = (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else "no output"
    return proc.returncode == 0, f"exit={proc.returncode}; {first}"


def env_summary(names: tuple[str, ...]) -> str:
    if not names:
        return ""
    parts = [f"{name}={'set' if os.environ.get(name) else 'missing'}" for name in names]
    return "; env " + ", ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely check LaVague package imports and CLI availability.")
    parser.add_argument("--check", choices=["all", *CHECKS.keys()], default="all", help="Check group to run.")
    parser.add_argument("--quiet", action="store_true", help="Print only failures and final status.")
    parser.add_argument("--disable-telemetry", action="store_true", help="Set LAVAGUE_TELEMETRY=NONE before imports.")
    args = parser.parse_args()

    if args.disable_telemetry:
        os.environ["LAVAGUE_TELEMETRY"] = "NONE"

    groups = CHECKS.keys() if args.check == "all" else [args.check]
    failures = 0
    for group in groups:
        if not args.quiet:
            print(f"[{group}]")
        for item in CHECKS[group]:
            if item.module:
                ok, msg = import_check(item.module)
            elif item.command:
                ok, msg = command_help(item.command)
            else:
                ok, msg = False, "invalid check"
            if not ok:
                failures += 1
            line = f"- {item.name}: {msg}{env_summary(item.env_vars)}"
            if not args.quiet or not ok:
                print(line)
    print("status:", "ok" if failures == 0 else f"{failures} failure(s)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
