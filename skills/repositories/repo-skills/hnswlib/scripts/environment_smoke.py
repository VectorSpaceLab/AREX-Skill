#!/usr/bin/env python3
"""Run a bounded, CPU-only import and Index/BFIndex smoke check."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import hnswlib
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", choices=("l2", "ip", "cosine"), default="l2")
    args = parser.parse_args()

    data = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    ids = np.asarray([4, 7, 9], dtype=np.int64)
    index = hnswlib.Index(args.space, 2)
    index.init_index(max_elements=3, M=8, ef_construction=20, random_seed=1)
    index.set_ef(10)
    index.add_items(data, ids, num_threads=1)
    labels, distances = index.knn_query(data[:1], k=2, num_threads=1)
    assert labels.shape == distances.shape == (1, 2)

    exact = hnswlib.BFIndex(args.space, 2)
    exact.init_index(3)
    exact.add_items(data, ids)
    exact_labels, exact_distances = exact.knn_query(data[:1], k=2, num_threads=1)
    # Tied distances may legitimately return different labels while preserving
    # the same exact distance multiset.
    assert all(int(label) in set(map(int, ids)) for label in labels[0])
    assert np.allclose(np.sort(distances), np.sort(exact_distances), atol=2e-5)

    with tempfile.TemporaryDirectory(prefix="hnswlib-smoke-") as tmp:
        path = Path(tmp) / "index.bin"
        index.save_index(str(path))
        loaded = hnswlib.Index(args.space, 2)
        loaded.load_index(str(path))
        assert loaded.ef == 10

    print(f"PASS: hnswlib {args.space} CPU smoke")


if __name__ == "__main__":
    main()
