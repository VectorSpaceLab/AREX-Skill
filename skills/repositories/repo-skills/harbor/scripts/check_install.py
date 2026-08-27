#!/usr/bin/env python3
"""Run a safe Harbor installation diagnostic.

This helper only reads package metadata, imports installed modules, and asks
Harbor for version/help output. It does not access a checkout, start Docker,
contact a model/provider, use credentials, or mutate files.

Usage:
    python path/to/check_install.py
"""

from __future__ import annotations

import importlib
import importlib.metadata
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Check:
    label: str
    ok: bool
    detail: str


def _version(distribution: str) -> Check:
    try:
        value = importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return Check(distribution, False, "distribution is not installed")
    return Check(distribution, True, value)


def _import(module: str) -> Check:
    try:
        importlib.import_module(module)
    except Exception as exc:  # diagnostic output should identify optional import failures
        return Check(f"import {module}", False, f"{type(exc).__name__}: {exc}")
    return Check(f"import {module}", True, "ok")


def _cli(*args: str) -> Check:
    command = ("harbor", *args)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return Check(" ".join(command), False, "harbor executable is not on PATH")
    except subprocess.TimeoutExpired:
        return Check(" ".join(command), False, "command timed out after 30 seconds")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        return Check(" ".join(command), False, detail[-1] if detail else "non-zero exit")
    first_line = next((line.strip() for line in completed.stdout.splitlines() if line.strip()), "ok")
    return Check(" ".join(command), True, first_line)


def main() -> int:
    checks = [
        _version("harbor"),
        _version("harbor-rewardkit"),
        _version("harbor-langsmith"),
        _import("harbor"),
        _import("rewardkit"),
        _import("harbor_langsmith"),
        _cli("--version"),
        _cli("run", "--help"),
        _cli("exec", "--help"),
    ]
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.label}: {check.detail}")
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
