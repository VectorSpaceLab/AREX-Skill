#!/usr/bin/env python3
"""Summarize and sanity-check a pix2tex YAML config without training."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

REQUIRED = [
    "data", "valdata", "tokenizer", "model_path", "name", "epochs", "batchsize",
    "max_width", "max_height", "min_width", "min_height", "channels", "patch_size",
    "dim", "encoder_depth", "num_layers", "heads", "num_tokens", "max_seq_len",
    "encoder_structure", "pad_token", "bos_token", "eos_token",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a pix2tex training/evaluation config")
    parser.add_argument("config", type=Path)
    parser.add_argument("--base-dir", type=Path, default=None, help="base directory for checking relative data/tokenizer paths")
    args = parser.parse_args()

    data = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    base = args.base_dir or args.config.parent
    report = {
        "config": str(args.config),
        "missing_required_keys": [k for k in REQUIRED if k not in data],
        "encoder_structure": data.get("encoder_structure"),
        "image_bounds": {
            "max_width": data.get("max_width"),
            "max_height": data.get("max_height"),
            "min_width": data.get("min_width"),
            "min_height": data.get("min_height"),
        },
        "training": {k: data.get(k) for k in ["epochs", "batchsize", "micro_batchsize", "lr", "optimizer", "scheduler", "wandb", "debug"]},
        "paths": {},
        "warnings": [],
    }
    for key in ["data", "valdata", "tokenizer", "load_chkpt"]:
        value = data.get(key)
        if value in (None, ""):
            report["paths"][key] = {"value": value, "exists": None}
            continue
        p = Path(value)
        check = p if p.is_absolute() else base / p
        report["paths"][key] = {"value": value, "checked_path": str(check), "exists": check.exists()}
    if data.get("patch_size") and data.get("max_width") and data["max_width"] % data["patch_size"] != 0:
        report["warnings"].append("max_width is not divisible by patch_size")
    if data.get("patch_size") and data.get("max_height") and data["max_height"] % data["patch_size"] != 0:
        report["warnings"].append("max_height is not divisible by patch_size")
    if data.get("encoder_structure") not in {"hybrid", "vit"}:
        report["warnings"].append("encoder_structure is not one of the known values: hybrid, vit")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["missing_required_keys"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
