#!/usr/bin/env python3
"""Encode or decode nucleus-style RLE masks.

Examples:
  python rle_tools.py encode --mask mask.npy --image-id SAMPLE
  python rle_tools.py decode --rle "1 3 10 2" --shape 256 256

This helper follows the Mask_RCNN nucleus sample convention: column-major
flattening, one-based runs, and [H, W, instances] stacks for encoding.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def rle_encode(mask: np.ndarray) -> str:
    if mask.ndim != 2:
        raise ValueError("mask must be 2D")
    pixels = mask.T.flatten()
    padded = np.concatenate([[0], pixels, [0]])
    changes = np.diff(padded)
    runs = np.where(changes != 0)[0].reshape(-1, 2) + 1
    runs[:, 1] = runs[:, 1] - runs[:, 0]
    return " ".join(map(str, runs.flatten()))


def rle_decode(rle: str, shape: tuple[int, int]) -> np.ndarray:
    entries = [int(x) for x in rle.split()]
    arr = np.array(entries, dtype=np.int32).reshape(-1, 2)
    arr[:, 1] += arr[:, 0]
    arr -= 1
    mask = np.zeros(shape[0] * shape[1], dtype=np.bool_)
    for start, end in arr:
        mask[start:end] = True
    return mask.reshape((shape[1], shape[0])).T


def encode_instances(image_id: str, mask: np.ndarray, scores: np.ndarray) -> str:
    if mask.ndim != 3:
        raise ValueError("mask must be [H, W, N]")
    if mask.shape[-1] == 0:
        return f"{image_id},"
    order = np.argsort(scores)[::-1] + 1
    stacked = np.max(mask * order.reshape(1, 1, -1), axis=-1)
    lines = []
    for o in order:
        single = np.where(stacked == o, 1, 0)
        if single.sum() == 0:
            continue
        lines.append(f"{image_id}, {rle_encode(single)}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Encode or decode nucleus-style RLE masks.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="Encode a mask stack to submission text.")
    enc.add_argument("--image-id", required=True)
    enc.add_argument("--mask", type=Path, required=True, help=".npy mask stack [H, W, N].")
    enc.add_argument("--scores", type=Path, required=True, help=".npy score vector [N].")

    dec = sub.add_parser("decode", help="Decode one RLE string to a boolean mask.")
    dec.add_argument("--rle", required=True)
    dec.add_argument("--shape", nargs=2, type=int, required=True, metavar=("H", "W"))
    dec.add_argument("--output", type=Path, help="Optional .npy output path.")

    args = ap.parse_args()
    if args.cmd == "encode":
        mask = np.load(args.mask)
        scores = np.load(args.scores)
        print(encode_instances(args.image_id, mask, scores))
    elif args.cmd == "decode":
        mask = rle_decode(args.rle, (args.shape[0], args.shape[1]))
        if args.output:
            np.save(args.output, mask)
            print(f"wrote {args.output}")
        else:
            print(mask.astype(int))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
