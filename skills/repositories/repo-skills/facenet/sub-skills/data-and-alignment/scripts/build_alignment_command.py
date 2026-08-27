#!/usr/bin/env python3
"""Build a module-style Facenet MTCNN alignment command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe Facenet MTCNN alignment command.")
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument("--image-size", type=int, default=182)
    parser.add_argument("--margin", type=int, default=44)
    parser.add_argument("--gpu-memory-fraction", type=float, default=1.0)
    parser.add_argument("--random-order", action="store_true")
    parser.add_argument("--detect-multiple-faces", action="store_true")
    args = parser.parse_args()

    cmd = [
        "python",
        "-m",
        "align.align_dataset_mtcnn",
        args.input_dir,
        args.output_dir,
        "--image_size",
        str(args.image_size),
        "--margin",
        str(args.margin),
        "--gpu_memory_fraction",
        str(args.gpu_memory_fraction),
    ]
    if args.random_order:
        cmd.append("--random_order")
    if args.detect_multiple_faces:
        cmd.extend(["--detect_multiple_faces", "True"])
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
