#!/usr/bin/env python3
"""Check that UltraRAG imports cleanly in the active environment.

This helper is safe to run from any working directory.

Usage:
  python check_install.py [--repo-root /path/to/UltraRAG] [--show-cli-help]
"""

from __future__ import annotations

import argparse
import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path


def _maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    candidate = Path(repo_root).expanduser().resolve()
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help="Optional checkout root to add to sys.path before importing the package.",
    )
    parser.add_argument(
        "--show-cli-help",
        action="store_true",
        help="Also run the ultrarag CLI help command if it is available.",
    )
    args = parser.parse_args()

    _maybe_add_repo_root(args.repo_root)

    import ultrarag.api  # noqa: F401
    import ultrarag.client  # noqa: F401
    import ultrarag.server  # noqa: F401

    print(f"ultrarag={importlib.metadata.version('ultrarag')}")
    print(f"ultrarag.client={Path(ultrarag.client.__file__).resolve()}")
    print(f"ultrarag.api={Path(ultrarag.api.__file__).resolve()}")
    print(f"ultrarag.server={Path(ultrarag.server.__file__).resolve()}")

    if args.show_cli_help:
        cli = shutil.which("ultrarag")
        if not cli:
            print("ultrarag CLI not found on PATH; skipping --help check.")
        else:
            result = subprocess.run([cli, "--help"], check=False)
            if result.returncode != 0:
                return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
