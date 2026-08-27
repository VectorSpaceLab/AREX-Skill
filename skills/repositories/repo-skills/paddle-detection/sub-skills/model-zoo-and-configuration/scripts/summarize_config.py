#!/usr/bin/env python3
"""Summarize a PaddleDetection YAML config from a user-provided checkout.

This helper is read-only. It loads the config with ppdet, prints the merged
high-value fields, and exits non-zero if the config cannot be loaded.

Example:
  python summarize_config.py --repo-root /path/to/PaddleDetection \
    --config configs/ppyoloe/ppyoloe_crn_s_300e_coco.yml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a PaddleDetection config.")
    parser.add_argument("--repo-root", required=True, help="Path to a PaddleDetection checkout.")
    parser.add_argument("--config", required=True, help="Config path relative to repo-root or an absolute path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root does not exist: {repo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))

    try:
        from ppdet.core.workspace import load_config
    except Exception as exc:
        print(f"ERROR: failed to import ppdet: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = repo_root / cfg_path
    if not cfg_path.exists():
        print(f"ERROR: config does not exist: {cfg_path}", file=sys.stderr)
        return 4

    try:
        cfg = load_config(str(cfg_path))
    except Exception as exc:
        print(f"ERROR: could not load config: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5

    summary = {
        "filename": getattr(cfg, "filename", None),
        "architecture": getattr(cfg, "architecture", None),
        "metric": getattr(cfg, "metric", None),
        "num_classes": getattr(cfg, "num_classes", None),
        "save_dir": getattr(cfg, "save_dir", None),
        "train_dataset": type(cfg.get("TrainDataset")) if hasattr(cfg, "get") else None,
        "eval_dataset": type(cfg.get("EvalDataset")) if hasattr(cfg, "get") else None,
        "test_dataset": type(cfg.get("TestDataset")) if hasattr(cfg, "get") else None,
    }

    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
