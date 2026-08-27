#!/usr/bin/env python3
"""Smoke-check public data-I/O APIs without network access."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    import numpy as np
    import skimage as ski
    import tifffile
except ModuleNotFoundError as error:
    missing = error.name or "required dependency"
    raise SystemExit(
        "Data-I/O smoke check requires `scikit-image` and its runtime dependencies. "
        f"Missing import: {missing}"
    ) from error


def main() -> int:
    camera = ski.data.camera()
    astronaut = ski.data.astronaut()
    coins = ski.data.coins()

    assert camera.ndim == 2
    assert camera.dtype == np.uint8
    assert astronaut.ndim == 3 and astronaut.shape[-1] == 3
    assert coins.ndim == 2

    float_camera = ski.util.img_as_float(camera)
    ubyte_camera = ski.util.img_as_ubyte(float_camera)
    assert float_camera.dtype == np.float64
    assert ubyte_camera.dtype == np.uint8
    assert np.array_equal(ubyte_camera, camera)

    windows = ski.util.view_as_windows(camera[:8, :8], (4, 4), step=2)
    assert windows.shape == (3, 3, 4, 4)

    montage = ski.util.montage(np.stack([camera[:16, :16], camera[:16, :16]]))
    assert montage.shape == (32, 32)

    inverted = ski.util.invert(np.array([0, 255], dtype=np.uint8))
    assert inverted.tolist() == [255, 0]

    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        gray_path = tmp / "gray.png"
        color_path = tmp / "color.png"
        ski.io.imsave(gray_path, camera)
        ski.io.imsave(color_path, astronaut)

        gray_back = ski.io.imread(gray_path)
        color_back = ski.io.imread(color_path)
        color_gray = ski.io.imread(color_path, as_gray=True)

        assert gray_back.shape == camera.shape
        assert gray_back.dtype == camera.dtype
        assert color_back.shape == astronaut.shape
        assert color_gray.ndim == 2
        assert color_gray.dtype == np.float64

        frame_dir = tmp / "frames"
        frame_dir.mkdir()
        ski.io.imsave(frame_dir / "frame02.png", camera[:32, :32], check_contrast=False)
        ski.io.imsave(frame_dir / "frame01.png", camera[:32, :32], check_contrast=False)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            collection = ski.io.imread_collection(str(frame_dir / "*.png"))
            assert len(collection) == 2
            assert Path(collection.files[0]).name == "frame01.png"
            assert collection[0].shape == (32, 32)

            concatenated = ski.io.concatenate_images(collection)
            assert concatenated.shape == (2, 32, 32)

        multi_path = tmp / "multi.tif"
        tifffile.imwrite(multi_path, np.stack([camera[:16, :16], camera[:16, :16]]))
        multi = ski.io.MultiImage(str(multi_path))
        assert len(multi) == 1
        assert multi[0].shape == (2, 16, 16)

    summary = {
        "sample_data": True,
        "round_trip": True,
        "collection": True,
        "dtype_conversion": True,
        "windows": True,
        "montage": True,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
