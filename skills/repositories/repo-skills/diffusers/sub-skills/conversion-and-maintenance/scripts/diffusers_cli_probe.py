#!/usr/bin/env python3
"""Safe probes for Diffusers CLI availability and environment reporting.

This script only calls help/env style commands. It does not run conversion,
write model files, download checkpoints, or push to the Hub.
"""

import argparse
import json
import shutil
import subprocess
import sys


def run_command(command):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main():
    parser = argparse.ArgumentParser(description="Run safe diffusers-cli probes.")
    parser.add_argument(
        "probe",
        choices=["help", "env", "subcommands"],
        nargs="?",
        default="help",
        help="Probe to run. 'env' executes diffusers-cli env; others only print help.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON with command, return code, stdout, and stderr instead of plain stdout/stderr.",
    )
    args = parser.parse_args()

    executable = shutil.which("diffusers-cli")
    if executable is None:
        command_prefix = [sys.executable, "-m", "diffusers.commands.diffusers_cli"]
    else:
        command_prefix = [executable]

    if args.probe == "help":
        command = command_prefix + ["--help"]
    elif args.probe == "env":
        command = command_prefix + ["env"]
    else:
        commands = [command_prefix + ["--help"]]
        for subcommand in ("env", "fp16_safetensors", "custom_blocks"):
            commands.append(command_prefix + [subcommand, "--help"])
        payload = [run_command(command) for command in commands]
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for item in payload:
                print("$ " + " ".join(item["command"]))
                if item["stdout"]:
                    print(item["stdout"].rstrip())
                if item["stderr"]:
                    print(item["stderr"].rstrip(), file=sys.stderr)
                print(f"[exit {item['returncode']}]")
        return 0 if all(item["returncode"] == 0 for item in payload) else 1

    payload = run_command(command)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if payload["stdout"]:
            print(payload["stdout"], end="")
        if payload["stderr"]:
            print(payload["stderr"], end="", file=sys.stderr)
    return payload["returncode"]


if __name__ == "__main__":
    raise SystemExit(main())
