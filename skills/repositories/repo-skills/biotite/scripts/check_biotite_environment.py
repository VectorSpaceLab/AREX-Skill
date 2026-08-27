#!/usr/bin/env python3
"""Safe Biotite environment diagnostic for agents.

This script imports core Biotite surfaces and optionally delegates to bundled
sub-skill diagnostics. It performs no network requests, launches no GUI, and
runs no external analyses.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str | None = None


def check_import(module_name: str) -> Check:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report any import failure
        return Check(module_name, "failed", f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", None)
    detail = f"version={version}" if version else "imported"
    return Check(module_name, "ok", detail)


def run_child(script: Path, args: list[str]) -> Check:
    if not script.exists():
        return Check(str(script), "failed", "bundled diagnostic script is missing")
    process = subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    detail = (process.stdout or process.stderr or "").strip().replace("\n", " | ")
    if len(detail) > 500:
        detail = detail[:497] + "..."
    if process.returncode == 0:
        return Check(script.name, "ok", detail or "passed")
    if process.returncode == 1:
        return Check(script.name, "warning", detail or "optional dependency missing")
    return Check(script.name, "failed", detail or f"exit code {process.returncode}")


def collect(include_optional: bool) -> list[Check]:
    modules = [
        "biotite",
        "biotite.sequence",
        "biotite.sequence.align",
        "biotite.structure",
        "biotite.structure.io.pdbx",
        "biotite.database.rcsb",
        "biotite.application",
        "biotite.interface",
    ]
    checks = [check_import(module) for module in modules]

    if include_optional:
        root = Path(__file__).resolve().parents[1]
        children = [
            root / "sub-skills" / "database-application" / "scripts" / "check_optional_applications.py",
            root / "sub-skills" / "interfaces-visualization" / "scripts" / "check_optional_interfaces.py",
        ]
        for script in children:
            args = ["--json"] if script.name == "check_optional_interfaces.py" else ["--json", "--timeout", "1"]
            checks.append(run_child(script, args))
    return checks


def print_text(checks: list[Check]) -> None:
    print("Biotite environment diagnostic")
    print("No network requests, GUI launches, or analyses were run.\n")
    for check in checks:
        suffix = f" - {check.detail}" if check.detail else ""
        print(f"[{check.status.upper()}] {check.name}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check core Biotite imports and optional bundled diagnostics safely."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="also run optional application/interface diagnostics bundled in sub-skills",
    )
    args = parser.parse_args()

    checks = collect(args.include_optional)
    if args.json:
        print(json.dumps([asdict(check) for check in checks], indent=2, sort_keys=True))
    else:
        print_text(checks)

    if any(check.status == "failed" for check in checks):
        return 2
    if any(check.status == "warning" for check in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
