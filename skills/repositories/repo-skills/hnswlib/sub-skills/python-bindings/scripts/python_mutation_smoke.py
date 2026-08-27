#!/usr/bin/env python3
"""Deterministic tiny smoke check for update, delete, replacement, and resize."""
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


def expect_error(callable_, message: str) -> None:
    try:
        callable_()
    except Exception as exc:
        print(f"PASS: {message} ({type(exc).__name__})")
    else:
        raise AssertionError(f"expected an exception: {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", choices=("l2", "ip", "cosine"), default="l2")
    args = parser.parse_args()

    base = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0], [3.0, 1.0]], dtype=np.float32)
    ids = np.asarray([20, 21, 22, 23], dtype=np.int64)
    index = hnswlib.Index(space=args.space, dim=2)
    index.init_index(max_elements=4, M=8, ef_construction=40, allow_replace_deleted=True)
    index.set_ef(20)
    index.add_items(base, ids=ids, num_threads=1)

    replacement_vector = np.asarray([[9.0, 9.0]], dtype=np.float32)
    index.add_items(replacement_vector, ids=np.asarray([21], dtype=np.int64), num_threads=1)
    returned = index.get_items(np.asarray([21], dtype=np.int64))
    expected_replacement = replacement_vector
    if args.space == "cosine":
        expected_replacement = replacement_vector / np.linalg.norm(replacement_vector, axis=1, keepdims=True)
    check(np.allclose(returned, expected_replacement, atol=2e-6), "reusing a live label updates its vector")
    check(index.element_count == 4, "an update does not increase element count")

    index.mark_deleted(22)
    check(22 in set(map(int, index.get_ids_list())), "ID list retains the label for explicit deleted-state bookkeeping")
    live_labels, _ = index.knn_query(np.asarray([0.0, 2.0], dtype=np.float32), k=3, num_threads=1)
    check(22 not in set(map(int, live_labels.ravel())), "deleted label is omitted from query results")
    index.unmark_deleted(22)
    restored_labels, _ = index.knn_query(np.asarray([0.0, 2.0], dtype=np.float32), k=4, num_threads=1)
    check(22 in set(map(int, restored_labels.ravel())), "unmark_deleted restores a live label")

    index.mark_deleted(22)
    index.add_items(np.asarray([8.0, 8.0], dtype=np.float32), np.int64(24), num_threads=1, replace_deleted=True)
    current_ids = set(map(int, index.get_ids_list()))
    check(22 not in current_ids and 24 in current_ids, "replacement reuses a deleted slot with a new label")
    check(index.element_count == 4, "replacement keeps capacity and count bounded")
    found, _ = index.knn_query(
        np.asarray([8.0, 8.0], dtype=np.float32),
        k=1,
        num_threads=1,
        filter=lambda label: int(label) == 24,
    )
    check(int(found[0, 0]) == 24, "replaced vector is queryable through an exact label filter")

    index.resize_index(5)
    index.add_items(np.asarray([20.0, 20.0], dtype=np.float32), np.int64(25), num_threads=1)
    check(index.max_elements == 5 and index.element_count == 5, "resize permits one additional new label")

    # Reloading a deleted index without the replacement policy must not silently
    # turn replacement on. This is a deliberately difficult lifecycle case.
    no_replace = hnswlib.Index(space="l2", dim=2)
    no_replace.init_index(max_elements=2)
    no_replace.add_items(np.asarray([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32), ids=np.asarray([30, 31]))
    no_replace.mark_deleted(31)
    with tempfile.TemporaryDirectory(prefix="hnswlib-mutation-") as temp_dir:
        path = Path(temp_dir) / "deleted.bin"
        no_replace.save_index(str(path))
        reloaded = hnswlib.Index(space="l2", dim=2)
        reloaded.load_index(str(path))
        expect_error(
            lambda: reloaded.add_items(np.asarray([2.0, 2.0], dtype=np.float32), np.int64(32), replace_deleted=True),
            "reload without allow_replace_deleted rejects replacement",
        )
        enabled = hnswlib.Index(space="l2", dim=2)
        enabled.load_index(str(path), allow_replace_deleted=True)
        enabled.add_items(np.asarray([2.0, 2.0], dtype=np.float32), np.int64(32), replace_deleted=True)
        check(32 in set(map(int, enabled.get_ids_list())), "reload with allow_replace_deleted enables replacement")

    print("PASS: python_mutation_smoke completed")


if __name__ == "__main__":
    main()
