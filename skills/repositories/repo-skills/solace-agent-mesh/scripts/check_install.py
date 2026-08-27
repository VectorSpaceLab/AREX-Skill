#!/usr/bin/env python3
"""Safe installed-package smoke checker for Solace Agent Mesh.

The checker verifies imports and CLI entry points only. It does not start a
broker, run SAM apps, contact LLM providers, open browsers, submit tasks, or
call REST gateways.

Examples:
  python check_install.py
  python check_install.py --include-rest-client
  python check_install.py --rest-client-only
  python check_install.py --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any


class CheckResult:
    def __init__(self, name: str, ok: bool, detail: str, severity: str = "error") -> None:
        self.name = name
        self.ok = ok
        self.detail = detail
        self.severity = severity

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "severity": self.severity, "detail": self.detail}


def dist_version(dist: str) -> str | None:
    try:
        return version(dist)
    except PackageNotFoundError:
        return None


def check_python_version() -> CheckResult:
    major, minor, micro = sys.version_info[:3]
    ok = (major, minor, micro) >= (3, 10, 16) and (major, minor) < (3, 14)
    return CheckResult(
        "python-version",
        ok,
        f"Python {major}.{minor}.{micro}; solace-agent-mesh requires >=3.10.16,<3.14",
    )


def check_distribution(dist: str) -> CheckResult:
    found = dist_version(dist)
    return CheckResult(
        f"dist:{dist}",
        found is not None,
        f"{dist} {found}" if found else f"distribution {dist!r} is not installed",
    )


def check_import(module: str) -> CheckResult:
    try:
        imported = importlib.import_module(module)
        location = getattr(imported, "__file__", "built-in or namespace package")
        return CheckResult(f"import:{module}", True, str(location), severity="info")
    except Exception as exc:
        return CheckResult(f"import:{module}", False, f"{type(exc).__name__}: {exc}")


def run_help(command: list[str], timeout: int) -> CheckResult:
    executable = command[0]
    if shutil.which(executable) is None:
        return CheckResult("cli:" + " ".join(command), False, f"executable {executable!r} was not found on PATH")
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult("cli:" + " ".join(command), False, f"timed out after {timeout}s")
    output = (completed.stdout or completed.stderr or "").strip().splitlines()
    first = output[0] if output else "no output"
    return CheckResult(
        "cli:" + " ".join(command),
        completed.returncode == 0,
        f"exit={completed.returncode}; {first}",
    )


def collect_checks(include_rest_client: bool, cli_timeout: int, main_package: bool = True) -> list[CheckResult]:
    checks: list[CheckResult] = [check_python_version()]
    if main_package:
        checks.extend(
            [
                check_distribution("solace-agent-mesh"),
                check_import("solace_agent_mesh.cli.main"),
                check_import("solace_agent_mesh.workflow.app"),
                check_import("solace_agent_mesh.evaluation.run"),
                check_import("solace_agent_mesh.config_portal.backend.common"),
                run_help(["sam", "--help"], cli_timeout),
                run_help(["sam", "--version"], cli_timeout),
            ]
        )
    if include_rest_client:
        checks.extend(
            [
                check_distribution("sam-rest-client"),
                check_import("sam_rest_client.client"),
                check_import("sam_rest_client.cli"),
                run_help(["sam-rest-cli", "--help"], cli_timeout),
            ]
        )
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe Solace Agent Mesh install/import/CLI smoke checker.")
    parser.add_argument("--include-rest-client", action="store_true", help="Also check the separate sam-rest-client package and sam-rest-cli entry point in this same environment.")
    parser.add_argument("--rest-client-only", action="store_true", help="Check only Python plus sam-rest-client/sam-rest-cli; useful when the REST client is isolated from the main SAM package.")
    parser.add_argument("--cli-timeout", type=int, default=15, help="Timeout in seconds for each CLI help/version command.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    checks = collect_checks(args.include_rest_client or args.rest_client_only, args.cli_timeout, main_package=not args.rest_client_only)
    failures = [c for c in checks if not c.ok and c.severity == "error"]

    if args.json:
        print(json.dumps({"ok": not failures, "checks": [c.as_dict() for c in checks]}, indent=2))
    else:
        for c in checks:
            status = "OK" if c.ok else c.severity.upper()
            print(f"[{status}] {c.name}: {c.detail}")
        print(f"Summary: {len(failures)} blocking failure(s)")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
