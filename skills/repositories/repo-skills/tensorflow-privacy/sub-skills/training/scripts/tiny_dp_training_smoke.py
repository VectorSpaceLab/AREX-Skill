#!/usr/bin/env python3
"""Train a tiny synthetic classifier with a DP Keras optimizer.

This script is safe and deterministic. It uses a tiny synthetic dataset and a
single short fit call to prove that the DP training path is working.

Example:
  python scripts/tiny_dp_training_smoke.py
  python scripts/tiny_dp_training_smoke.py --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def _add_repo_root(repo_root: str | None) -> None:
  if repo_root:
    path = str(Path(repo_root).resolve())
    if path not in sys.path:
      sys.path.insert(0, path)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "--repo-root",
      help="Optional local checkout to prepend to sys.path for development checks.",
  )
  args = parser.parse_args()

  _add_repo_root(args.repo_root)

  import tensorflow as tf  # pylint: disable=import-error
  from tensorflow_privacy.privacy.optimizers.dp_optimizer_keras import DPKerasSGDOptimizer

  tf.random.set_seed(7)
  np.random.seed(7)

  model = tf.keras.Sequential([
      tf.keras.layers.Input(shape=(2,)),
      tf.keras.layers.Dense(2, activation="softmax"),
  ])
  optimizer = DPKerasSGDOptimizer(
      l2_norm_clip=1.0,
      noise_multiplier=0.0,
      num_microbatches=1,
      learning_rate=0.1,
  )
  loss = tf.keras.losses.SparseCategoricalCrossentropy(
      reduction=tf.keras.losses.Reduction.NONE
  )
  model.compile(optimizer=optimizer, loss=loss)

  x = np.array(
      [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype=np.float32
  )
  y = np.array([0, 1, 1, 0], dtype=np.int32)
  history = model.fit(x, y, epochs=1, batch_size=2, verbose=0)
  print(f"final_loss={history.history['loss'][-1]:.6f}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
