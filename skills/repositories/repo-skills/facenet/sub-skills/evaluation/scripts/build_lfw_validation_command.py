#!/usr/bin/env python3
"""Build a Facenet LFW validation command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet validate_on_lfw command.")
    parser.add_argument("lfw_dir")
    parser.add_argument("model")
    parser.add_argument("--lfw-pairs", default="data/pairs.txt")
    parser.add_argument("--lfw-batch-size", type=int, default=100)
    parser.add_argument("--lfw-nrof-folds", type=int, default=10)
    parser.add_argument("--distance-metric", type=int, default=0)
    parser.add_argument("--subtract-mean", action="store_true")
    parser.add_argument("--use-flipped-images", action="store_true")
    parser.add_argument("--use-fixed-image-standardization", action="store_true")
    parser.add_argument("--image-size", type=int, default=160)
    args = parser.parse_args()
    cmd = ["python", "-m", "validate_on_lfw", args.lfw_dir, args.model, "--lfw_pairs", args.lfw_pairs, "--lfw_batch_size", str(args.lfw_batch_size), "--lfw_nrof_folds", str(args.lfw_nrof_folds), "--distance_metric", str(args.distance_metric), "--image_size", str(args.image_size)]
    if args.subtract_mean:
        cmd.append("--subtract_mean")
    if args.use_flipped_images:
        cmd.append("--use_flipped_images")
    if args.use_fixed_image_standardization:
        cmd.append("--use_fixed_image_standardization")
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
