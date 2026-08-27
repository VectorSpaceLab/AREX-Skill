#!/usr/bin/env python3
"""Run a tiny deterministic smoke test for fast clipping helpers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import tensorflow as tf


def _add_repo_root(repo_root: str | None) -> None:
  if repo_root:
    path = str(Path(repo_root).resolve())
    if path not in sys.path:
      sys.path.insert(0, path)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--repo-root", help="Optional local checkout to import from.")
  args = parser.parse_args()

  _add_repo_root(args.repo_root)

  from tensorflow_privacy.privacy.fast_gradient_clipping import clip_grads
  from tensorflow_privacy.privacy.fast_gradient_clipping import gradient_clipping_utils
  from tensorflow_privacy.privacy.fast_gradient_clipping import layer_registry
  from tensorflow_privacy.privacy.fast_gradient_clipping import noise_utils

  model = tf.keras.Sequential([
      tf.keras.layers.Input(shape=(2,)),
      tf.keras.layers.Dense(1),
  ])
  registry = layer_registry.make_default_layer_registry()
  registry_ok = gradient_clipping_utils.all_trainable_layers_are_registered(
      model, registry
  )
  clip_weights = clip_grads.compute_clip_weights(
      1.0, tf.constant([0.5, 2.0], dtype=tf.float32)
  )
  noisy_grads = noise_utils.add_aggregate_noise(
      clipped_grads=[tf.constant([[0.2, -0.2], [0.1, 0.0]], dtype=tf.float32)],
      batch_size=tf.constant(2),
      l2_norm_clip=1.0,
      noise_multiplier=0.0,
      loss_reduction='mean',
  )[0]

  print(f"registry_ok={registry_ok}")
  print(f"clip_weights={clip_weights.numpy().tolist()}")
  print(f"noisy_grads={noisy_grads.numpy().tolist()}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
