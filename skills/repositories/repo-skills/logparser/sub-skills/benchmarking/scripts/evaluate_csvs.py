#!/usr/bin/env python
"""Evaluate a parsed CSV against ground truth.

This is a safe wrapper around `logparser.utils.evaluator.evaluate`.
It prints the metric pair returned by the repository evaluator.

Example:
    python scripts/evaluate_csvs.py --groundtruth GT.csv --parsed OUT.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys



def _bootstrap_repo_root() -> None:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "setup.py").exists() and (candidate / "logparser").is_dir():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Could not locate the repository root for Logparser")

_bootstrap_repo_root()

from logparser.utils import evaluator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groundtruth", type=Path, required=True, help="ground-truth structured CSV")
    parser.add_argument("--parsed", type=Path, required=True, help="parsed structured CSV")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    f_measure, accuracy = evaluator.evaluate(str(args.groundtruth), str(args.parsed))
    print(f"F1_measure={f_measure:.6f}")
    print(f"Accuracy={accuracy:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
