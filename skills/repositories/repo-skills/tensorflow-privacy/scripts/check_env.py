#!/usr/bin/env python3
"""Check that TensorFlow Privacy imports from the intended environment.

This helper is safe to run from any working directory. It optionally accepts a
local checkout root for development use, but by default it only inspects the
installed package set.

Example:
  python scripts/check_env.py
  python scripts/check_env.py --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import sys
from importlib import metadata
from pathlib import Path


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
  import tensorflow_privacy  # pylint: disable=import-error

  print(f"tensorflow={tf.__version__}")
  print(f"tensorflow_privacy={metadata.version('tensorflow_privacy')}")
  print(f"tensorflow_privacy_file={tensorflow_privacy.__file__}")
  print("cpu_devices=", tf.config.list_physical_devices("CPU"))
  print("gpu_devices=", tf.config.list_physical_devices("GPU"))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
