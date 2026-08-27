#!/usr/bin/env python3
"""Check that Cookiecutter Data Science is importable and its CLI is usable.

Example:
  python check_ccds_environment.py --json
  python check_ccds_environment.py --require-version 2.3.0
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any


def _result(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run safe import, metadata, and CLI checks for cookiecutter-data-science."
    )
    parser.add_argument(
        "--require-version",
        help="Require an exact cookiecutter-data-science distribution version.",
    )
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip ccds console-script checks and only verify Python imports/metadata.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text checklist.",
    )
    args = parser.parse_args()

    checks: list[dict[str, Any]] = []

    try:
        dist_version = metadata.version("cookiecutter-data-science")
        checks.append(_result("distribution", True, f"cookiecutter-data-science {dist_version}"))
        if args.require_version and dist_version != args.require_version:
            checks.append(
                _result(
                    "required-version",
                    False,
                    f"expected {args.require_version}, found {dist_version}",
                )
            )
        elif args.require_version:
            checks.append(_result("required-version", True, dist_version))
    except metadata.PackageNotFoundError:
        checks.append(
            _result(
                "distribution",
                False,
                "cookiecutter-data-science is not installed in this Python environment",
            )
        )
        dist_version = None

    for module_name in [
        "ccds",
        "ccds.__main__",
        "ccds.monkey_patch",
        "ccds.hook_utils.dependencies",
        "ccds.hook_utils.custom_config",
    ]:
        try:
            module = importlib.import_module(module_name)
            checks.append(_result(f"import:{module_name}", True, getattr(module, "__name__", module_name)))
        except Exception as exc:  # noqa: BLE001 - diagnostic helper should report any import failure.
            checks.append(_result(f"import:{module_name}", False, f"{type(exc).__name__}: {exc}"))

    try:
        deps = importlib.import_module("ccds.hook_utils.dependencies")
        spec_2 = deps.resolve_python_version_specifier("3.12")
        spec_3 = deps.resolve_python_version_specifier("3.12.2")
        ok = spec_2 == "~=3.12.0" and spec_3 == "==3.12.2"
        checks.append(_result("helper:python-version-specifier", ok, f"3.12->{spec_2}; 3.12.2->{spec_3}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_result("helper:python-version-specifier", False, f"{type(exc).__name__}: {exc}"))

    if not args.skip_cli:
        ccds_exe = shutil.which("ccds")
        if not ccds_exe:
            checks.append(_result("cli:ccds", False, "ccds executable not found on PATH"))
        else:
            try:
                proc = subprocess.run(
                    [ccds_exe, "--help"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=20,
                    check=False,
                )
                combined = proc.stdout + proc.stderr
                ok = proc.returncode == 0 and "Usage: ccds" in combined and "--checkout" in combined
                checks.append(
                    _result(
                        "cli:ccds-help",
                        ok,
                        "help output includes Usage and --checkout"
                        if ok
                        else f"exit {proc.returncode}: {combined[:400]}",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                checks.append(_result("cli:ccds-help", False, f"{type(exc).__name__}: {exc}"))

    overall_ok = all(check["ok"] for check in checks)
    payload = {"ok": overall_ok, "python": sys.version.split()[0], "checks": checks}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for check in checks:
            status = "PASS" if check["ok"] else "FAIL"
            print(f"[{status}] {check['name']}: {check['detail']}")
        print(f"Overall: {'PASS' if overall_ok else 'FAIL'}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
