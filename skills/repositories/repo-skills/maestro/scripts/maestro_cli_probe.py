#!/usr/bin/env python3
"""Probe Maestro CLI routes without training, downloads, or credentials.

The probe runs `python -m maestro.cli.main ...` with help/info/version commands
from the current Python environment. It suppresses recipe-import warnings by
default so missing optional dependencies are reported through command failures
rather than noisy warning text.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

ROOT_COMMANDS = [
    ["--help"],
    ["version"],
    ["info"],
]
MODEL_HELP_COMMANDS = [
    ["florence_2", "train", "--help"],
    ["paligemma_2", "train", "--help"],
    ["qwen_2_5_vl", "train", "--help"],
]


def run_command(args: list[str], timeout: float, suppress_warnings: bool) -> dict[str, Any]:
    env = os.environ.copy()
    if suppress_warnings:
        env.setdefault("DISABLE_RECIPE_IMPORTS_WARNINGS", "True")
    cmd = [sys.executable, "-m", "maestro.cli.main", *args]
    try:
        completed = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:  # pragma: no cover
        return {"args": args, "ok": False, "returncode": None, "error": str(exc)}
    except subprocess.TimeoutExpired as exc:  # pragma: no cover
        return {"args": args, "ok": False, "returncode": None, "error": f"timeout after {exc.timeout}s"}
    return {
        "args": args,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_first_lines": completed.stdout.splitlines()[:30],
        "stderr_first_lines": completed.stderr.splitlines()[:30],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely probe Maestro CLI help/info/version routes without training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--include-model-help", action="store_true", help="Also probe each model train --help route.")
    parser.add_argument("--timeout", type=float, default=90.0, help="Per-command timeout in seconds.")
    parser.add_argument("--show-warnings", action="store_true", help="Do not set DISABLE_RECIPE_IMPORTS_WARNINGS=True.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command_args = list(ROOT_COMMANDS)
    if args.include_model_help:
        command_args.extend(MODEL_HELP_COMMANDS)

    results = [run_command(item, args.timeout, not args.show_warnings) for item in command_args]
    ok = all(result["ok"] for result in results)
    report = {"commands": results, "ok": ok}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for result in results:
            command = "maestro " + " ".join(result["args"])
            print(f"{command}: {'ok' if result['ok'] else 'failed'}")
            if not result["ok"]:
                print("  stderr:")
                for line in result.get("stderr_first_lines", []):
                    print(f"    {line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
