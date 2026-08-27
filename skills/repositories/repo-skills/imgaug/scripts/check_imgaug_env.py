#!/usr/bin/env python3
"""Check that imgaug is importable and its core runtime dependencies are healthy.

Safe default:
- no network
- no GUI
- no downloads
- exits non-zero on a broken install

Example:
    python scripts/check_imgaug_env.py
"""

from __future__ import annotations

import argparse
import sys
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Check imgaug runtime health.")
    parser.add_argument(
        "--require-imagecorruptions",
        action="store_true",
        help="Fail if the optional imagecorruptions package is missing.",
    )
    args = parser.parse_args()

    import numpy as np
    import imgaug as ia
    import imgaug.augmenters as iaa
    import imgaug.parameters as iap
    import imgaug.multicore as multicore

    print(f"python={sys.version.split()[0]}")
    print(f"imgaug={metadata.version('imgaug')}")
    print(f"numpy={np.__version__}")
    print(f"opencv={metadata.version('opencv-python-headless') if 'opencv-python-headless' in {dist.metadata['Name'] for dist in metadata.distributions()} else 'installed'}")
    print(f"import imgaug from {ia.__file__}")
    print(f"seququential={iaa.Sequential}")
    print(f"parameters={iap.Clip}")
    print(f"multicore={multicore.Pool}")

    if np.__version__.startswith('2.'):
        raise SystemExit("imgaug 0.4.0 requires numpy<2 because it reads np.sctypes.")

    images = np.zeros((1, 8, 8, 3), dtype=np.uint8)
    images[..., 0] = 10
    out = iaa.Sequential([iaa.Fliplr(1.0), iaa.Add(1)])(images=images)
    if out.shape != images.shape or out.dtype != images.dtype:
        raise SystemExit(f"unexpected augmentation result: shape={out.shape} dtype={out.dtype}")
    if int(out[0, 0, -1, 0]) != 11:
        raise SystemExit("tiny augmentation smoke did not modify the expected pixel")

    try:
        import imagecorruptions  # type: ignore  # noqa: F401
        print("imagecorruptions=installed")
    except Exception:
        if args.require_imagecorruptions:
            raise SystemExit("optional dependency imagecorruptions is missing")
        print("imagecorruptions=missing (optional)")

    print("imgaug environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
