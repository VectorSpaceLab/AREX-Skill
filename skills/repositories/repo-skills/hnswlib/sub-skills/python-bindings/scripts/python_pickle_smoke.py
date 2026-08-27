#!/usr/bin/env python3
"""Deterministic tiny smoke check for Index pickle state and caveats."""
from __future__ import annotations

import argparse
import pickle

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

    dim = 3
    data = np.asarray([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [1.0, 1.0, 0.0]], dtype=np.float32)
    ids = np.asarray([40, 41, 42], dtype=np.int64)
    queries = np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)

    index = hnswlib.Index(space=args.space, dim=dim)
    index.init_index(max_elements=4, M=8, ef_construction=40, random_seed=11)
    index.set_ef(17)
    index.num_threads = 1
    index.add_items(data, ids=ids, num_threads=1)
    before_labels, before_distances = index.knn_query(queries, k=2, num_threads=1)

    # The extension's pickle state captures Index parameters and graph data.
    copy = pickle.loads(pickle.dumps(index))
    check(copy.space == args.space and copy.dim == dim, "pickle preserves space and dimension")
    check(copy.max_elements == 4 and copy.element_count == 3, "pickle preserves capacity and count")
    check(copy.ef == 17 and copy.num_threads == 1, "pickle preserves ef and thread default")
    requested = np.asarray([40, 41, 42], dtype=np.int64)
    check(np.allclose(copy.get_items(requested), index.get_items(requested), atol=2e-6), "pickle preserves explicit vector retrieval")
    after_labels, after_distances = copy.knn_query(queries, k=2, num_threads=1)
    check(np.array_equal(before_labels, after_labels), "pickle preserves tiny query labels")
    check(np.allclose(before_distances, after_distances, atol=2e-5), "pickle preserves tiny query distances")

    # Pickle also carries deletion/replacement state; take the snapshot only
    # after mutations, never concurrently with add_items.
    replaceable = hnswlib.Index(space="l2", dim=2)
    replaceable.init_index(max_elements=2, allow_replace_deleted=True)
    replaceable.add_items(np.asarray([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32), ids=np.asarray([50, 51]))
    replaceable.mark_deleted(51)
    restored = pickle.loads(pickle.dumps(replaceable))
    restored.add_items(np.asarray([2.0, 2.0], dtype=np.float32), np.int64(52), replace_deleted=True)
    check(52 in set(map(int, restored.get_ids_list())), "pickle preserves replacement-enabled deletion state")
    check(51 not in set(map(int, restored.get_ids_list())), "replaced deleted label stays absent after pickle")

    print("PASS: python_pickle_smoke completed")


if __name__ == "__main__":
    main()
