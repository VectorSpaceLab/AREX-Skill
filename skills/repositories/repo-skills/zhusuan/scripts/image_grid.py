"""Image-grid helper adapted from ZhuSuan example utilities.

This module is intentionally small and self-contained. It only imports the
optional image stack inside the save function so that plain imports stay light.
"""

from __future__ import absolute_import
from __future__ import division

import os

import numpy as np


__all__ = [
    "save_image_collections",
]


def _makedirs(filename):
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)


def save_image_collections(x, filename, shape=(10, 10), scale_each=False,
                           transpose=False):
    """Tile a batch of images into a single output image file.

    Parameters
    ----------
    x : numpy.ndarray
        Image batch with shape (N, H, W, C) or (N, C, H, W) when transpose is
        True.
    filename : str
        Output file path.
    shape : tuple
        Grid shape as (rows, cols).
    scale_each : bool
        Rescale each image to [0, 1] before writing.
    transpose : bool
        Treat the input as (N, C, H, W) and transpose to channels-last.
    """
    try:
        from skimage import io, img_as_ubyte
        from skimage.exposure import rescale_intensity
    except ImportError as exc:
        raise ImportError(
            "save_image_collections requires scikit-image; install the "
            "examples extra to use this helper.") from exc

    _makedirs(filename)
    n = x.shape[0]
    if transpose:
        x = x.transpose(0, 2, 3, 1)
    if scale_each:
        for i in range(n):
            x[i] = rescale_intensity(x[i], out_range=(0, 1))
    n_channels = x.shape[3]
    x = img_as_ubyte(x)
    r, c = shape
    if r * c < n:
        print('Shape too small to contain all images')
    h, w = x.shape[1:3]
    ret = np.zeros((h * r, w * c, n_channels), dtype='uint8')
    for i in range(r):
        for j in range(c):
            if i * c + j < n:
                ret[i * h:(i + 1) * h, j * w:(j + 1) * w, :] = x[i * c + j]
    ret = ret.squeeze()
    io.imsave(filename, ret)
