#!/usr/bin/env python3
"""Run a tiny deterministic smoke test for the DPQuery family.

The smoke uses a Gaussian sum query and a no-privacy sum query on a small
scalar fixture so that both the private and baseline paths are exercised.
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
  args = parser.parse_args()

  _add_repo_root(args.repo_root)

  import tensorflow as tf  # pylint: disable=import-error
  from tensorflow_privacy.privacy.dp_query import gaussian_query
  from tensorflow_privacy.privacy.dp_query import no_privacy_query
  from tensorflow_privacy.privacy.dp_query import test_utils

  records = [tf.constant(0.25, dtype=tf.float32), tf.constant(0.5, dtype=tf.float32)]

  gaussian = gaussian_query.GaussianSumQuery(l2_norm_clip=1.0, stddev=0.0)
  gaussian_result, _ = test_utils.run_query(gaussian, records)

  baseline = no_privacy_query.NoPrivacySumQuery()
  baseline_result, _ = test_utils.run_query(baseline, records)

  print(f"gaussian_result={float(gaussian_result.numpy()):.6f}")
  print(f"baseline_result={float(baseline_result.numpy()):.6f}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
