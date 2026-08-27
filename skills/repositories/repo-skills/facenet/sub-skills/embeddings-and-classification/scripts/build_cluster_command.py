#!/usr/bin/env python3
"""Build a contributed Facenet DBSCAN clustering command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet cluster command.")
    parser.add_argument("model")
    parser.add_argument("data_dir")
    parser.add_argument("out_dir")
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--margin", type=int, default=44)
    parser.add_argument("--min-cluster-size", type=int, default=1)
    parser.add_argument("--cluster-threshold", type=float, default=1.0)
    parser.add_argument("--largest-cluster-only", action="store_true")
    parser.add_argument("--gpu-memory-fraction", type=float, default=1.0)
    args = parser.parse_args()
    cmd = ["python", "-m", "cluster", args.model, args.data_dir, args.out_dir, "--image_size", str(args.image_size), "--margin", str(args.margin), "--min_cluster_size", str(args.min_cluster_size), "--cluster_threshold", str(args.cluster_threshold), "--gpu_memory_fraction", str(args.gpu_memory_fraction)]
    if args.largest_cluster_only:
        cmd.append("--largest_cluster_only")
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
