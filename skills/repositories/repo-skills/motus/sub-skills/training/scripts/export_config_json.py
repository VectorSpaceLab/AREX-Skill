#!/usr/bin/env python3
"""Export Motus checkpoint-relevant YAML sections to ``config.json``.

This self-contained helper intentionally does not import Motus or load a
checkpoint. It validates and reads a YAML configuration, then writes the same
filtered sections used by Motus training checkpoint saves:

- common
- model.action_expert
- model.und_expert
- model.time_distribution
- model.ema

It can create ``--ckpt_dir``. That directory creation is the only filesystem
side effect. This is not a model checkpoint writer or a full run-config export.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

try:
    from omegaconf import OmegaConf
except ImportError as exc:  # pragma: no cover - dependency gate
    raise SystemExit(
        "OmegaConf is required. Install the Motus Python requirements in the "
        "active environment before using this helper."
    ) from exc


def filtered_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Return the checkpoint-relevant subset of a resolved config mapping."""
    model = config.get("model", {})
    if not isinstance(model, Mapping):
        raise ValueError("YAML field 'model' must be a mapping when present")
    return {
        "common": config.get("common", {}),
        "action_expert": model.get("action_expert", {}),
        "und_expert": model.get("und_expert", {}),
        "time_distribution": model.get("time_distribution", {}),
        "ema": model.get("ema", {}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export filtered Motus training YAML to config.json in a checkpoint directory. "
            "Does not load model weights."
        )
    )
    parser.add_argument(
        "--yaml",
        required=True,
        type=Path,
        help="Training YAML path (for example, configs/robotwin.yaml).",
    )
    parser.add_argument(
        "--ckpt_dir",
        required=True,
        type=Path,
        help="Existing or new checkpoint directory that will receive config.json.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Explicitly replace an existing config.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.yaml.is_file():
        print(f"ERROR: YAML file not found or not a regular file: {args.yaml}", file=sys.stderr)
        return 2

    try:
        cfg = OmegaConf.load(args.yaml)
        cfg_dict = OmegaConf.to_container(cfg, resolve=True)
    except Exception as exc:
        print(f"ERROR: failed to parse YAML {args.yaml}: {exc}", file=sys.stderr)
        return 2

    if not isinstance(cfg_dict, Mapping):
        print("ERROR: top-level YAML value must be a mapping", file=sys.stderr)
        return 2

    try:
        payload = filtered_config(cfg_dict)
        args.ckpt_dir.mkdir(parents=True, exist_ok=True)
        output_path = args.ckpt_dir / "config.json"
        if output_path.exists() and not args.force:
            print(
                f"ERROR: refusing to replace existing {output_path}; "
                "pass --force only after reviewing the destination",
                file=sys.stderr,
            )
            return 2
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: could not write filtered config: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote filtered config to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
