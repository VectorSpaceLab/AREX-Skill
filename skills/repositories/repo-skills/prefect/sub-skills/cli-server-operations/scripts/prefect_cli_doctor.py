#!/usr/bin/env python3
"""Safe read-only diagnostics for Prefect CLI/profile/API readiness."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any


HELP_COMMANDS = [
    ["--help"],
    ["config", "--help"],
    ["profile", "use", "--help"],
    ["server", "start", "--help"],
    ["server", "status", "--help"],
    ["api", "--help"],
    ["cloud", "--help"],
    ["variable", "--help"],
    ["artifact", "--help"],
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    command: list[str]
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    advice: str = ""


def run_command(command: list[str], timeout: int, env: dict[str, str] | None = None) -> CheckResult:
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
            check=False,
        )
    except FileNotFoundError:
        return CheckResult(
            name="command-found",
            ok=False,
            command=command,
            advice="Could not find the Prefect executable. Install Prefect or pass --prefect-bin.",
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            name="timeout",
            ok=False,
            command=command,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            advice=f"Command timed out after {timeout} seconds.",
        )

    return CheckResult(
        name="command",
        ok=completed.returncode == 0,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def summarize_config(config_result: CheckResult) -> dict[str, Any]:
    if not config_result.ok:
        return {"available": False, "advice": "Config view failed; inspect stderr for settings validation errors."}

    try:
        payload = json.loads(config_result.stdout)
    except json.JSONDecodeError:
        return {"available": False, "advice": "Config output was not valid JSON."}

    settings = payload.get("settings", [])
    by_name = {item.get("name"): item for item in settings if isinstance(item, dict)}
    api_url = by_name.get("PREFECT_API_URL", {}).get("value")
    api_key = by_name.get("PREFECT_API_KEY", {}).get("value")
    profile = payload.get("profile")
    api_source = by_name.get("PREFECT_API_URL", {}).get("source")
    key_source = by_name.get("PREFECT_API_KEY", {}).get("source")

    hints: list[str] = []
    if not api_url:
        hints.append("No PREFECT_API_URL is visible in active sources; server status and API commands need a configured API URL unless using ephemeral mode.")
    elif isinstance(api_url, str) and "prefect.cloud" not in api_url and not api_url.rstrip("/").endswith("/api"):
        hints.append("Self-hosted API URLs usually end with /api; check that this is not the UI URL.")
    if api_url and "prefect.cloud" in str(api_url) and not api_key:
        hints.append("Cloud API URL is configured but no visible PREFECT_API_KEY source was found.")

    return {
        "available": True,
        "profile": profile,
        "api_url": api_url,
        "api_url_source": api_source,
        "api_key_configured": bool(api_key),
        "api_key_source": key_source,
        "hints": hints,
    }


def compact_text(value: str, limit: int = 600) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def print_human(results: list[CheckResult], summary: dict[str, Any]) -> int:
    failures = [result for result in results if not result.ok]
    print("Prefect CLI Doctor")
    print("==================")
    print()

    config = summary.get("config", {})
    if config.get("available"):
        print(f"Profile: {config.get('profile') or 'unknown'}")
        print(f"API URL: {config.get('api_url') or 'not configured'}")
        if config.get("api_url_source"):
            print(f"API URL source: {config.get('api_url_source')}")
        print(f"API key configured: {config.get('api_key_configured')}")
        if config.get("api_key_source"):
            print(f"API key source: {config.get('api_key_source')}")
        for hint in config.get("hints", []):
            print(f"Hint: {hint}")
        print()

    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {' '.join(result.command)}")
        if not result.ok:
            if result.returncode is not None:
                print(f"  return code: {result.returncode}")
            if result.advice:
                print(f"  advice: {result.advice}")
            if result.stderr.strip():
                print(f"  stderr: {compact_text(result.stderr)}")
            elif result.stdout.strip():
                print(f"  stdout: {compact_text(result.stdout)}")

    if failures:
        print()
        print("One or more checks failed. Use command --help for parser issues and `prefect config view --show-sources` for settings/profile issues.")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe read-only Prefect CLI diagnostics. The script checks the CLI, "
            "version, config/profile visibility, optional help commands, optional "
            "server status, and optional safe-mode plugin diagnostics."
        )
    )
    parser.add_argument(
        "--prefect-bin",
        default="prefect",
        help="Prefect executable to run. Defaults to the first `prefect` on PATH.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Per-command timeout in seconds for short CLI checks.",
    )
    parser.add_argument(
        "--check-help",
        action="store_true",
        help="Check representative command --help output.",
    )
    parser.add_argument(
        "--check-server",
        action="store_true",
        help="Run `prefect server status --output json` without starting a server.",
    )
    parser.add_argument(
        "--wait-server",
        action="store_true",
        help="When checking server status, wait until available or timeout.",
    )
    parser.add_argument(
        "--server-timeout",
        type=int,
        default=10,
        help="Timeout seconds for the Prefect server status wait and subprocess.",
    )
    parser.add_argument(
        "--run-plugin-diagnostics",
        action="store_true",
        help="Run plugin diagnostics with PREFECT_PLUGINS_SAFE_MODE=1.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prefect_bin = args.prefect_bin

    if shutil.which(prefect_bin) is None and os.path.sep not in prefect_bin:
        result = CheckResult(
            name="command-found",
            ok=False,
            command=[prefect_bin],
            advice="Prefect executable not found on PATH. Pass --prefect-bin or activate an environment with Prefect installed.",
        )
        output = {"ok": False, "results": [asdict(result)]}
        if args.json:
            print(json.dumps(output, indent=2))
            return 1
        return print_human([result], {})

    results: list[CheckResult] = []

    version_result = run_command([prefect_bin, "--version"], args.timeout)
    version_result.name = "version"
    results.append(version_result)

    detail_result = run_command([prefect_bin, "version"], args.timeout)
    detail_result.name = "version-detail"
    results.append(detail_result)

    config_result = run_command(
        [prefect_bin, "config", "view", "--output", "json"], args.timeout
    )
    config_result.name = "config-view"
    if not config_result.ok and "Only 'json' output format" in config_result.stderr:
        config_result.advice = "This Prefect version did not accept JSON output for config view. Run `prefect config view --show-sources` manually."
    results.append(config_result)

    profile_result = run_command(
        [prefect_bin, "profile", "ls", "--output", "json"], args.timeout
    )
    profile_result.name = "profile-list"
    results.append(profile_result)

    if args.check_help:
        for help_args in HELP_COMMANDS:
            result = run_command([prefect_bin, *help_args], args.timeout)
            result.name = "help"
            results.append(result)

    if args.check_server:
        server_command = [prefect_bin, "server", "status", "--output", "json"]
        if args.wait_server:
            server_command.extend(["--wait", "--timeout", str(args.server_timeout)])
        result = run_command(server_command, max(args.timeout, args.server_timeout + 5))
        result.name = "server-status"
        if not result.ok:
            result.advice = "Check PREFECT_API_URL, server reachability, profile selection, and whether the URL ends with /api for self-hosted servers."
        results.append(result)

    if args.run_plugin_diagnostics:
        env = os.environ.copy()
        env["PREFECT_PLUGINS_SAFE_MODE"] = "1"
        result = run_command([prefect_bin, "plugins", "diagnose"], args.timeout, env=env)
        result.name = "plugin-diagnostics"
        if not result.ok:
            result.advice = "Plugin diagnostics failed even with safe mode; inspect plugin settings and installed plugin entry points."
        results.append(result)

    summary = {"config": summarize_config(config_result)}
    ok = all(result.ok for result in results)
    output = {"ok": ok, "summary": summary, "results": [asdict(result) for result in results]}

    if args.json:
        print(json.dumps(output, indent=2))
        return 0 if ok else 1
    return print_human(results, summary)


if __name__ == "__main__":
    raise SystemExit(main())
