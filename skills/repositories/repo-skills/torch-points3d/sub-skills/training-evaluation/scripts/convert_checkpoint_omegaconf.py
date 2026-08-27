#!/usr/bin/env python3
"""Convert OmegaConf containers inside a Torch Points3D checkpoint copy.

The original repository helper was intended for old OmegaConf checkpoints. This
safer variant requires an explicit output path, optionally writes a backup, and
does not modify the input file unless `--in-place` is requested.

Examples:
  python sub-skills/training-evaluation/scripts/convert_checkpoint_omegaconf.py \
    --input run/model.pt --output run/model-converted.pt
  python sub-skills/training-evaluation/scripts/convert_checkpoint_omegaconf.py \
    --input run/model.pt --in-place --backup run/model-before-convert.pt
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any, Iterable, Set


def convert_value(value: Any, exclude_keys: Set[str]) -> Any:
    from omegaconf import DictConfig, ListConfig, OmegaConf

    if isinstance(value, DictConfig):
        return convert_value(OmegaConf.to_container(value, resolve=False), exclude_keys)
    if isinstance(value, ListConfig):
        return convert_value(OmegaConf.to_container(value, resolve=False), exclude_keys)
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if str(key) in exclude_keys:
                out[key] = item
            else:
                out[key] = convert_value(item, exclude_keys)
        return out
    if isinstance(value, list):
        return [convert_value(item, exclude_keys) for item in value]
    if isinstance(value, tuple):
        return tuple(convert_value(item, exclude_keys) for item in value)
    return value


def parse_exclude(raw: Iterable[str]) -> Set[str]:
    result: Set[str] = set()
    for item in raw:
        result.update(part.strip() for part in item.split(",") if part.strip())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert OmegaConf containers in a Torch Points3D checkpoint.")
    parser.add_argument("--input", required=True, type=Path, help="Input .pt checkpoint.")
    parser.add_argument("--output", type=Path, help="Output .pt checkpoint. Required unless --in-place is used.")
    parser.add_argument("--in-place", action="store_true", help="Overwrite --input after optional backup.")
    parser.add_argument("--backup", type=Path, help="Optional backup path written before conversion.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing --output file.")
    parser.add_argument("--exclude-key", action="append", default=["models", "optimizer"], help="Top-level/nested key to leave unchanged; may be repeated or comma-separated.")
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"input checkpoint does not exist: {args.input}")
    if args.in_place and args.output:
        raise SystemExit("use either --in-place or --output, not both")
    if not args.in_place and not args.output:
        raise SystemExit("provide --output or --in-place")

    target = args.input if args.in_place else args.output
    assert target is not None
    if target.exists() and target != args.input and not args.overwrite:
        raise SystemExit(f"output already exists (use --overwrite to replace): {target}")

    try:
        import torch
        import omegaconf  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Required import failed: {type(exc).__name__}: {exc}")

    if args.backup:
        if args.backup.exists() and not args.overwrite:
            raise SystemExit(f"backup already exists (use --overwrite to replace): {args.backup}")
        shutil.copy2(args.input, args.backup)

    checkpoint = torch.load(args.input, map_location="cpu")
    converted = convert_value(checkpoint, parse_exclude(args.exclude_key))
    torch.save(converted, target)
    print(f"Wrote converted checkpoint: {target}")
    if args.backup:
        print(f"Backup: {args.backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
