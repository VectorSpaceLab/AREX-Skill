#!/usr/bin/env python3
"""Run a tiny deterministic secret-sharer smoke test."""

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

  from tensorflow_privacy.privacy.privacy_tests.secret_sharer import exposures
  from tensorflow_privacy.privacy.privacy_tests.secret_sharer import generate_secrets

  properties = generate_secrets.TextSecretProperties(vocab=["a", "b"], pattern="{}{}")
  config = generate_secrets.SecretConfig(
      num_repetitions=[1, 2],
      num_secrets_for_repetitions=[1, 1],
      num_references=2,
      name="toy",
      properties=properties,
  )
  secrets_set = generate_secrets.generate_text_secrets_and_references([config], seed=3)[0]
  dataset = generate_secrets.construct_secret_dataset([secrets_set])
  exposure = exposures.compute_exposure_interpolation(
      {"toy": [1.0, 1.1]},
      [0.25, 0.5, 0.75],
  )
  print(f"secret_dataset_size={len(dataset)}")
  print(f"reference_count={len(secrets_set.references)}")
  print(f"exposure={exposure['toy'].tolist()}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
