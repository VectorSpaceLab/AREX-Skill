#!/usr/bin/env python3
"""Deterministically check DeepDanbooru's image preprocessing contract.

This helper creates a temporary PNG, so it needs no model, weights, network,
or source-checkout path. Run it in the installed DeepDanbooru environment.
"""

from __future__ import annotations

import argparse
import io
import os
import tempfile
from pathlib import Path

# Keep this helper CPU-first. Set before importing TensorFlow transitively.
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    import numpy as np
    import tensorflow as tf

    from deepdanbooru.data import load_image_for_evaluate

    # Deliberately non-square so aspect-preserving resize and padding are used.
    source = np.zeros((3, 5, 3), dtype=np.uint8)
    source[:, :, 0] = 255
    source[1, 2] = (0, 255, 0)

    with tempfile.TemporaryDirectory(prefix="deepdanbooru-preprocess-") as temp_dir:
        image_path = Path(temp_dir) / "fixture.png"
        encoded = tf.io.encode_png(source).numpy()
        tf.io.write_file(str(image_path), encoded)

        from_path = load_image_for_evaluate(str(image_path), width=8, height=6)
        from_bytes = load_image_for_evaluate(
            io.BytesIO(encoded), width=8, height=6
        )

    for name, image in (("path", from_path), ("bytes", from_bytes)):
        assert image.shape == (6, 8, 3), f"{name}: unexpected shape {image.shape}"
        assert np.issubdtype(image.dtype, np.floating), (
            f"{name}: expected floating output, got {image.dtype}"
        )
        assert float(image.min()) >= -1e-6, f"{name}: value below 0"
        assert float(image.max()) <= 1.0 + 1e-6, f"{name}: value above 1"

    np.testing.assert_allclose(from_path, from_bytes, rtol=0.0, atol=1e-6)
    print("preprocess smoke passed: path/bytes -> (6, 8, 3), normalized to 0..1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
