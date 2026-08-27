#!/usr/bin/env python3
"""Safe AutoGPT Platform backend layout, import, and CLI help probe."""

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
    "backend/app.py",
    "backend/api/rest_api.py",
    "backend/api/ws_api.py",
    "backend/cli/main.py",
    "backend/blocks/test/test_block.py",
    "scripts/generate_block_docs.py",
)
REQUIRED_DIRS = (
    "backend/api/features",
    "backend/blocks",
    "backend/data",
    "backend/sdk",
    "backend/integrations",
    "scripts",
)
HELP_COMMANDS = (
    ("backend.cli.main", "--help"),
    ("backend.cli.generate_openapi_json", "--help"),
    ("scripts.generate_block_docs", "--help"),
)


def run_python(python: str, module: str, arg: str, backend_root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    source_paths = [str(backend_root), str(backend_root.parent / "autogpt_libs")]
    env["PYTHONPATH"] = os.pathsep.join(source_paths + [env.get("PYTHONPATH", "")])
    try:
        result = subprocess.run(
            [python, "-m", module, arg],
            cwd=backend_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": f"{python} -m {module} {arg}", "ok": False, "error": str(exc)}
    return {
        "command": f"{python} -m {module} {arg}",
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_head": result.stdout.strip().splitlines()[:8],
        "stderr_head": result.stderr.strip().splitlines()[:8],
    }


def import_probe(python: str, backend_root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    source_paths = [str(backend_root), str(backend_root.parent / "autogpt_libs")]
    env["PYTHONPATH"] = os.pathsep.join(source_paths + [env.get("PYTHONPATH", "")])
    code = "import backend, autogpt_libs; print('backend-import-ok')"
    try:
        result = subprocess.run(
            [python, "-c", code],
            cwd=backend_root,
            env=env,
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
    backend_root = repo / "autogpt_platform" / "backend"
    files = {path: (backend_root / path).is_file() for path in REQUIRED_FILES}
    dirs = {path: (backend_root / path).is_dir() for path in REQUIRED_DIRS}
    result: dict[str, Any] = {
        "backend_root": str(backend_root),
        "files": files,
        "directories": dirs,
        "python": args.python,
        "import_probe": None,
        "help_commands": [],
    }
    layout_ok = backend_root.is_dir() and all(files.values()) and all(dirs.values())

    python_ok = True
    if not args.skip_python:
        result["import_probe"] = import_probe(args.python, backend_root)
        for module, arg in HELP_COMMANDS:
            result["help_commands"].append(run_python(args.python, module, arg, backend_root))
        python_ok = bool(result["import_probe"]["ok"]) and all(
            item["ok"] for item in result["help_commands"]
        )

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Backend root: {backend_root}")
        print(f"Layout ready: {'yes' if layout_ok else 'no'}")
        if result["import_probe"] is not None:
            print(f"Import probe: {'ok' if result['import_probe']['ok'] else 'failed'}")
            for item in result["help_commands"]:
                print(f"{item['command']}: {'ok' if item['ok'] else 'failed'}")
    return 0 if layout_ok and python_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
