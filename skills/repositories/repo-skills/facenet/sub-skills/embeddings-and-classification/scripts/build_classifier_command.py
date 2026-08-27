#!/usr/bin/env python3
"""Build a Facenet SVM classifier TRAIN or CLASSIFY command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet classifier command.")
    parser.add_argument("mode", choices=["TRAIN", "CLASSIFY"])
    parser.add_argument("data_dir")
    parser.add_argument("model")
    parser.add_argument("classifier_filename")
    parser.add_argument("--use-split-dataset", action="store_true")
    parser.add_argument("--batch-size", type=int, default=90)
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--min-images-per-class", type=int, default=20)
    parser.add_argument("--train-images-per-class", type=int, default=10)
    args = parser.parse_args()
    cmd = ["python", "-m", "classifier", args.mode, args.data_dir, args.model, args.classifier_filename, "--batch_size", str(args.batch_size), "--image_size", str(args.image_size), "--min_nrof_images_per_class", str(args.min_images_per_class), "--nrof_train_images_per_class", str(args.train_images_per_class)]
    if args.use_split_dataset:
        cmd.append("--use_split_dataset")
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
