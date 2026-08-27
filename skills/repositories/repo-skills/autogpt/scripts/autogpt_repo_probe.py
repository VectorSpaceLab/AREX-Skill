#!/usr/bin/env python3
"""Read-only layout and host-tool probe for an AutoGPT checkout."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_FILES = (
    "README.md",
    "autogpt_platform/README.md",
    "autogpt_platform/Makefile",
    "autogpt_platform/docker-compose.yml",
    "autogpt_platform/backend/pyproject.toml",
    "autogpt_platform/frontend/package.json",
    "classic/pyproject.toml",
)
EXPECTED_DIRS = (
    "autogpt_platform/backend/backend",
    "autogpt_platform/frontend/src",
    "classic/original_autogpt/autogpt",
    "classic/forge/forge",
    "classic/direct_benchmark/direct_benchmark",
)
TOOLS = ("git", "docker", "poetry", "node", "corepack", "pnpm", "conda", "uv")


def tool_version(command: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return executable
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else executable


def probe(repo: Path) -> dict[str, Any]:
    repo = repo.expanduser().resolve()
    files = {path: (repo / path).is_file() for path in EXPECTED_FILES}
    dirs = {path: (repo / path).is_dir() for path in EXPECTED_DIRS}
    return {
        "repo": str(repo),
        "looks_like_autogpt": sum(files.values()) >= 5 and sum(dirs.values()) >= 3,
        "files": files,
        "directories": dirs,
        "tools": {tool: tool_version(tool) for tool in TOOLS},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = probe(args.repo)
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["looks_like_autogpt"] else 1

    print(f"AutoGPT checkout: {result['repo']}")
    print(f"Recognized layout: {'yes' if result['looks_like_autogpt'] else 'no'}")
    print("Missing expected files:")
    missing_files = [path for path, present in result["files"].items() if not present]
    print("  none" if not missing_files else "  " + "\n  ".join(missing_files))
    print("Missing expected directories:")
    missing_dirs = [path for path, present in result["directories"].items() if not present]
    print("  none" if not missing_dirs else "  " + "\n  ".join(missing_dirs))
    print("Host tools:")
    for tool, version in result["tools"].items():
        print(f"  {tool}: {version or 'not found'}")
    return 0 if result["looks_like_autogpt"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
