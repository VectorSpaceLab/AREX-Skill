#!/usr/bin/env python3
"""Read-only Prefect environment checker for the bundled Prefect repo skill.

The script imports Prefect when available, optionally checks CLI help, and can
query server status only when explicitly requested. It does not start services,
create deployments, mutate profiles, or require the original Prefect checkout.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def run_command(command: list[str], timeout: float) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, f"executable not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout:g}s: {' '.join(command)}"

    output = (completed.stdout or completed.stderr or "").strip()
    first_line = output.splitlines()[0] if output else "no output"
    return completed.returncode == 0, first_line


def import_prefect() -> tuple[Check, dict[str, Any]]:
    try:
        prefect = importlib.import_module("prefect")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return Check("import-prefect", False, f"{type(exc).__name__}: {exc}"), {}

    details = {
        "version": getattr(prefect, "__version__", None),
        "has_flow": hasattr(prefect, "flow"),
        "has_task": hasattr(prefect, "task"),
        "has_get_client": hasattr(prefect, "get_client"),
    }
    return Check("import-prefect", True, f"prefect {details['version']}"), details


def settings_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in ("PREFECT_PROFILE", "PREFECT_API_URL", "PREFECT_API_KEY", "PREFECT_HOME"):
        value = os.environ.get(key)
        if key == "PREFECT_API_KEY" and value:
            value = "<set>"
        summary[key] = value

    try:
        from prefect.settings import get_current_settings

        settings = get_current_settings()
        summary["profile_name"] = getattr(settings, "profile", None)
        api = getattr(settings, "api", None)
        if api is not None:
            summary["settings_api_url"] = str(getattr(api, "url", None))
    except Exception as exc:  # pragma: no cover - diagnostic path
        summary["settings_error"] = f"{type(exc).__name__}: {exc}"

    return summary


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    checks: list[Check] = []
    details: dict[str, Any] = {
        "python": sys.version.split()[0],
        "python_executable": "omitted",
    }

    import_check, import_details = import_prefect()
    checks.append(import_check)
    details["prefect"] = import_details

    if args.show_settings:
        details["settings"] = settings_summary()

    prefect_bin = args.prefect_bin or shutil.which("prefect")
    if args.check_cli:
        if not prefect_bin:
            checks.append(Check("prefect-cli", False, "prefect command not found on PATH"))
        else:
            checks.append(Check("prefect-cli-path", True, "prefect command found"))
            for command_name, command in (
                ("prefect-help", [prefect_bin, "--help"]),
                ("prefect-version", [prefect_bin, "version"]),
                ("prefect-config-help", [prefect_bin, "config", "--help"]),
                ("prefect-deploy-help", [prefect_bin, "deploy", "--help"]),
                ("prefect-server-help", [prefect_bin, "server", "--help"]),
            ):
                ok, detail = run_command(command, args.timeout)
                checks.append(Check(command_name, ok, detail))

    if args.check_server:
        if not prefect_bin:
            checks.append(Check("prefect-server-status", False, "prefect command not found on PATH"))
        else:
            command = [prefect_bin, "server", "status", "--output", "json"]
            if args.wait_server:
                command.extend(["--wait", "--timeout", str(int(args.server_timeout))])
            ok, detail = run_command(command, args.server_timeout)
            checks.append(Check("prefect-server-status", ok, detail))

    return {
        "ok": all(check.ok for check in checks),
        "checks": [asdict(check) for check in checks],
        "details": details,
        "notes": [
            "This script is read-only and does not start a Prefect server or worker.",
            "Passing local checks does not prove server-side objects such as deployments, blocks, automations, or work pools exist.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    status = "PASS" if report["ok"] else "FAIL"
    print(f"Prefect environment check: {status}")
    for check in report["checks"]:
        marker = "PASS" if check["ok"] else "FAIL"
        print(f"[{marker}] {check['name']}: {check['detail']}")
    if "settings" in report["details"]:
        print("Settings summary:")
        for key, value in report["details"]["settings"].items():
            print(f"  {key}: {value}")
    for note in report["notes"]:
        print(f"Note: {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Prefect installation and selected CLI/server signals without mutating state.")
    parser.add_argument("--prefect-bin", help="Path to the prefect CLI executable. Defaults to PATH lookup.")
    parser.add_argument("--check-cli", action="store_true", help="Run read-only Prefect CLI help/version checks.")
    parser.add_argument("--check-server", action="store_true", help="Run `prefect server status --output json`; does not start a server.")
    parser.add_argument("--wait-server", action="store_true", help="Add --wait/--timeout to the server status check.")
    parser.add_argument("--server-timeout", type=float, default=10.0, help="Timeout for server status checks in seconds.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout for each CLI help/version command in seconds.")
    parser.add_argument("--show-settings", action="store_true", help="Include selected environment and Prefect settings-source signals.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    args = parser.parse_args()

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
