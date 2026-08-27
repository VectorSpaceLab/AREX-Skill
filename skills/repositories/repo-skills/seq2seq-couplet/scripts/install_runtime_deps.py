#!/usr/bin/env python3
"""Install the verified runtime dependency set for seq2seq-couplet.

Run this inside the target Python environment. It installs the exact package
set that was verified for the bundled training and inference helpers, including
the protobuf and NumPy compatibility pins required by TensorFlow 1.15.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List, Optional

CPU_PACKAGES = [
    "Flask==2.0.3",
    "Flask-Cors==3.0.10",
    "gevent==22.10.2",
    "greenlet==2.0.2",
    "numpy==1.18.5",
    "protobuf==3.20.3",
    "tensorboard==1.15.0",
    "tensorflow==1.15.0",
]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the verified seq2seq-couplet runtime dependency set."
    )
    parser.add_argument(
        "--backend",
        choices=["cpu"],
        default="cpu",
        help="Verified runtime backend to install. Only the CPU-friendly set is bundled.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pip command without executing it.",
    )
    parser.add_argument(
        "--force-reinstall",
        action="store_true",
        help="Pass --force-reinstall to pip in case the environment drifted.",
    )
    args = parser.parse_args(argv)

    if sys.version_info < (3, 7):
        raise SystemExit("Python 3.7 or newer is required for the verified runtime set.")

    cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir"]
    if args.force_reinstall:
        cmd.append("--force-reinstall")
    cmd.extend(CPU_PACKAGES)

    print("Python:", sys.version.split()[0])
    print("Backend:", args.backend)
    print("Command:", " ".join(cmd))

    if args.dry_run:
        return 0

    completed = subprocess.run(cmd, check=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
