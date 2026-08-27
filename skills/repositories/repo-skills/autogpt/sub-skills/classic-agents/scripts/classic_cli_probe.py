#!/usr/bin/env python3
"""Safe AutoGPT Classic layout, import, and CLI help probe."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "pyproject.toml",
    "original_autogpt/autogpt/__main__.py",
    "forge/forge/__main__.py",
    "direct_benchmark/direct_benchmark/__main__.py",
    "forge/tests/test_permissions.py",
)
REQUIRED_DIRS = (
    "original_autogpt/autogpt",
    "forge/forge",
    "direct_benchmark/direct_benchmark",
)
HELP_COMMANDS = (
    ("autogpt", "--help"),
    ("autogpt", "run", "--help"),
    ("autogpt", "serve", "--help"),
    ("direct_benchmark", "--help"),
)


def python_env(classic_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    source_paths = [
        str(classic_root / "original_autogpt"),
        str(classic_root / "forge"),
        str(classic_root / "direct_benchmark"),
    ]
    env["PYTHONPATH"] = os.pathsep.join(source_paths + [env.get("PYTHONPATH", "")])
    return env


def run_command(python: str, args: tuple[str, ...], classic_root: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [python, "-m", *args],
            cwd=classic_root,
            env=python_env(classic_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": f"{python} -m {' '.join(args)}", "ok": False, "error": str(exc)}
    return {
        "command": f"{python} -m {' '.join(args)}",
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_head": result.stdout.strip().splitlines()[:10],
        "stderr_head": result.stderr.strip().splitlines()[:10],
    }


def import_probe(python: str, classic_root: Path) -> dict[str, Any]:
    code = "import autogpt, forge, direct_benchmark; print('classic-import-ok')"
    try:
        result = subprocess.run(
            [python, "-c", code],
            cwd=classic_root,
            env=python_env(classic_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_head": result.stdout.strip().splitlines()[:8],
        "stderr_head": result.stderr.strip().splitlines()[:8],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--skip-python", action="store_true")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    classic_root = repo / "classic"
    files = {path: (classic_root / path).is_file() for path in REQUIRED_FILES}
    dirs = {path: (classic_root / path).is_dir() for path in REQUIRED_DIRS}
    result: dict[str, Any] = {
        "classic_root": str(classic_root),
        "files": files,
        "directories": dirs,
        "python": args.python,
        "import_probe": None,
        "help_commands": [],
    }
    layout_ok = classic_root.is_dir() and all(files.values()) and all(dirs.values())
    python_ok = True
    if not args.skip_python:
        result["import_probe"] = import_probe(args.python, classic_root)
        result["help_commands"] = [
            run_command(args.python, command, classic_root) for command in HELP_COMMANDS
        ]
        python_ok = bool(result["import_probe"]["ok"]) and all(
            item["ok"] for item in result["help_commands"]
        )

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Classic root: {classic_root}")
        print(f"Layout ready: {'yes' if layout_ok else 'no'}")
        if result["import_probe"] is not None:
            print(f"Import probe: {'ok' if result['import_probe']['ok'] else 'failed'}")
            for item in result["help_commands"]:
                print(f"{item['command']}: {'ok' if item['ok'] else 'failed'}")
    return 0 if layout_ok and python_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
