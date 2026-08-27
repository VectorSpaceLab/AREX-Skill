#!/usr/bin/env python3
"""Deterministic tiny smoke check for the Index/BFIndex Python lifecycle."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import hnswlib
import numpy as np


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", choices=("l2", "ip", "cosine"), default="l2")
    args = parser.parse_args()

    dim = 2
    data = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0], [3.0, 1.0]], dtype=np.float64)
    ids = np.asarray([10, 11, 12, 13], dtype=np.int64)
    queries = np.asarray([[0.1, 0.0], [2.5, 1.0]], dtype=np.float64)

    index = hnswlib.Index(space=args.space, dim=dim)
    check(index.space == args.space and index.dim == dim, "constructor stores space and dimension")
    index.init_index(max_elements=4, M=8, ef_construction=40, random_seed=7)
    index.set_ef(20)
    index.num_threads = 1
    check(index.max_elements == 4 and index.element_count == 0, "initial capacity and count are exposed")

    # The binding accepts float64 input but stores/copies float32 data.
    index.add_items(data, ids=ids, num_threads=1)
    check(index.element_count == 4 and index.get_current_count() == 4, "batch insertion reaches the expected count")
    check(index.M == 8 and index.ef_construction == 40 and index.ef == 20, "construction and query parameters are readable")

    labels, distances = index.knn_query(queries, k=2, num_threads=1)
    check(labels.shape == (2, 2) and distances.shape == (2, 2), "batch query returns rectangular (rows, k) arrays")
    check(np.all(np.diff(distances, axis=1) >= -1e-6), "returned distances are closest-first")

    requested = np.asarray(sorted(index.get_ids_list()), dtype=np.int64)
    stored = index.get_items(requested, return_type="numpy")
    expected = data.astype(np.float32)
    if args.space == "cosine":
        norms = np.linalg.norm(expected, axis=1, keepdims=True)
        expected = expected / (norms + np.float32(1e-30))
    check(np.allclose(stored, expected, atol=2e-6), "explicit IDs retrieve stored vectors")
    check(isinstance(index.get_items(requested[:2], return_type="list"), list), "list retrieval is available")

    # A one-dimensional vector and scalar label are accepted for one row.
    single = hnswlib.Index(space="l2", dim=2)
    single.init_index(max_elements=1)
    single.add_items(np.asarray([9.0, 8.0]), np.int64(99))
    one_labels, one_distances = single.knn_query(np.asarray([9.0, 8.0]), k=1, num_threads=1)
    check(one_labels.shape == (1, 1) and one_distances.shape == (1, 1), "1-D vectors and scalar labels form one row")
    check(int(one_labels[0, 0]) == 99, "scalar-labeled vector is queryable")

    oracle = hnswlib.BFIndex(space=args.space, dim=dim)
    oracle.init_index(max_elements=4)
    oracle.add_items(data, ids=ids)
    oracle_labels, oracle_distances = oracle.knn_query(queries, k=2, num_threads=1)
    check(oracle_labels.shape == (2, 2), "BFIndex supplies an exact-oracle-shaped result")
    check(np.allclose(distances, oracle_distances, atol=2e-5), "tiny HNSW distances agree with BFIndex")
    check(all(set(map(int, row)) == set(map(int, truth)) for row, truth in zip(labels, oracle_labels)), "tiny HNSW labels match BFIndex")

    with tempfile.TemporaryDirectory(prefix="hnswlib-lifecycle-") as temp_dir:
        path = Path(temp_dir) / "index.bin"
        index.save_index(str(path))
        loaded = hnswlib.Index(space=args.space, dim=dim)
        loaded.load_index(str(path), max_elements=6)
        check(loaded.max_elements == 6 and loaded.element_count == 4, "file reload can increase capacity")
        check(loaded.ef == 10, "file reload resets ef to the documented default")
        loaded.set_ef(20)
        loaded.add_items(np.asarray([4.0, 4.0]), np.int64(14), num_threads=1)
        check(loaded.element_count == 5 and int(loaded.knn_query(np.asarray([4.0, 4.0]), k=1, num_threads=1)[0][0, 0]) == 14, "reloaded index accepts growth after ef reset")

    print("PASS: python_lifecycle_smoke completed")


if __name__ == "__main__":
    main()
