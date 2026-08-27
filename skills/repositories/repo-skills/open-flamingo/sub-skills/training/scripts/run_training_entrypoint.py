#!/usr/bin/env python3
"""Run OpenFlamingo's installed training entrypoint with import-path fixes.

This wrapper is bundled with the skill so future agents do not need to know a
source-checkout-relative `open_flamingo/train/train.py` path. It locates the
installed `open_flamingo` package, adds the package and train directories to
`sys.path` to satisfy the repository's unqualified local imports, then executes
its packaged `train.py` as `__main__`.

Example:
    python scripts/run_training_entrypoint.py --help
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path


def main() -> int:
    spec = importlib.util.find_spec("open_flamingo")
    if spec is None or spec.origin is None:
        raise SystemExit(
            "Cannot find installed package `open_flamingo`. Install OpenFlamingo before using this wrapper."
        )
    package_dir = Path(spec.origin).resolve().parent
    train_dir = package_dir / "train"
    entrypoint = train_dir / "train.py"
    if not entrypoint.exists():
        raise SystemExit(
            "Installed OpenFlamingo package does not include train/train.py; use a source checkout or refresh this skill."
        )
    for path in (str(package_dir), str(train_dir)):
        if path not in sys.path:
            sys.path.insert(0, path)
    sys.argv[0] = str(entrypoint)
    runpy.run_path(str(entrypoint), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
