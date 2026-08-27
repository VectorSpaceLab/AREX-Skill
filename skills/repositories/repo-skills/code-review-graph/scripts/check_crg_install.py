#!/usr/bin/env python3
"""Smoke-check a code-review-graph installation without touching a graph database.

This helper is bundled with the repo skill so future agents can verify import,
version, CLI discovery, and packaged docs without reopening the source checkout.
It performs no network calls and does not create or update `.code-review-graph/`.

Examples:
  python check_crg_install.py
  python check_crg_install.py --json
  python check_crg_install.py --skip-cli
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip invoking the console script; useful when PATH is intentionally minimal.",
    )
    args = parser.parse_args()

    report: dict[str, object] = {"status": "ok", "checks": {}}
    checks: dict[str, object] = report["checks"]  # type: ignore[assignment]

    try:
        import code_review_graph
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        report["status"] = "error"
        checks["import"] = f"FAILED: {type(exc).__name__}: {exc}"
        return _finish(report, args.json)

    checks["import"] = "ok"
    checks["package_version_attr"] = getattr(code_review_graph, "__version__", None)
    try:
        checks["distribution_version"] = metadata.version("code-review-graph")
    except metadata.PackageNotFoundError:
        checks["distribution_version"] = "not installed as a distribution"

    try:
        from code_review_graph.tools import get_docs_section

        docs_status = get_docs_section("usage").get("status")
        checks["packaged_docs_usage"] = docs_status
        if docs_status != "ok":
            report["status"] = "warning"
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        report["status"] = "warning"
        checks["packaged_docs_usage"] = f"FAILED: {type(exc).__name__}: {exc}"

    if not args.skip_cli:
        command = shutil.which("code-review-graph")
        checks["cli_on_path"] = bool(command)
        if command:
            try:
                proc = subprocess.run(
                    [command, "--version"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    check=False,
                )
                checks["cli_version_exit"] = proc.returncode
                checks["cli_version_stdout"] = proc.stdout.strip()
                if proc.returncode != 0:
                    report["status"] = "warning"
                    checks["cli_version_stderr"] = proc.stderr.strip()
            except Exception as exc:  # noqa: BLE001 - diagnostic script
                report["status"] = "warning"
                checks["cli_version"] = f"FAILED: {type(exc).__name__}: {exc}"
        else:
            report["status"] = "warning"
            checks["cli_hint"] = (
                "The package imports, but the console script is not on PATH. "
                "Use python -m code_review_graph or reinstall with pipx/uvx/PATH fixed."
            )

    return _finish(report, args.json)


def _finish(report: dict[str, object], as_json: bool) -> int:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"code-review-graph install smoke: {report['status']}")
        for key, value in (report.get("checks") or {}).items():
            print(f"- {key}: {value}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
