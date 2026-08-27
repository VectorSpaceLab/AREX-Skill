#!/usr/bin/env python3
"""Safe Headroom install and path diagnostic.

This helper does not mutate Headroom state or user configuration. It checks
whether the Python package imports, whether the `headroom` CLI is available, and
what canonical config/workspace paths the current process resolves.

Examples:
  python diagnose_headroom_install.py
  python diagnose_headroom_install.py --check-cli --json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DiagnosticReport:
    ok: bool = False
    python_executable: str = sys.executable
    python_version: str = sys.version.split()[0]
    headroom_import: bool = False
    headroom_version: str | None = None
    package_error: str | None = None
    cli_path: str | None = None
    cli_version_output: str | None = None
    cli_error: str | None = None
    paths: dict[str, str] = field(default_factory=dict)
    optional_imports: dict[str, str] = field(default_factory=dict)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose a local Headroom install safely.")
    parser.add_argument("--check-cli", action="store_true", help="Run `headroom --version` when the CLI is on PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def probe_import(report: DiagnosticReport) -> None:
    try:
        import headroom  # type: ignore

        report.headroom_import = True
        report.headroom_version = str(getattr(headroom, "__version__", "unknown"))
        try:
            from headroom import paths

            report.paths = {
                "config_dir": str(paths.config_dir()),
                "workspace_dir": str(paths.workspace_dir()),
                "settings_path": str(paths.settings_path()),
                "savings_path": str(paths.savings_path()),
                "savings_events_path": str(paths.savings_events_path()),
                "proxy_log_path": str(paths.proxy_log_path()),
                "memory_db_path": str(paths.memory_db_path()),
                "models_config_path": str(paths.models_config_path()),
            }
        except Exception as exc:  # pragma: no cover - diagnostic fallback
            report.paths = {"error": f"{type(exc).__name__}: {exc}"}

        for module in (
            "headroom._core",
            "headroom.proxy.server",
            "headroom.memory",
            "headroom.ccr.mcp_server",
            "headroom.image",
            "headroom.relevance",
        ):
            try:
                __import__(module)
                report.optional_imports[module] = "ok"
            except Exception as exc:  # noqa: BLE001 - report optional failures
                report.optional_imports[module] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # noqa: BLE001 - diagnostic should never traceback first
        report.package_error = f"{type(exc).__name__}: {exc}"


def probe_cli(report: DiagnosticReport, *, run_version: bool) -> None:
    report.cli_path = shutil.which("headroom")
    if not report.cli_path:
        report.cli_error = "headroom not found on PATH"
        return
    if not run_version:
        return
    try:
        completed = subprocess.run(
            [report.cli_path, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        report.cli_version_output = (completed.stdout or completed.stderr).strip()
        if completed.returncode != 0:
            report.cli_error = f"headroom --version exited {completed.returncode}"
    except Exception as exc:  # noqa: BLE001
        report.cli_error = f"{type(exc).__name__}: {exc}"


def print_text(report: DiagnosticReport) -> None:
    status = "OK" if report.ok else "CHECK"
    print(f"Headroom install diagnostic: {status}")
    print(f"Python: {report.python_executable} ({report.python_version})")
    if report.headroom_import:
        print(f"Python package: imported (version {report.headroom_version})")
    else:
        print(f"Python package: FAILED ({report.package_error})")
    print(f"CLI: {report.cli_path or 'not found'}")
    if report.cli_version_output:
        print(f"CLI version: {report.cli_version_output}")
    if report.cli_error:
        print(f"CLI note: {report.cli_error}")
    if report.paths:
        print("Paths:")
        for key, value in report.paths.items():
            print(f"  {key}: {value}")
    if report.optional_imports:
        print("Optional/module probes:")
        for key, value in report.optional_imports.items():
            print(f"  {key}: {value}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = DiagnosticReport()
    probe_import(report)
    probe_cli(report, run_version=args.check_cli)
    report.ok = report.headroom_import and report.cli_path is not None and not report.cli_error
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
