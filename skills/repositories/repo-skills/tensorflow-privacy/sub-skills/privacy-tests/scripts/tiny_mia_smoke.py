#!/usr/bin/env python3
"""Run a tiny deterministic membership-inference smoke test."""

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
  parser.add_argument("--repo-root", help="Optional local checkout to import from.")
  args = parser.parse_args()

  _add_repo_root(args.repo_root)

  from tensorflow_privacy.privacy.privacy_tests.membership_inference_attack import (
      data_structures,
      membership_inference_attack,
  )

  attack_input = data_structures.AttackInputData(
      loss_train=np.array([0.05, 0.08, 0.12, 0.15], dtype=np.float32),
      loss_test=np.array([0.40, 0.44, 0.48, 0.52], dtype=np.float32),
  )
  result = membership_inference_attack.run_attacks(
      attack_input=attack_input,
      attack_types=(data_structures.AttackType.THRESHOLD_ATTACK,),
  )
  print(result.summary())
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
