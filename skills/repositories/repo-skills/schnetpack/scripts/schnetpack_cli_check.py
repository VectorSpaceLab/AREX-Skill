#!/usr/bin/env python3
"""Run safe SchNetPack CLI help checks without launching workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


DEFAULT_COMMANDS = ["spktrain", "spkpredict", "spkmd", "spkconvert", "spkdeploy"]


def check_command(command: str, timeout: int) -> dict[str, Any]:
    entry: dict[str, Any] = {"command": command, "found": False, "ok": False}
    path = shutil.which(command)
    if path is None:
        sibling = Path(sys.executable).resolve().parent / command
        if sibling.exists():
            path = str(sibling)
    if path is None:
        entry["error"] = "not found on PATH or next to sys.executable"
        return entry
    entry["found"] = True
    entry["path"] = path
    try:
        completed = subprocess.run(
            [path, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        entry["error"] = f"timed out after {timeout}s"
        return entry
    except OSError as exc:
        entry["error"] = str(exc)
        return entry

    entry["returncode"] = completed.returncode
    entry["ok"] = completed.returncode == 0
    entry["output_head"] = completed.stdout.splitlines()[:30]
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commands",
        nargs="+",
        default=DEFAULT_COMMANDS,
        help="Command names to check with --help.",
    )
    parser.add_argument("--timeout", type=int, default=45, help="Timeout per command in seconds.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args()

    results = [check_command(command, args.timeout) for command in args.commands]
    ok = all(item["ok"] for item in results)
    payload = {"ok": ok, "results": results}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in results:
            status = "ok" if item["ok"] else "failed"
            print(f"{item['command']}: {status}")
            if not item.get("found"):
                print(f"  error: {item.get('error')}")
            elif item.get("error"):
                print(f"  error: {item['error']}")
            else:
                print(f"  returncode: {item.get('returncode')}")
                for line in item.get("output_head", [])[:8]:
                    print(f"  {line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
