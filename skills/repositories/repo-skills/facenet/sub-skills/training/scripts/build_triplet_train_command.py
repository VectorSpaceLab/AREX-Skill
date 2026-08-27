#!/usr/bin/env python3
"""Build a Facenet triplet-loss training command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet train_tripletloss command.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--model-def", default="models.inception_resnet_v1")
    parser.add_argument("--logs-base-dir", required=True)
    parser.add_argument("--models-base-dir", required=True)
    parser.add_argument("--max-nrof-epochs", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=90)
    parser.add_argument("--people-per-batch", type=int, default=45)
    parser.add_argument("--images-per-person", type=int, default=40)
    parser.add_argument("--epoch-size", type=int, default=1000)
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--pretrained-model")
    parser.add_argument("--lfw-dir")
    parser.add_argument("--lfw-pairs", default="data/pairs.txt")
    parser.add_argument("--lfw-nrof-folds", type=int, default=10)
    args = parser.parse_args()
    cmd = [
        "python", "-m", "train_tripletloss",
        "--data_dir", args.data_dir,
        "--model_def", args.model_def,
        "--logs_base_dir", args.logs_base_dir,
        "--models_base_dir", args.models_base_dir,
        "--max_nrof_epochs", str(args.max_nrof_epochs),
        "--batch_size", str(args.batch_size),
        "--people_per_batch", str(args.people_per_batch),
        "--images_per_person", str(args.images_per_person),
        "--epoch_size", str(args.epoch_size),
        "--alpha", str(args.alpha),
        "--image_size", str(args.image_size),
        "--lfw_pairs", args.lfw_pairs,
        "--lfw_nrof_folds", str(args.lfw_nrof_folds),
    ]
    if args.pretrained_model:
        cmd.extend(["--pretrained_model", args.pretrained_model])
    if args.lfw_dir:
        cmd.extend(["--lfw_dir", args.lfw_dir])
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
