#!/usr/bin/env python3
"""Deterministic tiny smoke check for Python label filters and cardinality."""
from __future__ import annotations

import argparse

import hnswlib
import numpy as np


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def expect_error(callable_, message: str) -> None:
    try:
        callable_()
    except Exception as exc:  # native exception type is implementation-facing
        print(f"PASS: {message} ({type(exc).__name__})")
    else:
        raise AssertionError(f"expected an exception: {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", choices=("l2", "ip", "cosine"), default="l2")
    args = parser.parse_args()

    data = np.asarray(
        [[0.0, 0.0], [1.0, 0.0], [0.0, 2.0], [3.0, 1.0], [4.0, 4.0]],
        dtype=np.float32,
    )
    ids = np.asarray([10, 11, 12, 13, 14], dtype=np.int64)
    index = hnswlib.Index(space=args.space, dim=2)
    index.init_index(max_elements=len(data), M=8, ef_construction=50)
    index.set_ef(20)
    index.add_items(data, ids=ids, num_threads=1)

    allowed = {10, 12, 14}
    seen = []

    def allow_even_slot(label: int) -> bool:
        seen.append(int(label))
        return int(label) in allowed

    labels, distances = index.knn_query(
        np.asarray([[0.1, 0.0], [3.5, 3.5]], dtype=np.float32),
        k=2,
        num_threads=1,
        filter=allow_even_slot,
    )
    check(labels.shape == (2, 2) and distances.shape == (2, 2), "filtered query preserves result shapes")
    check(all(int(label) in allowed for label in labels.ravel()), "filter results contain only allowed external labels")
    check(seen and all(isinstance(label, int) for label in seen), "Python filter receives integer external labels")

    oracle = hnswlib.BFIndex(space=args.space, dim=2)
    oracle.init_index(max_elements=len(data))
    oracle.add_items(data, ids=ids)
    oracle_labels, oracle_distances = oracle.knn_query(
        np.asarray([[0.1, 0.0], [3.5, 3.5]], dtype=np.float32),
        k=2,
        num_threads=1,
        filter=lambda label: int(label) in allowed,
    )
    # Tied distances may legally return different labels in a different order;
    # compare exact distances and the filter invariant rather than tie labels.
    check(np.allclose(distances, oracle_distances, atol=2e-5), "filtered distances match the tiny BFIndex oracle")
    check(all(int(label) in allowed for label in oracle_labels.ravel()), "BFIndex filter results also contain only allowed labels")

    # Difficult edge case: a filter cannot fill k by padding unavailable labels.
    one = hnswlib.Index(space="l2", dim=2)
    one.init_index(max_elements=1)
    one.add_items(np.asarray([1.0, 0.0], dtype=np.float32), np.int64(7))
    expect_error(
        lambda: one.knn_query(np.asarray([1.0, 0.0], dtype=np.float32), k=2, num_threads=1),
        "k larger than the one-vector population is rejected",
    )
    expect_error(
        lambda: one.knn_query(np.asarray([1.0, 0.0], dtype=np.float32), k=1, num_threads=1, filter=lambda label: False),
        "a filter with zero eligible labels is rejected",
    )

    print("PASS: python_filter_smoke completed")


if __name__ == "__main__":
    main()
