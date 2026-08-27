#!/usr/bin/env python3
"""Validate an image-model checkpoint directory.

This helper checks the file layout expected by the Lumina image inference
routes without downloading weights or running sampling.

Examples:
    python check_checkpoints.py --family lumina --checkpoint-dir /path/to/ckpt
    python check_checkpoints.py --family mini --checkpoint-dir /path/to/ckpt --expect-format pth
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch


FAMILY_LABELS = {
    "lumina": "Lumina-T2I",
    "lumina_next": "Lumina-Next-T2I",
    "mini": "Lumina-Next-T2I-Mini / SD3",
    "compositional": "Lumina-Next-T2I Compositional",
}


def find_weight_files(checkpoint_dir: Path) -> list[Path]:
    files = []
    files.extend(sorted(checkpoint_dir.glob("consolidated*.pth")))
    files.extend(sorted(checkpoint_dir.glob("consolidated*.safetensors")))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=sorted(FAMILY_LABELS), default="lumina")
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--expect-format", choices=["auto", "pth", "safetensors"], default="auto")
    parser.add_argument("--require-ema", action="store_true", help="Require an EMA checkpoint variant.")
    args = parser.parse_args()

    ckpt = args.checkpoint_dir.resolve()
    ok = True
    print(f"family={FAMILY_LABELS[args.family]}")
    print(f"checkpoint_dir={ckpt}")

    if not ckpt.exists():
        print("FAIL: checkpoint directory does not exist")
        return 1
    if not ckpt.is_dir():
        print("FAIL: checkpoint path is not a directory")
        return 1

    model_args = ckpt / "model_args.pth"
    if not model_args.exists():
        print("FAIL: missing model_args.pth")
        ok = False
    else:
        try:
            loaded = torch.load(model_args, map_location="cpu")
            keys = sorted(getattr(loaded, "__dict__", {}).keys())
            print(f"model_args=OK keys={keys[:12]}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: could not read model_args.pth ({type(exc).__name__}: {exc})")
            ok = False

    weights = find_weight_files(ckpt)
    if not weights:
        print("FAIL: no consolidated*.pth or consolidated*.safetensors files found")
        ok = False
    else:
        print("weights=OK")
        for weight in weights[:6]:
            print(f"  - {weight.name}")

    if args.expect_format != "auto":
        suffix = ".pth" if args.expect_format == "pth" else ".safetensors"
        matching = [path for path in weights if path.suffix == suffix]
        if not matching:
            print(f"FAIL: no weights with suffix {suffix}")
            ok = False

    if args.require_ema:
        ema = [p for p in weights if "ema" in p.name]
        if not ema:
            print("FAIL: no EMA checkpoint variant found")
            ok = False

    if ok:
        print("Result: checkpoint layout looks ready for image inference.")
        return 0

    print("Result: checkpoint layout is incomplete.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
