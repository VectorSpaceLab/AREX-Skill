#!/usr/bin/env python3
"""Tiny affine preprocessing smoke test.

Builds a synthetic RGB image, applies the TensorLayer affine helpers, and
checks that the output shape remains valid. An optional flag also exercises the
keypoint transform helper.
"""

from __future__ import annotations

import argparse

import numpy as np
import tensorlayer as tl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keypoints', action='store_true', help='also verify affine_transform_keypoints')
    args = parser.parse_args()

    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[2:6, 2:6] = 255

    matrix = tl.prepro.affine_rotation_matrix(angle=15)
    transformed = tl.prepro.affine_transform_cv2(image, matrix)
    if transformed.shape != image.shape:
        raise AssertionError(f'unexpected transformed shape: {transformed.shape}')

    if args.keypoints:
        coords = [[(1, 1), (6, 1), (6, 6), (1, 6)]]
        out = tl.prepro.affine_transform_keypoints(coords, matrix)
        if len(out) == 0 or len(out[0]) == 0:
            raise AssertionError('keypoint transform returned no coordinates')

    print('affine-ok', transformed.shape, transformed.dtype)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
