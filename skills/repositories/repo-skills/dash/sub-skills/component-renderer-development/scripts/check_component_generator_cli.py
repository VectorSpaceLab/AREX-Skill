#!/usr/bin/env python3
"""Check `dash-generate-components --help` without running generation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess


def run(command: str) -> dict:
    exe = shutil.which(command)
    if not exe:
        return {"command": command, "ok": False, "detail": "executable not found on PATH"}
    proc = subprocess.run([exe, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    output = proc.stdout or proc.stderr
    return {"command": command, "ok": proc.returncode == 0, "exit_code": proc.returncode, "first_line": (output.strip().splitlines() or [""])[0]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely check Dash component generator CLI help.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run("dash-generate-components")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "OK" if result["ok"] else "FAIL"
        print(f"[{status}] {result['command']}: {result.get('first_line', result.get('detail'))}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
