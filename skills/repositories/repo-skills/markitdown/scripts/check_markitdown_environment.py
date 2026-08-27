#!/usr/bin/env python3
"""Safe MarkItDown environment checker.

This helper verifies imports, distribution metadata, optional plugin discovery,
and CLI availability without converting user files, calling cloud services,
calling LLM APIs, starting servers, or reading the original repository checkout.

Examples:
  python scripts/check_markitdown_environment.py --check-cli --list-plugins
  python scripts/check_markitdown_environment.py --require markitdown-ocr --list-plugins
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_DISTRIBUTIONS = (
    ("markitdown", "markitdown"),
    ("markitdown-mcp", "markitdown_mcp"),
    ("markitdown-ocr", "markitdown_ocr"),
    ("markitdown-sample-plugin", "markitdown_sample_plugin"),
)


@dataclass
class CheckResult:
    label: str
    ok: bool
    detail: str


def _version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _import_module(module: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostics should preserve exception class
        return False, f"{type(exc).__name__}: {exc}"
    return True, "import ok"


def _entry_points(group: str) -> list[str]:
    try:
        entries = metadata.entry_points(group=group)
    except TypeError:
        entries = metadata.entry_points().get(group, [])
    return [f"{entry.name} = {entry.value}" for entry in entries]


def _resolve_command(command: str) -> str | None:
    path = shutil.which(command)
    if path is not None:
        return path
    sibling = Path(sys.executable).with_name(command)
    if sibling.exists():
        return str(sibling)
    return None


def _run_help(command: str) -> CheckResult:
    path = _resolve_command(command)
    if path is None:
        return CheckResult(command, False, "not found on PATH or beside the active Python executable")
    try:
        proc = subprocess.run(
            [path, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(command, False, f"failed to run --help: {type(exc).__name__}: {exc}")
    if proc.returncode != 0:
        snippet = (proc.stderr or proc.stdout).strip().splitlines()[:3]
        return CheckResult(command, False, f"--help exited {proc.returncode}: {' | '.join(snippet)}")
    first = (proc.stdout or proc.stderr).strip().splitlines()[:1]
    return CheckResult(command, True, first[0] if first else "--help ok")


def _selected_distributions(require: Iterable[str]) -> list[tuple[str, str | None]]:
    by_name = {dist: module for dist, module in DEFAULT_DISTRIBUTIONS}
    selected: list[tuple[str, str | None]] = list(DEFAULT_DISTRIBUTIONS)
    for dist in require:
        if dist not in by_name:
            selected.append((dist, None))
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MarkItDown imports, plugins, and CLI availability safely.")
    parser.add_argument("--require", action="append", default=[], help="Additional distribution name that must be installed.")
    parser.add_argument("--check-cli", action="store_true", help="Run safe --help checks for markitdown and markitdown-mcp when present.")
    parser.add_argument("--list-plugins", action="store_true", help="List installed markitdown.plugin entry points.")
    parser.add_argument("--strict", action="store_true", help="Fail if optional monorepo packages are missing, not just required packages.")
    args = parser.parse_args()

    failures = 0
    required = {"markitdown", *args.require}
    for distribution, module in _selected_distributions(args.require):
        version = _version(distribution)
        is_required = args.strict or distribution in required
        if version is None:
            status = "FAIL" if is_required else "WARN"
            print(f"[{status}] distribution {distribution}: not installed")
            failures += int(is_required)
            continue
        print(f"[OK] distribution {distribution}: {version}")
        if module:
            ok, detail = _import_module(module)
            print(f"[{'OK' if ok else 'FAIL'}] import {module}: {detail}")
            failures += int(not ok)

    if args.list_plugins:
        plugins = _entry_points("markitdown.plugin")
        if plugins:
            print("[OK] markitdown.plugin entry points:")
            for plugin in plugins:
                print(f"  - {plugin}")
        else:
            print("[WARN] no markitdown.plugin entry points installed")

    if args.check_cli:
        for command in ("markitdown", "markitdown-mcp"):
            result = _run_help(command)
            required_cli = command == "markitdown" or args.strict
            print(f"[{'OK' if result.ok else ('FAIL' if required_cli else 'WARN')}] CLI {command}: {result.detail}")
            failures += int((not result.ok) and required_cli)

    if failures:
        print(f"Environment check failed with {failures} required issue(s).")
        return 1
    print("Environment check completed without required failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
