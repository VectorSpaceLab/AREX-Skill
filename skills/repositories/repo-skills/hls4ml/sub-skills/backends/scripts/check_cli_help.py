#!/usr/bin/env python3
"""Check the deprecated hls4ml CLI help surface safely.

This helper only asks argparse for help text. It does not convert, write,
build, report, or run synthesis. Use it to confirm that the installed CLI still
advertises the expected legacy subcommands.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from typing import Any

REQUIRED_SUBCOMMANDS = ["config", "convert", "build", "report"]
PYTHON_CLI_SNIPPET = "import hls4ml.cli; hls4ml.cli.main()"
CLI_EXECUTABLE = shutil.which("hls4ml")


def run_cli_help(cli_args: list[str]) -> dict[str, Any]:
    """Run hls4ml.cli with help arguments in a subprocess."""

    if CLI_EXECUTABLE:
        cmd = [CLI_EXECUTABLE, *cli_args]
    else:
        cmd = [sys.executable, "-c", PYTHON_CLI_SNIPPET, *cli_args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "args": cli_args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def extract_usage(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("usage:"):
            return line.strip()
    return None


def extract_root_subcommands(text: str) -> list[str]:
    match = re.search(r"\{([^{}]+)\}", text)
    if not match:
        return []
    return [part.strip() for part in match.group(1).split(",") if part.strip()]


def extract_long_options(text: str) -> list[str]:
    return sorted(set(re.findall(r"(?<!\w)--[A-Za-z][A-Za-z0-9_-]*", text)))


def summarize(name: str, result: dict[str, Any], include_output: bool) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "name": name,
        "args": result["args"],
        "returncode": result["returncode"],
        "usage": extract_usage(result["stdout"]),
        "longOptions": extract_long_options(result["stdout"]),
    }
    if include_output:
        summary["stdout"] = result["stdout"]
        summary["stderr"] = result["stderr"]
    elif result["stderr"]:
        summary["stderrPreview"] = result["stderr"].splitlines()[:8]
    return summary


def print_text(summary: dict[str, Any]) -> None:
    print("hls4ml CLI help check")
    print("deprecated: true; prefer the Python API for new workflows")
    print("root subcommands: " + ", ".join(summary["rootSubcommands"]))
    if summary["missingSubcommands"]:
        print("missing required subcommands: " + ", ".join(summary["missingSubcommands"]))
    print()
    for item in summary["helps"]:
        print(f"[{item['returncode']}] {item['name']}: {item.get('usage')}")
        if item.get("longOptions"):
            print("  options: " + ", ".join(item["longOptions"]))
        if item.get("stderrPreview"):
            print("  stderr preview: " + " | ".join(item["stderrPreview"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect deprecated hls4ml CLI help output.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if expected help output is missing.")
    parser.add_argument("--include-output", action="store_true", help="Include raw help stdout/stderr in JSON.")
    args = parser.parse_args(argv)

    commands = {
        "root": ["--help"],
        "config": ["config", "--help"],
        "convert": ["convert", "--help"],
        "build": ["build", "--help"],
        "report": ["report", "--help"],
    }

    raw_results = {name: run_cli_help(cmd_args) for name, cmd_args in commands.items()}
    root_subcommands = extract_root_subcommands(raw_results["root"]["stdout"])
    missing = [name for name in REQUIRED_SUBCOMMANDS if name not in root_subcommands]
    helps = [summarize(name, raw_results[name], args.include_output) for name in commands]

    summary = {
        "deprecated": True,
        "preferredApi": "Python API",
        "requiredSubcommands": REQUIRED_SUBCOMMANDS,
        "rootSubcommands": root_subcommands,
        "missingSubcommands": missing,
        "helps": helps,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)

    failed_help = any(item["returncode"] != 0 for item in helps)
    return 1 if args.strict and (missing or failed_help) else 0


if __name__ == "__main__":
    raise SystemExit(main())
