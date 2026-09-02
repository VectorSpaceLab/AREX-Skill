#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

try:
    from pairwise_loss import pairwise_kl_loss
except Exception:
    pairwise_kl_loss = None


def _shape(x: Any) -> list[int]:
    shape = []
    while isinstance(x, list):
        shape.append(len(x))
        x = x[0] if x else []
    return shape


def haar_high_frequency(images: list) -> list:
    shape = _shape(images)
    if len(shape) != 4:
        raise ValueError("images must have shape [batch, channels, height, width]")
    batch, channels, height, width = shape
    if height % 2 or width % 2:
        raise ValueError("height and width must be even")
    out = []
    for b in range(batch):
        sample = []
        for c in range(channels):
            channel = []
            for y in range(0, height, 2):
                row = []
                for x in range(0, width, 2):
                    a = float(images[b][c][y][x])
                    b01 = float(images[b][c][y][x + 1])
                    c10 = float(images[b][c][y + 1][x])
                    d = float(images[b][c][y + 1][x + 1])
                    lh = (a - b01 + c10 - d) / 2.0
                    hl = (a + b01 - c10 - d) / 2.0
                    hh = (a - b01 - c10 + d) / 2.0
                    row.append(lh + hl + hh)
                channel.append(row)
            sample.append(channel)
        out.append(sample)
    return out


def flatten(x: Any) -> list[float]:
    if isinstance(x, list):
        result = []
        for item in x:
            result.extend(flatten(item))
        return result
    return [float(x)]


def mse(a: Any, b: Any) -> float:
    av = flatten(a)
    bv = flatten(b)
    if len(av) != len(bv):
        raise ValueError("shape mismatch")
    return sum((x - y) ** 2 for x, y in zip(av, bv)) / len(av)


def energy(x: Any) -> float:
    vals = flatten(x)
    return sum(v * v for v in vals) / len(vals)


def high_frequency_losses(source_images: list, adapted_images: list, target_images: list) -> dict:
    source_hf = haar_high_frequency(source_images)
    adapted_hf = haar_high_frequency(adapted_images)
    target_hf = haar_high_frequency(target_images)
    if pairwise_kl_loss is None:
        lhf = 0.0 if source_hf == adapted_hf else mse(source_hf, adapted_hf)
    else:
        lhf = pairwise_kl_loss(source_hf, adapted_hf)["loss"]
    return {
        "source_hf": source_hf,
        "adapted_hf": adapted_hf,
        "target_hf": target_hf,
        "Lhf": lhf,
        "Lhfmse": mse(adapted_hf, target_hf),
        "energy": {"source": energy(source_hf), "adapted": energy(adapted_hf), "target": energy(target_hf)},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        img = [[[[1.0, -1.0], [-1.0, 1.0]]], [[[0.5, -0.5], [-0.5, 0.5]]]]
        print(json.dumps(high_frequency_losses(img, img, img), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
