#!/usr/bin/env python3
"""Inspect a PaddleOCR-style YAML config without launching training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


_INTERESTING_SECTIONS = ["Global", "Architecture", "Train", "Eval", "Optimizer"]


def _to_builtin(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_builtin(v) for v in obj]
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a PaddleOCR training/export YAML config."
    )
    parser.add_argument("config", help="Path to a PaddleOCR-style YAML config.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    parser.add_argument(
        "--mode",
        choices=["train", "eval", "export"],
        default=None,
        help="Print a command suggestion for the chosen workflow.",
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="Optional checkpoint path for eval/export command suggestions.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    summary = {
        "config": str(config_path),
        "top_level_keys": list(data.keys()) if isinstance(data, dict) else None,
        "sections": {
            key: _to_builtin(data[key])
            for key in _INTERESTING_SECTIONS
            if isinstance(data, dict) and key in data
        },
    }

    if args.mode is not None:
        summary["workflow_recommendation"] = args.mode
        summary["next_step"] = (
            "Read the training-and-export reference for the exact source command shape."
        )
        if args.checkpoint:
            summary["checkpoint"] = args.checkpoint

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"config: {summary['config']}")
        print(f"top-level keys: {summary['top_level_keys']}")
        for key, value in summary["sections"].items():
            print(f"[{key}] {value}")
        if "workflow_recommendation" in summary:
            print(f"workflow recommendation: {summary['workflow_recommendation']}")
            print(summary["next_step"])
            if "checkpoint" in summary:
                print(f"checkpoint: {summary['checkpoint']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
