#!/usr/bin/env python3
"""Deterministic qdrant-client local-mode smoke test.

Run after installing qdrant-client:

    python local_mode_smoke.py --mode memory
    python local_mode_smoke.py --mode persistent

The script does not require a Qdrant server or the qdrant-client source tree.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient, models

COLLECTION = "local_mode_smoke"


def build_client(mode: str, path: str | None) -> tuple[QdrantClient, Path | None]:
    if mode == "memory":
        return QdrantClient(":memory:"), None

    if path is None:
        store_dir = Path(tempfile.mkdtemp(prefix="qdrant-local-smoke-"))
    else:
        store_dir = Path(path)
        store_dir.mkdir(parents=True, exist_ok=True)

    return QdrantClient(path=str(store_dir)), store_dir


def create_collection(client: QdrantClient) -> None:
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config={
            "text": models.VectorParams(size=4, distance=models.Distance.COSINE),
            "image": models.VectorParams(size=4, distance=models.Distance.COSINE),
            "colbert": models.VectorParams(
                size=3,
                distance=models.Distance.DOT,
                multivector_config=models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM
                ),
            ),
        },
        sparse_vectors_config={"sparse": models.SparseVectorParams()},
        metadata={"created_by": "qdrant-client-local-mode-smoke"},
    )


def upsert_points(client: QdrantClient) -> None:
    client.upsert(
        collection_name=COLLECTION,
        points=[
            models.PointStruct(
                id=1,
                vector={
                    "text": [1.0, 0.0, 0.0, 0.0],
                    "image": [1.0, 0.0, 0.0, 0.0],
                    "colbert": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                    "sparse": models.SparseVector(indices=[1, 3], values=[0.7, 0.3]),
                },
                payload={"city": "Berlin", "group": "alpha", "rank": 1},
            ),
            models.PointStruct(
                id=2,
                vector={
                    "text": [0.9, 0.1, 0.0, 0.0],
                    "image": [0.8, 0.2, 0.0, 0.0],
                    "colbert": [[0.8, 0.2, 0.0], [0.0, 0.8, 0.2]],
                    "sparse": models.SparseVector(indices=[1, 5], values=[0.6, 0.4]),
                },
                payload={"city": ["Berlin", "London"], "group": "alpha", "rank": 2},
            ),
            models.PointStruct(
                id=3,
                vector={
                    "text": [0.0, 1.0, 0.0, 0.0],
                    "image": [0.0, 1.0, 0.0, 0.0],
                    "colbert": [[0.0, 0.0, 1.0], [0.2, 0.8, 0.0]],
                    "sparse": models.SparseVector(indices=[7], values=[1.0]),
                },
                payload={"city": "London", "group": "beta", "rank": 3},
            ),
        ],
    )


def assert_local_queries(client: QdrantClient) -> dict[str, Any]:
    count = client.count(COLLECTION).count
    if count != 3:
        raise AssertionError(f"expected 3 points, got {count}")

    london_filter = models.Filter(
        must=[models.FieldCondition(key="city", match=models.MatchValue(value="London"))]
    )

    dense_ids = [
        point.id
        for point in client.query_points(
            collection_name=COLLECTION,
            using="text",
            query=[1.0, 0.0, 0.0, 0.0],
            query_filter=london_filter,
            limit=3,
        ).points
    ]
    if dense_ids != [2, 3]:
        raise AssertionError(f"unexpected dense filtered ids: {dense_ids}")

    sparse_ids = [
        point.id
        for point in client.query_points(
            collection_name=COLLECTION,
            using="sparse",
            query=models.SparseVector(indices=[1, 5], values=[0.6, 0.4]),
            limit=3,
        ).points
    ]
    if sparse_ids[:2] != [2, 1]:
        raise AssertionError(f"unexpected sparse ids: {sparse_ids}")

    multivector_ids = [
        point.id
        for point in client.query_points(
            collection_name=COLLECTION,
            using="colbert",
            query=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            limit=3,
        ).points
    ]
    if multivector_ids[0] != 1:
        raise AssertionError(f"unexpected multivector ids: {multivector_ids}")

    fusion_result = client.query_points(
        collection_name=COLLECTION,
        prefetch=[
            models.Prefetch(query=[1.0, 0.0, 0.0, 0.0], using="text", limit=3),
            models.Prefetch(query=[1.0, 0.0, 0.0, 0.0], using="image", limit=3),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        score_threshold=0.45,
        limit=3,
    )
    fusion_ids = [point.id for point in fusion_result.points]
    if not fusion_ids or fusion_ids[0] != 1:
        raise AssertionError(f"unexpected fusion ids: {fusion_ids}")

    return {
        "count": count,
        "dense_london_ids": dense_ids,
        "sparse_top_ids": sparse_ids,
        "multivector_top_ids": multivector_ids,
        "fusion_ids": fusion_ids,
    }


def assert_persistent_reopen(store_dir: Path) -> dict[str, Any]:
    reopened = QdrantClient(path=str(store_dir))
    try:
        count = reopened.count(COLLECTION).count
        if count != 3:
            raise AssertionError(f"expected reopened count 3, got {count}")
        records, _ = reopened.scroll(COLLECTION, limit=10, with_vectors=True, with_payload=True)
        sparse_indices = sorted(records[0].vector["sparse"].indices)
        return {"reopened_count": count, "first_sparse_indices": sparse_indices}
    finally:
        reopened.close()


def assert_persistent_lock(store_dir: Path) -> str:
    first = QdrantClient(path=str(store_dir))
    try:
        try:
            second = QdrantClient(path=str(store_dir))
        except Exception as exc:  # noqa: BLE001 - wording differs by portalocker platform
            message = str(exc)
            if "already accessed by another instance" not in message:
                raise AssertionError(f"unexpected lock error: {message}") from exc
            return message
        else:
            second.close()
            raise AssertionError("opening the same persistent path twice should fail")
    finally:
        first.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run qdrant-client local-mode smoke checks.")
    parser.add_argument("--mode", choices=("memory", "persistent"), default="memory")
    parser.add_argument(
        "--path",
        help="Persistent store directory for --mode persistent. Defaults to a temporary directory.",
    )
    args = parser.parse_args()

    client, store_dir = build_client(args.mode, args.path)
    summary: dict[str, Any] = {"mode": args.mode}

    try:
        create_collection(client)
        upsert_points(client)
        summary.update(assert_local_queries(client))
    finally:
        client.close()

    if args.mode == "persistent":
        if store_dir is None:
            raise AssertionError("persistent mode did not create a store directory")
        summary["store_dir"] = str(store_dir)
        summary.update(assert_persistent_reopen(store_dir))
        summary["lock_error_contains"] = "already accessed by another instance" in assert_persistent_lock(
            store_dir
        )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
