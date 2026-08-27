#!/usr/bin/env python3
"""Inspect a Facenet model directory for checkpoint and meta files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Facenet model directory.")
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = sorted(p.name for p in args.model_dir.iterdir()) if args.model_dir.exists() else []
    meta_files = [name for name in files if name.endswith(".meta")]
    ckpt_files = [name for name in files if ".ckpt" in name]
    checkpoint_state = args.model_dir / "checkpoint"
    payload = {
        "exists": args.model_dir.exists(),
        "model_dir": str(args.model_dir),
        "meta_files": meta_files,
        "checkpoint_files": ckpt_files,
        "has_checkpoint_state": checkpoint_state.exists(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"exists={payload['exists']} meta={len(meta_files)} ckpt={len(ckpt_files)} checkpoint_state={payload['has_checkpoint_state']}")
        for name in meta_files:
            print(f"META {name}")
        for name in ckpt_files[:20]:
            print(f"CKPT {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
