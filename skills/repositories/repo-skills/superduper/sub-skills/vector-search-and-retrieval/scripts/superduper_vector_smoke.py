#!/usr/bin/env python3
"""Small, deterministic Superduper vector-search smoke helper.

Default mode constructs ObjectModel, Listener, VectorIndex, and the local
in-memory searcher without creating a database. Optional --run-db attempts a
small mongomock-backed Datalayer workflow if the active environment has the
required optional backend installed.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from typing import Any

import numpy as np


MEASURES = ("cosine", "dot", "l2")


def tiny_vector(value: int, dimension: int) -> np.ndarray:
    """Return a deterministic sparse vector for a small integer value."""
    if dimension < 2:
        raise ValueError("dimension must be at least 2")
    value = int(value)
    vector = np.zeros(dimension, dtype=np.int64)
    vector[value % dimension] = 1
    vector[(value * 3 + 1) % dimension] = 1
    return vector


def make_embedding(dimension: int, *, negate: bool = False):
    """Build a serializable embedding callable for ObjectModel."""

    def embed(value: int) -> np.ndarray:
        numeric = -int(value) if negate else int(value)
        return tiny_vector(numeric, dimension)

    return embed


def construct_components(dimension: int, measure: str) -> dict[str, Any]:
    """Construct vector components without requiring a Datalayer."""
    from superduper import Listener, ObjectModel, VectorIndex

    embedding_model = ObjectModel(
        identifier="skill-vector-embedding",
        object=make_embedding(dimension),
        datatype=f"vector[int:{dimension}]",
    )
    indexing_listener = Listener(
        identifier="skill-vector-listener",
        model=embedding_model,
        key="x",
        select=None,
    )

    query_model = ObjectModel(
        identifier="skill-query-embedding",
        object=make_embedding(dimension, negate=True),
    )
    compatible_listener = Listener(
        identifier="skill-query-listener",
        model=query_model,
        key="query",
        select=None,
    )

    vector_index = VectorIndex(
        identifier="skill-vector-index",
        indexing_listener=indexing_listener,
        compatible_listener=compatible_listener,
        measure=measure,
    )

    return {
        "model": embedding_model.identifier,
        "model_datatype": embedding_model.datatype,
        "indexing_listener": indexing_listener.identifier,
        "indexing_key": indexing_listener.key,
        "indexing_outputs": indexing_listener.outputs,
        "compatible_listener": compatible_listener.identifier,
        "compatible_key": compatible_listener.key,
        "vector_index": vector_index.identifier,
        "measure": vector_index.measure,
    }


def run_searcher_smoke(dimension: int, measure: str) -> dict[str, Any]:
    """Exercise the local in-memory VectorSearcher contract."""
    from superduper.backends.base.vector_search import VectorItem
    from superduper.backends.local.vector_search import InMemoryVectorSearcher

    searcher = InMemoryVectorSearcher(
        identifier="skill-searcher",
        dimensions=dimension,
        measure=measure,
    )
    items = [
        VectorItem.create(id=str(i), vector=tiny_vector(i, dimension))
        for i in range(5)
    ]
    searcher.add(items)
    ids, scores = searcher.find_nearest_from_array(tiny_vector(2, dimension), n=3)
    description = searcher.describe()
    return {
        "description": description,
        "nearest_ids": ids,
        "nearest_scores_for_ids": [float(score) for score in scores[: len(ids)]],
        "raw_score_count": len(scores),
    }


def run_db_smoke(dimension: int, measure: str) -> dict[str, Any]:
    """Attempt a tiny database-backed VectorIndex workflow."""
    try:
        import superduper_mongodb  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on optional plugin
        raise RuntimeError(
            "optional mongomock/MongoDB backend is not installed in this environment"
        ) from exc

    from superduper import Listener, ObjectModel, Table, VectorIndex, superduper

    with tempfile.TemporaryDirectory(prefix="superduper-vector-smoke-") as tmpdir:
        db = superduper(
            "mongomock://superduper_vector_smoke",
            artifact_store=f"filesystem://{tmpdir}/artifacts",
            force_apply=True,
            log_level="ERROR",
            vector_search_engine="local",
        )
        try:
            table = Table(
                "documents",
                fields={"id": "str", "x": "int", "label": "int"},
            )
            db.apply(table)
            db["documents"].insert(
                [
                    {"id": str(i), "x": i, "label": int(i % 2 == 0)}
                    for i in range(8)
                ]
            )

            model = ObjectModel(
                identifier="skill-db-embedding",
                object=make_embedding(dimension),
                datatype=f"vector[int:{dimension}]",
            )
            indexing_listener = Listener(
                identifier="skill-db-vector-listener",
                model=model,
                key="x",
                select=db["documents"].select(),
            )
            query_model = ObjectModel(
                identifier="skill-db-query-embedding",
                object=make_embedding(dimension, negate=True),
            )
            compatible_listener = Listener(
                identifier="skill-db-query-listener",
                model=query_model,
                key="query",
                select=None,
            )
            vector_index = VectorIndex(
                identifier="skill_db_vector_index",
                indexing_listener=indexing_listener,
                compatible_listener=compatible_listener,
                measure=measure,
            )
            db.apply(vector_index)

            rows = (
                db["documents"]
                .like({"query": -2}, vector_index="skill_db_vector_index", n=3)
                .select()
                .execute()
            )
            first = dict(rows[0]) if rows else {}
            return {
                "rows": len(rows),
                "first_id": first.get("id"),
                "first_x": first.get("x"),
                "first_score": float(first["score"]) if "score" in first else None,
            }
        finally:
            disconnect = getattr(db, "disconnect", None)
            if callable(disconnect):
                disconnect()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Construct and optionally exercise a tiny Superduper VectorIndex "
            "workflow without network, credentials, downloads, or training."
        )
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=8,
        help="Embedding dimension for the deterministic tiny vector function.",
    )
    parser.add_argument(
        "--measure",
        choices=MEASURES,
        default="cosine",
        help="Vector-search measure to use for construction and local smoke.",
    )
    parser.add_argument(
        "--run-db",
        action="store_true",
        help=(
            "Attempt a small mongomock-backed Datalayer VectorIndex workflow. "
            "Requires the optional MongoDB/mongomock backend to be installed."
        ),
    )
    parser.add_argument(
        "--as-json",
        action="store_true",
        help="Accepted for consistency with sibling helpers; output is always JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    payload: dict[str, Any] = {
        "components": construct_components(args.dimension, args.measure),
        "local_searcher": run_searcher_smoke(args.dimension, args.measure),
    }
    if args.run_db:
        try:
            payload["db_workflow"] = run_db_smoke(args.dimension, args.measure)
        except Exception as exc:  # pragma: no cover - environment-specific
            payload["db_workflow"] = {
                "status": "failed",
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
