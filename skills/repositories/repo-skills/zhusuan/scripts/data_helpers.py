"""Small reusable NumPy helpers distilled from ZhuSuan examples.

These functions are safe to use without the original examples directory.
They intentionally avoid network access and external datasets.
"""

from __future__ import absolute_import
from __future__ import division

import numpy as np


__all__ = [
    "standardize",
    "to_one_hot",
    "average_rmse_over_batches",
]


def standardize(data_train, data_test):
    """Standardize train/test arrays with train-set statistics."""
    std = np.std(data_train, 0, keepdims=True)
    std[std == 0] = 1
    mean = np.mean(data_train, 0, keepdims=True)
    data_train_standardized = (data_train - mean) / std
    data_test_standardized = (data_test - mean) / std
    mean, std = np.squeeze(mean, 0), np.squeeze(std, 0)
    return data_train_standardized, data_test_standardized, mean, std


def to_one_hot(x, depth):
    """Return a one-hot matrix for a 1-D integer array."""
    ret = np.zeros((x.shape[0], depth))
    ret[np.arange(x.shape[0]), x] = 1
    return ret


def average_rmse_over_batches(rmses, sizes):
    """Average batch RMSE values that may correspond to uneven batch sizes."""
    rmses = np.array(rmses)
    sizes = np.array(sizes)
    return np.sqrt(np.sum(rmses ** 2 * sizes) / np.sum(sizes))
