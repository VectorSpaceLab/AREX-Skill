#!/usr/bin/env python3
"""Safely inspect Sana public CLI help and version details."""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
from pathlib import Path
import shutil
import subprocess
import sys
from textwrap import indent


CLI_COMMANDS = {
    "sana-run": {
        "entrypoint": ["sana-run", "--help"],
        "module": [sys.executable, "-m", "sana.cli.run", "--help"],
        "display_module": "python -m sana.cli.run --help",
    },
    "sana-upload": {
        "entrypoint": ["sana-upload", "--help"],
        "module": [sys.executable, "-m", "sana.cli.upload2hf", "--help"],
        "display_module": "python -m sana.cli.upload2hf --help",
    },
}


def sanitize(text: str) -> str:
    if not text:
        return text
    replacements = {
        str(Path.cwd()): "<cwd>",
        str(Path.home()): "<home>",
        sys.executable: "python",
    }
    for old, new in replacements.items():
        if old:
            text = text.replace(old, new)
    return text


def run_help(command_name: str) -> tuple[subprocess.CompletedProcess[str], str, str]:
    spec = CLI_COMMANDS[command_name]
    executable = spec["entrypoint"][0]
    if shutil.which(executable):
        return subprocess.run(spec["entrypoint"], capture_output=True, text=True), "entrypoint", " ".join(spec["entrypoint"])
    result = subprocess.run(spec["module"], capture_output=True, text=True)
    return result, "module-fallback", spec["display_module"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Sana CLI help without running any jobs.")
    parser.add_argument("--command", choices=sorted(CLI_COMMANDS), required=True)
    parser.add_argument("--show-version", action="store_true")
    parser.add_argument("--json-out", action="store_true")
    args = parser.parse_args()

    result, mode, display_command = run_help(args.command)
    version = None
    try:
        version = metadata.version("sana")
    except metadata.PackageNotFoundError:
        version = None

    payload = {
        "command": args.command,
        "display_command": display_command,
        "inspection_mode": mode,
        "returncode": result.returncode,
        "stdout": sanitize(result.stdout),
        "stderr": sanitize(result.stderr),
        "version": version if args.show_version else None,
        "safe_only": True,
    }

    if args.json_out:
        import json

        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Command: {args.command}")
        print(f"Inspection mode: {mode}")
        print(f"Display command: {display_command}")
        if args.show_version:
            print(f"Version: {version if version is not None else 'unknown'}")
        print(f"Return code: {result.returncode}")
        if payload["stdout"]:
            print("stdout:")
            print(indent(payload["stdout"].rstrip(), "  "))
        if payload["stderr"]:
            print("stderr:")
            print(indent(payload["stderr"].rstrip(), "  "))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
