#!/usr/bin/env python3
"""Score TuSimple prediction JSONL files with the repo's benchmark helper.

This wrapper adds an explicit --repo-root argument so it can be run from any
working directory.

Example:
    python score_tusimple_json.py --repo-root . --pred-file preds.txt --gt-file test_label.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score TuSimple JSONL predictions.")
    parser.add_argument("--repo-root", required=True, help="Path to the Ultra-Fast-Lane-Detection checkout")
    parser.add_argument("--pred-file", required=True, help="Prediction JSONL file")
    parser.add_argument("--gt-file", required=True, help="TuSimple ground-truth JSONL file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    from evaluation.tusimple.lane import LaneEval  # noqa: WPS433

    result = LaneEval.bench_one_submit(args.pred_file, args.gt_file)
    print(json.dumps(json.loads(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
