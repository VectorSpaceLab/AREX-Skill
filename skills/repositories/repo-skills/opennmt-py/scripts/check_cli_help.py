#!/usr/bin/env python3
"""Run the main OpenNMT-py CLIs with --help."""

from __future__ import annotations

import subprocess
import sys

COMMANDS = [
    [sys.executable, "-m", "onmt.bin.build_vocab", "--help"],
    [sys.executable, "-m", "onmt.bin.train", "--help"],
    [sys.executable, "-m", "onmt.bin.translate", "--help"],
    [sys.executable, "-m", "onmt.bin.server", "--help"],
    [sys.executable, "-m", "onmt.bin.average_models", "--help"],
    [sys.executable, "-m", "onmt.bin.release_model", "--help"],
]


def main() -> None:
    for cmd in COMMANDS:
        print("$", " ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
