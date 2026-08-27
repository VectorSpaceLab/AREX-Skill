#!/usr/bin/env python3
"""Create a small deterministic MDT-like 2D fixture without importing MDT.

The helper writes image/segmentation pairs as NumPy arrays and a JSON manifest.
It never overwrites a non-empty output directory and caps all sizes/counts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--train-count", type=int, default=2)
    p.add_argument("--test-count", type=int, default=1)
    p.add_argument("--height", type=int, default=32)
    p.add_argument("--width", type=int, default=32)
    p.add_argument("--seed", type=int, default=0)
    return p.parse_args()


def make_case(rng: np.random.Generator, shape: tuple[int, int], case_id: int) -> np.ndarray:
    h, w = shape
    image = rng.normal(0.0, 0.1, size=shape).astype(np.float32)
    seg = np.zeros(shape, dtype=np.uint8)
    radius = max(2, min(h, w) // 8)
    cy = h // 2 + (case_id % 3 - 1) * max(1, h // 8)
    cx = w // 2 + ((case_id * 2) % 3 - 1) * max(1, w // 8)
    yy, xx = np.ogrid[:h, :w]
    mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= radius**2
    image[mask] += 1.0
    seg[mask] = 1
    return np.stack([image, seg], axis=0)


def main() -> int:
    args = parse_args()
    if not (0 < args.train_count <= 32 and 0 < args.test_count <= 32):
        raise SystemExit("train/test counts must be between 1 and 32")
    if not (8 <= args.height <= 256 and 8 <= args.width <= 256):
        raise SystemExit("height/width must be between 8 and 256")
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    records = []
    for split, count in (("train", args.train_count), ("test", args.test_count)):
        split_dir = out / split
        split_dir.mkdir()
        for i in range(count):
            rel = Path(split) / f"case_{i:04d}.npy"
            np.save(out / rel, make_case(rng, (args.height, args.width), i))
            records.append({"split": split, "case_id": f"case_{i:04d}", "path": rel.as_posix(), "shape": [2, args.height, args.width]})
    (out / "manifest.json").write_text(json.dumps({"format": "mdt-toy-fixture-v1", "records": records}, indent=2) + "\n")
    print(json.dumps({"output_dir": str(out), "records": len(records), "manifest": "manifest.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
