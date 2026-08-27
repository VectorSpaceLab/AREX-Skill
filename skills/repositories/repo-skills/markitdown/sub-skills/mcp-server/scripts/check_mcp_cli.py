#!/usr/bin/env python3
"""Safe preflight checks for the markitdown-mcp CLI.

This script does not start a persistent MCP server. It only locates the CLI,
inspects `--help`, validates a requested transport/host/port combination, and
reports the plugin environment variable state when requested.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

LOCALHOST_HOSTS = {"127.0.0.1", "localhost"}
PLUGIN_TRUE_VALUES = {"true", "1", "yes"}
REQUIRED_HELP_FLAGS = ("--http", "--sse", "--host", "--port")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect markitdown-mcp CLI availability and validate safe transport "
            "settings without starting a server."
        )
    )
    parser.add_argument(
        "--command",
        default="markitdown-mcp",
        help="CLI executable name or path to inspect (default: markitdown-mcp).",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http", "sse"),
        default="stdio",
        help="Transport configuration to validate (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host value to validate. Only valid for --transport http or sse.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port value to validate. Only valid for --transport http or sse.",
    )
    parser.add_argument(
        "--report-plugin-env",
        action="store_true",
        help="Report whether MARKITDOWN_ENABLE_PLUGINS is set to a truthy value.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of human-readable text.",
    )
    return parser.parse_args()


def resolve_command(command: str) -> str | None:
    command_path = Path(command)
    if command_path.parent != Path(".") or command_path.is_absolute():
        return str(command_path) if command_path.exists() else None
    resolved = shutil.which(command)
    if resolved is not None:
        return resolved
    sibling = Path(sys.executable).with_name(command)
    if sibling.exists():
        return str(sibling)
    return None


def inspect_help(executable: str) -> tuple[list[str], list[str], str]:
    messages: list[str] = []
    warnings: list[str] = []

    try:
        completed_process = subprocess.run(
            [executable, "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return [], [], "timed out while running markitdown-mcp --help"
    except OSError as error:
        return [], [], f"failed to run markitdown-mcp --help: {error}"

    if completed_process.returncode != 0:
        help_error = completed_process.stderr.strip() or completed_process.stdout.strip()
        return [], [], f"markitdown-mcp --help exited with {completed_process.returncode}: {help_error}"

    help_text = completed_process.stdout
    missing_flags = [flag for flag in REQUIRED_HELP_FLAGS if flag not in help_text]
    if missing_flags:
        return (
            messages,
            warnings,
            "help output is missing expected flags: " + ", ".join(missing_flags),
        )

    messages.append("help output contains --http, --sse, --host, and --port")
    return messages, warnings, ""


def distribution_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package_name in ("markitdown-mcp", "markitdown"):
        try:
            versions[package_name] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            versions[package_name] = "not installed in this Python environment"
    return versions


def validate_transport(args: argparse.Namespace) -> tuple[list[str], list[str], list[str], dict[str, Any]]:
    messages: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    effective: dict[str, Any] = {"transport": args.transport}

    if args.transport == "stdio":
        if args.host is not None or args.port is not None:
            errors.append("--host and --port are only valid with --transport http or --transport sse")
        else:
            messages.append("STDIO transport is selected; no listening socket will be opened by this check")
        return messages, warnings, errors, effective

    effective_host = args.host or "127.0.0.1"
    effective_port = args.port if args.port is not None else 3001
    effective["host"] = effective_host
    effective["port"] = effective_port

    if args.transport == "sse":
        warnings.append("--sse is a deprecated alias for HTTP mode; prefer --transport http for new configs")

    if not (1 <= effective_port <= 65535):
        errors.append("port must be between 1 and 65535")

    if args.host is not None and effective_host not in LOCALHOST_HOSTS:
        warnings.append(
            "non-localhost bind requested; markitdown-mcp has no authentication and runs with user privileges"
        )
    else:
        messages.append("HTTP/SSE host is loopback-local by default or explicit selection")

    messages.append("validated HTTP/SSE settings without starting a server")
    return messages, warnings, errors, effective


def plugin_env_report() -> dict[str, Any]:
    raw_value = os.getenv("MARKITDOWN_ENABLE_PLUGINS")
    normalized = "" if raw_value is None else raw_value.strip().lower()
    return {
        "variable": "MARKITDOWN_ENABLE_PLUGINS",
        "value_set": raw_value is not None,
        "enabled": normalized in PLUGIN_TRUE_VALUES,
        "truthy_values": sorted(PLUGIN_TRUE_VALUES),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": False,
        "messages": [],
        "warnings": [],
        "errors": [],
        "versions": distribution_versions(),
    }

    executable = resolve_command(args.command)
    if executable is None:
        report["errors"].append(f"could not find executable: {args.command}")
    else:
        report["executable"] = executable
        report["messages"].append(f"found executable: {executable}")
        help_messages, help_warnings, help_error = inspect_help(executable)
        report["messages"].extend(help_messages)
        report["warnings"].extend(help_warnings)
        if help_error:
            report["errors"].append(help_error)

    transport_messages, transport_warnings, transport_errors, effective = validate_transport(args)
    report["messages"].extend(transport_messages)
    report["warnings"].extend(transport_warnings)
    report["errors"].extend(transport_errors)
    report["effective"] = effective

    if args.report_plugin_env:
        report["plugin_env"] = plugin_env_report()

    report["ok"] = not report["errors"]
    return report


def print_text_report(report: dict[str, Any]) -> None:
    for package_name, version in report["versions"].items():
        print(f"version: {package_name} = {version}")

    if "executable" in report:
        print(f"executable: {report['executable']}")

    for message in report["messages"]:
        print(f"ok: {message}")
    for warning in report["warnings"]:
        print(f"warning: {warning}")
    for error in report["errors"]:
        print(f"error: {error}", file=sys.stderr)

    if "plugin_env" in report:
        plugin_env = report["plugin_env"]
        state = "enabled" if plugin_env["enabled"] else "disabled"
        set_text = "set" if plugin_env["value_set"] else "unset"
        print(f"plugin-env: MARKITDOWN_ENABLE_PLUGINS is {set_text}; plugins are {state}")

    result = "passed" if report["ok"] else "failed"
    print(f"result: safe preflight {result}; no MCP server was started")


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
