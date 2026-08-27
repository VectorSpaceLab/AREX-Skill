#!/usr/bin/env python3
"""Launch a PFLlib experiment from a checkout.

This helper normalizes the working directory to `system/` and keeps the source
path explicit. By default it prints the exact command; add `--execute` to run
it.

Examples:
  python run_experiment.py --repo-root /path/to/PFLlib -- -data MNIST -m CNN -algo FedAvg -gr 1 -did 0
  python run_experiment.py --repo-root /path/to/PFLlib --execute -- -data MNIST -m CNN -algo FedPAC -gr 1 -did 0
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Path to the PFLlib checkout.")
    parser.add_argument("--execute", action="store_true", help="Actually run the experiment instead of printing the command.")
    args, passthrough = parser.parse_known_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    system_dir = repo_root / "system"
    main_py = system_dir / "main.py"

    if not main_py.is_file():
        print(f"error: expected system/main.py under {repo_root}", file=sys.stderr)
        return 2

    if passthrough[:1] == ["--"]:
        passthrough = passthrough[1:]

    cmd = [sys.executable, str(main_py), *passthrough]
    print(f"cwd: {system_dir}")
    print("command:", " ".join(cmd))

    if not args.execute:
        print("dry-run only; add --execute to launch the experiment.")
        return 0

    completed = subprocess.run(cmd, cwd=str(system_dir))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
