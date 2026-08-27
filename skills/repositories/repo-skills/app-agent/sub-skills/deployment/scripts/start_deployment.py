#!/usr/bin/env python3
"""Run the AppAgent deployment phase.

This wrapper keeps the runtime command explicit and avoids shell-string
construction. It delegates to the repository's own task executor so the
interactive prompt flow remains unchanged.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch AppAgent deployment.")
    parser.add_argument("--repo-root", default=".", help="Path to the AppAgent checkout.")
    parser.add_argument("--app", required=True, help="Target app name, spaces will be removed.")
    parser.add_argument("--root-dir", default=".", help="Local working directory for apps/ and tasks/ outputs.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    app = args.app.replace(" ", "")

    if not repo_root.exists():
        print(f"ERROR: repo root does not exist: {repo_root}")
        return 1

    script = repo_root / "scripts" / "task_executor.py"
    if not script.exists():
        print(f"ERROR: missing deployment script: {script}")
        return 1

    cmd = [sys.executable, "scripts/task_executor.py", "--app", app, "--root_dir", args.root_dir]
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=repo_root)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
