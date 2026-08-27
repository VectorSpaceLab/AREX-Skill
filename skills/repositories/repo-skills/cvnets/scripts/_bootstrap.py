"""Shared helpers for bundled CVNets skill scripts.

These helpers are imported by the runnable wrappers in `scripts/` and
`sub-skills/*/scripts/`. They are not user-facing entry points.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Sequence


def parse_repo_root(
    argv: Sequence[str],
    env_var: str = "CVNETS_REPO_ROOT",
) -> tuple[Path, list[str]]:
    """Extract `--repo-root` from argv and return the cleaned argument list."""

    repo_root = None
    remaining: list[str] = []
    argv = list(argv)
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--repo-root":
            if i + 1 >= len(argv):
                raise SystemExit("--repo-root requires a path.")
            repo_root = argv[i + 1]
            i += 2
            continue
        if token.startswith("--repo-root="):
            repo_root = token.split("=", 1)[1]
            i += 1
            continue
        remaining.append(token)
        i += 1

    if repo_root is None:
        repo_root = os.environ.get(env_var)
    if repo_root is None:
        raise SystemExit("Missing --repo-root or CVNETS_REPO_ROOT.")

    return Path(repo_root).expanduser(), remaining


def activate_repo_root(repo_root: str | Path, chdir: bool = True) -> Path:
    """Add the repo root to `sys.path` and optionally chdir there."""

    repo_path = Path(repo_root).expanduser().resolve()
    if not repo_path.exists():
        raise SystemExit(f"Repo root does not exist: {repo_path}")
    if str(repo_path) not in sys.path:
        sys.path.insert(0, str(repo_path))
    if chdir:
        os.chdir(repo_path)
    return repo_path


def bootstrap_repo(
    argv: Sequence[str],
    env_var: str = "CVNETS_REPO_ROOT",
    chdir: bool = True,
) -> tuple[Path, list[str]]:
    """Parse `--repo-root`, activate the checkout, and return passthrough args."""

    repo_root, remaining = parse_repo_root(argv, env_var=env_var)
    repo_path = activate_repo_root(repo_root, chdir=chdir)
    return repo_path, remaining
