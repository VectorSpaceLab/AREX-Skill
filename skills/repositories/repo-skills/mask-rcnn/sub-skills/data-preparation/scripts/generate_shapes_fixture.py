#!/usr/bin/env python3
"""Generate a tiny Shapes-style fixture for Mask_RCNN data pipeline examples.

The output is a JSON metadata file and optional PNG image/mask files. It avoids
any dependency on the original repository checkout.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np


def draw_shape(image: np.ndarray, shape: str, dims, color) -> np.ndarray:
    x, y, s = dims
    yy, xx = np.ogrid[: image.shape[0], : image.shape[1]]
    if shape == "circle":
        mask = (xx - x) ** 2 + (yy - y) ** 2 <= s ** 2
    elif shape == "square":
        mask = (np.abs(xx - x) <= s) & (np.abs(yy - y) <= s)
    elif shape == "triangle":
        # Simple upright triangle using barycentric-like half-plane tests.
        h = int(round(s * math.sqrt(3)))
        y_top = max(0, y - h // 2)
        y_bottom = min(image.shape[0] - 1, y + h // 2)
        mask = np.zeros(image.shape[:2], dtype=bool)
        for row in range(y_top, y_bottom + 1):
            frac = (row - y_top) / max(1, (y_bottom - y_top))
            half_width = int(round(s * frac))
            x1 = max(0, x - half_width)
            x2 = min(image.shape[1], x + half_width + 1)
            mask[row, x1:x2] = True
    else:
        raise ValueError(shape)
    image[mask] = color
    return image


def make_fixture(count: int, height: int, width: int, seed: int):
    rng = random.Random(seed)
    records = []
    for image_id in range(count):
        bg = np.array([rng.randint(0, 255) for _ in range(3)], dtype=np.uint8)
        image = np.ones((height, width, 3), dtype=np.uint8) * bg
        specs = []
        masks = []
        for _ in range(rng.randint(1, 4)):
            shape = rng.choice(["square", "circle", "triangle"])
            color = [rng.randint(0, 255) for _ in range(3)]
            buffer = max(8, min(height, width) // 8)
            x = rng.randint(buffer, width - buffer - 1)
            y = rng.randint(buffer, height - buffer - 1)
            s = rng.randint(max(5, buffer // 2), max(6, min(height, width) // 5))
            before = image.copy()
            image = draw_shape(image, shape, (x, y, s), color)
            mask = np.any(image != before, axis=-1).astype(np.uint8)
            specs.append({"shape": shape, "color": color, "dims": [x, y, s]})
            masks.append(mask)
        stacked = np.stack(masks, axis=-1) if masks else np.zeros((height, width, 0), dtype=np.uint8)
        records.append({"image_id": image_id, "image": image, "mask": stacked, "specs": specs, "bg_color": bg.tolist()})
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a tiny Shapes-style fixture.")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--height", type=int, default=128)
    ap.add_argument("--width", type=int, default=128)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--write-npy", action="store_true", help="Also write image_N.npy and mask_N.npy arrays.")
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = make_fixture(args.count, args.height, args.width, args.seed)
    manifest = []
    for rec in records:
        entry = {
            "image_id": rec["image_id"],
            "height": args.height,
            "width": args.width,
            "bg_color": rec["bg_color"],
            "shapes": rec["specs"],
            "mask_shape": list(rec["mask"].shape),
        }
        if args.write_npy:
            image_name = f"image_{rec['image_id']}.npy"
            mask_name = f"mask_{rec['image_id']}.npy"
            np.save(args.output_dir / image_name, rec["image"])
            np.save(args.output_dir / mask_name, rec["mask"])
            entry["image_npy"] = image_name
            entry["mask_npy"] = mask_name
        manifest.append(entry)
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"wrote {len(manifest)} records to {args.output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
