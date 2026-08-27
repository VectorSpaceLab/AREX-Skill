#!/usr/bin/env python3
"""Build a Facenet freeze_graph command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet freeze_graph command.")
    parser.add_argument("model_dir")
    parser.add_argument("output_file")
    args = parser.parse_args()
    cmd = ["python", "-m", "freeze_graph", args.model_dir, args.output_file]
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
