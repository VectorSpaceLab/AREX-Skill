#!/usr/bin/env python3
"""Tiny smoke for imgaug parameters, RNG, sample data, and dtype helpers.

Safe default:
- package data only
- no GUI
- no network

Example:
    python sub-skills/parameters-random-and-utilities/scripts/smoke_parameters_and_data.py
"""

from __future__ import annotations

import numpy as np


def main() -> int:
    import imgaug as ia
    import imgaug.parameters as iap
    import imgaug.random as iarandom
    import imgaug.dtypes as iadt

    rng = iarandom.RNG(1)
    param = iap.Clip(iap.Normal(1.0, 0.1), 0.1, 3.0)
    sample = float(param.draw_sample(random_state=rng))
    assert 0.1 <= sample <= 3.0, sample

    image = ia.data.quokka_square(size=(32, 32))
    assert image.shape == (32, 32, 3)
    assert image.dtype == np.uint8

    heatmap = ia.data.quokka_heatmap(size=(32, 32))
    segmap = ia.data.quokka_segmentation_map(size=(32, 32))
    assert heatmap.arr_0to1.ndim == 3
    assert segmap.arr.ndim == 3

    floats = np.array([[-5.5, 12.2, 300.0]], dtype=np.float32)
    converted = iadt.change_dtype_(floats, np.uint8, clip=True, round=True)
    assert converted.dtype == np.uint8
    assert converted.tolist() == [[0, 12, 255]]

    grid = ia.draw_grid([image, image], cols=2)
    assert grid.ndim == 3 and grid.dtype == np.uint8

    print("parameters/data/dtype smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
