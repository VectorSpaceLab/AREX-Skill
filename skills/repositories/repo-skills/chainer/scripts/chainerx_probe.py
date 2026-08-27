#!/usr/bin/env python3
"""Inspect whether ChainerX is available and usable in the current environment."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        default="native:0",
        help="Device name to test when ChainerX is available",
    )
    args = parser.parse_args()

    try:
        import chainerx as chx
    except Exception as exc:
        print(f"chainerx import failed: {exc}")
        print("Check that the package was built with CHAINER_BUILD_CHAINERX=1.")
        print("Use CHAINERX_BUILD_CUDA=1 and cuDNN settings if you need CUDA.")
        return 1

    print(f"available={chx.is_available()}")
    if not chx.is_available():
        print("ChainerX is not built into this install.")
        print("Rebuild from source with CHAINER_BUILD_CHAINERX=1.")
        return 0

    with chx.using_device(args.device):
        arr = chx.array([1, 2, 3], dtype=chx.float32)
        arr = arr + 1
        print(f"device={arr.device}")
        print(f"values={chx.to_numpy(arr).tolist()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
