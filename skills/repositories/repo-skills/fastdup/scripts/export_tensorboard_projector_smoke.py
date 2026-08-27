#!/usr/bin/env python3
"""Create minimal TensorBoard projector artifacts when TensorFlow is installed.

This script is self-contained because some fastdup wheels do not ship a
`fastdup.tensorboard_projector` module.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
from fastdup.synthetic_image_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny TensorBoard projector smoke test")
    parser.add_argument("--root", required=True, help="Workspace root for images and projector output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    img_dir = root / "images"
    log_dir = root / "tensorboard"
    img_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    if importlib.util.find_spec("tensorflow") is None:
        print("tensorflow_not_installed=1")
        print("skipping projector smoke")
        return 0

    import tensorflow as tf  # type: ignore

    _, valid, *_ = create_synthetic_data(str(img_dir), n_valid=4, n_corrupted=0, n_duplicated=0, n_no_annotation=0, n_no_image=0)
    labels = [str(row["label"]) for _, row in valid.iterrows()]
    features = np.arange(len(labels) * 4, dtype="float32").reshape(len(labels), 4)

    (log_dir / "meta.tsv").write_text("\n".join(labels) + "\n")
    embedding = tf.Variable(features, name="embeddings")
    checkpoint = tf.train.Checkpoint(embedding=embedding)
    checkpoint.write(str(log_dir / "embeddings.ckpt"))

    print(f"log_dir={log_dir}")
    print(f"rows={len(labels)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
