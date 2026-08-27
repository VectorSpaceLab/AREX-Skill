#!/usr/bin/env python3
"""Build a Facenet image-comparison command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet compare command.")
    parser.add_argument("model")
    parser.add_argument("images", nargs="+")
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--margin", type=int, default=44)
    parser.add_argument("--gpu-memory-fraction", type=float, default=1.0)
    args = parser.parse_args()
    cmd = ["python", "-m", "compare", args.model, *args.images, "--image_size", str(args.image_size), "--margin", str(args.margin), "--gpu_memory_fraction", str(args.gpu_memory_fraction)]
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
