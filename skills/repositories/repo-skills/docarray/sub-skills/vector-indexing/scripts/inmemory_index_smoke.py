#!/usr/bin/env python3
"""Run a safe, deterministic CPU smoke for InMemoryExactNNIndex.

The helper creates a tiny typed BaseDoc schema, indexes NumPy vectors, checks
find/filter/query-builder behavior, and optionally checks persistence. It does
not require a database, network, credentials, model downloads, or torch.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-docs", type=int, default=8, help="Number of tiny docs to index (default: 8).")
    parser.add_argument("--dim", type=int, default=4, help="Embedding dimension (default: 4).")
    parser.add_argument("--work-dir", default=None, help="Optional directory for a persistence smoke.")
    parser.add_argument("--exercise-persist", action="store_true", help="Persist and restore the local index.")
    args = parser.parse_args(argv)
    if args.num_docs < 2 or args.dim < 1:
        parser.error("--num-docs must be >= 2 and --dim must be >= 1")

    try:
        import numpy as np
        from docarray import BaseDoc, DocList
        from docarray.index import InMemoryExactNNIndex
        from docarray.typing import NdArray
        from pydantic import Field
    except ImportError as exc:
        raise SystemExit(
            "ImportError: this helper needs DocArray, NumPy, and the in-memory index. "
            "Install the base DocArray package before running it. Original error: " + str(exc)
        ) from exc

    # Dynamic parametrization is intentional: the helper works with arbitrary --dim.
    VectorType = NdArray[args.dim]

    class SmokeDoc(BaseDoc):
        text: str
        rank: int
        # Explicit Euclidean distance keeps the synthetic magnitudes
        # distinguishable instead of relying on cosine's default behavior.
        embedding: VectorType = Field(space="euclidean_dist")

    # A shared nonzero direction gives every document a distinct magnitude,
    # and the nonzero query avoids the all-zero equal-score boundary.
    direction = np.linspace(1.0, 2.0, args.dim, dtype=np.float32)
    vectors = np.arange(1, args.num_docs + 1, dtype=np.float32)[:, None] * direction
    query_vector = direction * np.float32(0.25)
    docs = DocList[SmokeDoc](
        SmokeDoc(text=f"doc-{i}", rank=i, embedding=vectors[i]) for i in range(args.num_docs)
    )
    index = InMemoryExactNNIndex[SmokeDoc](docs)
    assert index.num_docs() == args.num_docs

    matches, scores = index.find(query_vector, search_field="embedding", limit=min(3, args.num_docs))
    assert len(matches) == len(scores) == min(3, args.num_docs)
    assert matches[0].rank == 0
    filtered = index.filter({"rank": {"$gte": 2}}, limit=args.num_docs)
    assert len(filtered) == args.num_docs - 2

    # The same distinctive query is used inside the filtered query builder.
    query = (
        index.build_query()
        .filter(filter_query={"rank": {"$eq": 1}})
        .find(query=query_vector, search_field="embedding", limit=1)
        .build()
    )
    query_docs, query_scores = index.execute_query(query)
    assert len(query_docs) == len(query_scores) == 1
    assert query_docs[0].rank == 1

    if args.exercise_persist:
        if args.work_dir:
            work_dir = Path(args.work_dir).expanduser().resolve()
            work_dir.mkdir(parents=True, exist_ok=True)
            path = work_dir / "inmemory-index-smoke.bin"
            _run_persist(index, path, SmokeDoc, InMemoryExactNNIndex, query_vector)
        else:
            with tempfile.TemporaryDirectory(prefix="docarray-index-smoke-") as tmp:
                _run_persist(index, Path(tmp) / "inmemory-index-smoke.bin", SmokeDoc, InMemoryExactNNIndex, query_vector)

    print(f"InMemoryExactNNIndex smoke passed: docs={args.num_docs}, dim={args.dim}")
    if args.exercise_persist:
        print("Persistence round-trip passed")
    return 0


def _run_persist(index, path, schema, index_cls, query_vector) -> None:
    index.persist(str(path))
    restored = index_cls[schema](index_file_path=str(path))
    assert restored.num_docs() == index.num_docs()
    docs, scores = restored.find(query_vector, search_field="embedding", limit=1)
    assert len(docs) == len(scores) == 1
    assert docs[0].rank == 0


if __name__ == "__main__":
    raise SystemExit(main())
