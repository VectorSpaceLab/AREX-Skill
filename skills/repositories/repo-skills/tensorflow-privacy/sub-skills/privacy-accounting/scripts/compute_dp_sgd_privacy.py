#!/usr/bin/env python3
"""Compute a TensorFlow Privacy DP-SGD privacy statement.

This is a small, safe wrapper around the repo's privacy-statement calculator.
It preserves the core flag names and prints the same human-readable statement.

Example:
  python scripts/compute_dp_sgd_privacy.py \
    --N 60000 \
    --batch_size 256 \
    --noise_multiplier 1.1 \
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
  parser.add_argument(
      "--noise_multiplier", type=float, required=True, help="Noise multiplier."
  )
  parser.add_argument("--epochs", type=float, required=True, help="Number of epochs.")
  parser.add_argument("--delta", type=float, default=1e-6, help="Target delta.")
  parser.add_argument(
      "--used_microbatching",
      action=argparse.BooleanOptionalAction,
      default=True,
      help="Whether microbatching was used.",
  )
  parser.add_argument(
      "--max_examples_per_user",
      type=int,
      default=None,
      help="Optional user-level privacy bound.",
  )
  parser.add_argument(
      "--accountant_type",
      choices=("RDP", "PLD"),
      default="RDP",
      help="Privacy accountant to use.",
  )
  args = parser.parse_args()

  _add_repo_root(args.repo_root)

  from tensorflow_privacy.privacy.analysis.compute_dp_sgd_privacy_lib import (  # pylint: disable=import-error
      AccountantType,
      compute_dp_sgd_privacy_statement,
  )

  statement = compute_dp_sgd_privacy_statement(
      args.N,
      args.batch_size,
      args.epochs,
      args.noise_multiplier,
      args.delta,
      args.used_microbatching,
      args.max_examples_per_user,
      AccountantType(args.accountant_type),
  )
  print(statement)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
