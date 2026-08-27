#!/usr/bin/env python3
"""Read-only Platform stack preflight with opt-in env-file initialization."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "README.md",
    "Makefile",
    "docker-compose.yml",
    ".env.default",
    "backend/.env.default",
    "frontend/.env.default",
)
REQUIRED_DIRS = ("backend", "frontend", "backend/backend", "frontend/src")
TOOLS = ("docker", "node", "corepack", "pnpm", "poetry", "make")


def version(command: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [command, "--version"], check=False, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return executable
    lines = (result.stdout or result.stderr).strip().splitlines()
    return lines[0] if lines else executable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--init-env",
        action="store_true",
        help="Create missing .env files from matching defaults; never overwrite.",
    )
    parser.add_argument(
        "--compose-config",
        action="store_true",
        help="Run docker compose config --quiet if Docker Compose is available.",
    )
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    platform = repo / "autogpt_platform"
    files = {path: (platform / path).is_file() for path in REQUIRED_FILES}
    dirs = {path: (platform / path).is_dir() for path in REQUIRED_DIRS}
    created: list[str] = []

    if args.init_env:
        for default in (".env.default", "backend/.env.default", "frontend/.env.default"):
            target = platform / default.replace(".env.default", ".env")
            source = platform / default
            if source.is_file() and not target.exists():
                target.write_bytes(source.read_bytes())
                created.append(str(target.relative_to(repo)))

    compose_check: str | None = None
    if args.compose_config and shutil.which("docker"):
        result = subprocess.run(
            ["docker", "compose", "config", "--quiet"],
            cwd=platform,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        compose_check = "passed" if result.returncode == 0 else (result.stderr.strip() or "failed")

    result: dict[str, Any] = {
        "repo": str(repo),
        "platform": str(platform),
        "files": files,
        "directories": dirs,
        "tools": {tool: version(tool) for tool in TOOLS},
        "created_env_files": created,
        "compose_config": compose_check,
    }
    ready = platform.is_dir() and all(files.values()) and all(dirs.values())
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Platform checkout: {platform}")
        print(f"Layout ready: {'yes' if ready else 'no'}")
        print(f"Created env files: {', '.join(created) if created else 'none'}")
        print("Tools:")
        for tool, value in result["tools"].items():
            print(f"  {tool}: {value or 'not found'}")
        if compose_check is not None:
            print(f"Compose config: {compose_check}")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
