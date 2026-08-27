#!/usr/bin/env python3
"""Build a Facenet softmax training command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet train_softmax command.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--model-def", default="models.inception_resnet_v1")
    parser.add_argument("--logs-base-dir", required=True)
    parser.add_argument("--models-base-dir", required=True)
    parser.add_argument("--max-nrof-epochs", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=90)
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--epoch-size", type=int, default=1000)
    parser.add_argument("--use-fixed-image-standardization", action="store_true")
    parser.add_argument("--center-loss-factor", type=float, default=0.0)
    parser.add_argument("--prelogits-norm-loss-factor", type=float, default=0.0)
    parser.add_argument("--pretrained-model")
    parser.add_argument("--lfw-dir")
    parser.add_argument("--lfw-pairs", default="data/pairs.txt")
    parser.add_argument("--lfw-batch-size", type=int, default=100)
    parser.add_argument("--lfw-nrof-folds", type=int, default=10)
    args = parser.parse_args()
    cmd = [
        "python", "-m", "train_softmax",
        "--data_dir", args.data_dir,
        "--model_def", args.model_def,
        "--logs_base_dir", args.logs_base_dir,
        "--models_base_dir", args.models_base_dir,
        "--max_nrof_epochs", str(args.max_nrof_epochs),
        "--batch_size", str(args.batch_size),
        "--image_size", str(args.image_size),
        "--epoch_size", str(args.epoch_size),
        "--center_loss_factor", str(args.center_loss_factor),
        "--prelogits_norm_loss_factor", str(args.prelogits_norm_loss_factor),
        "--lfw_pairs", args.lfw_pairs,
        "--lfw_batch_size", str(args.lfw_batch_size),
        "--lfw_nrof_folds", str(args.lfw_nrof_folds),
    ]
    if args.use_fixed_image_standardization:
        cmd.append("--use_fixed_image_standardization")
    if args.pretrained_model:
        cmd.extend(["--pretrained_model", args.pretrained_model])
    if args.lfw_dir:
        cmd.extend(["--lfw_dir", args.lfw_dir])
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
