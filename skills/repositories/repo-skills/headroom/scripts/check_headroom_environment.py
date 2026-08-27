#!/usr/bin/env python3
"""Check Headroom package, CLI, and optional module availability safely.

This helper performs read-only imports and `headroom --version` checks. It does
not start a proxy, contact an LLM provider, write config, or download models.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field


@dataclass
class Report:
    ok: bool = False
    python: str = sys.executable
    package_version: str | None = None
    cli: str | None = None
    cli_version: str | None = None
    imports: dict[str, str] = field(default_factory=dict)
    error: str | None = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Headroom environment without side effects.")
    parser.add_argument("--check-cli", action="store_true", help="Run `headroom --version` when available.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv or sys.argv[1:])
    report = Report()

    try:
        import headroom

        report.package_version = str(getattr(headroom, "__version__", "unknown"))
        for name in (
            "headroom._core",
            "headroom.cli.main",
            "headroom.proxy.server",
            "headroom.memory",
            "headroom.image",
            "headroom.relevance",
        ):
            try:
                __import__(name)
                report.imports[name] = "ok"
            except Exception as exc:  # noqa: BLE001 - report optional module failures
                report.imports[name] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # noqa: BLE001 - clean diagnostic output
        report.error = f"{type(exc).__name__}: {exc}"

    report.cli = shutil.which("headroom")
    if args.check_cli and report.cli:
        try:
            result = subprocess.run([report.cli, "--version"], check=False, capture_output=True, text=True, timeout=10)
            report.cli_version = (result.stdout or result.stderr).strip()
            if result.returncode:
                report.error = report.error or f"headroom --version exited {result.returncode}"
        except Exception as exc:  # noqa: BLE001
            report.error = report.error or f"{type(exc).__name__}: {exc}"

    report.ok = report.package_version is not None and (not args.check_cli or report.cli is not None)
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(f"Headroom package: {report.package_version or 'unavailable'}")
        print(f"CLI: {report.cli or 'not found'}")
        if report.cli_version:
            print(f"CLI version: {report.cli_version}")
        for name, status in report.imports.items():
            print(f"{name}: {status}")
        if report.error:
            print(f"error: {report.error}")
        print("ok" if report.ok else "not-ok")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
