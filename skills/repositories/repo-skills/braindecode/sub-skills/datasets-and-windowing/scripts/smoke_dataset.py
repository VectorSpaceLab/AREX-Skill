#!/usr/bin/env python3
"""Validate local array-to-window behavior without downloads or credentials."""
from __future__ import annotations
import argparse
import numpy as np
from braindecode.datasets import create_from_X_y

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--channels", type=int, default=2)
    p.add_argument("--samples", type=int, default=20)
    p.add_argument("--window-size", type=int, default=10)
    p.add_argument("--stride", type=int, default=5)
    args = p.parse_args()
    if min(args.channels, args.samples, args.window_size, args.stride) <= 0:
        p.error("dimensions and window parameters must be positive")
    X = np.arange(args.channels * args.samples, dtype="float32").reshape(1, args.channels, args.samples)
    ds = create_from_X_y(X, np.array([3]), drop_last_window=False, sfreq=100,
                         window_size_samples=args.window_size,
                         window_stride_samples=args.stride)
    expected = 1 + max(0, (args.samples - args.window_size + args.stride - 1) // args.stride)
    assert len(ds) == expected, (len(ds), expected)
    first = ds[0][0]
    assert tuple(first.shape) == (args.channels, args.window_size)
    print(f"windows={len(ds)} first_shape={tuple(first.shape)}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
