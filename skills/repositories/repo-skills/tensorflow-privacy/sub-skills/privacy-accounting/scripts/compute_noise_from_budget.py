#!/usr/bin/env python3
"""Compute a TensorFlow Privacy noise multiplier from a target epsilon.

This is a small wrapper around the inverse privacy-accounting helper.

Example:
  python scripts/compute_noise_from_budget.py \
    --N 60000 \
    --batch_size 256 \
    --epsilon 2.92 \
    --epochs 60 \
    --delta 1e-5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _add_repo_root(repo_root: str | None) -> None:
  if repo_root:
    path = str(Path(repo_root).resolve())
    if path not in sys.path:
      sys.path.insert(0, path)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--repo-root", help="Optional local checkout to import from.")
  parser.add_argument("--N", type=int, required=True, help="Total number of examples.")
  parser.add_argument("--batch_size", type=int, required=True, help="Batch size.")
  parser.add_argument("--epsilon", type=float, required=True, help="Target epsilon.")
  parser.add_argument("--epochs", type=float, required=True, help="Number of epochs.")
  parser.add_argument("--delta", type=float, default=1e-6, help="Target delta.")
  parser.add_argument(
      "--min_noise",
      type=float,
      default=1e-5,
      help="Minimum noise level for the search.",
  )
  args = parser.parse_args()

  _add_repo_root(args.repo_root)

  from tensorflow_privacy.privacy.analysis.compute_noise_from_budget_lib import (  # pylint: disable=import-error
      compute_noise,
  )

  noise_multiplier = compute_noise(
      args.N,
      args.batch_size,
      args.epsilon,
      args.epochs,
      args.delta,
      args.min_noise,
  )
  print(f"noise_multiplier={noise_multiplier}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
