#!/usr/bin/env python3
"""Run a tiny Albumentations import and pipeline smoke check."""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check that Albumentations imports and runs a tiny pipeline.")
    parser.add_argument("--expect-version", default=None, help="Optional exact Albumentations version to require.")
    parser.add_argument("--allow-update-check", action="store_true", help="Do not set NO_ALBUMENTATIONS_UPDATE=1 before import.")
    args = parser.parse_args()

    if not args.allow_update_check:
        os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

    try:
        import albumentations as A
        import numpy as np
    except Exception as exc:
        raise SystemExit(f"import failed: {exc}") from exc

    if args.expect_version and A.__version__ != args.expect_version:
        raise SystemExit(f"version mismatch: expected {args.expect_version}, got {A.__version__}")

    image = np.arange(4 * 5 * 3, dtype=np.uint8).reshape(4, 5, 3)
    transform = A.Compose([A.HorizontalFlip(p=1.0)], strict=True, seed=137)
    result = transform(image=image)
    if result["image"].shape != image.shape:
        raise SystemExit(f"unexpected output shape: {result['image'].shape}")
    print(f"ok albumentations={A.__version__} shape={result['image'].shape}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
