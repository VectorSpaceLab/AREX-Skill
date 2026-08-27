#!/usr/bin/env python3
"""Deterministic qdrant-client model/conversion smoke checks.

This script uses only local model construction and REST/gRPC conversion helpers.
It does not connect to a Qdrant server and does not perform inference.
"""

from __future__ import annotations

from datetime import datetime, timezone

from qdrant_client import models
from qdrant_client.conversions.conversion import (
    GrpcToRest,
    RestToGrpc,
    grpc_to_payload,
    payload_to_grpc,
)


def build_filter() -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(
                key="kind",
                match=models.MatchValue(value="article"),
            )
        ],
        min_should=models.MinShould(
            conditions=[
                models.FieldCondition(
                    key="lang",
                    match=models.MatchAny(any=["en", "de"]),
                ),
                models.FieldCondition(
                    key="published",
                    match=models.MatchValue(value=True),
                ),
            ],
            min_count=1,
        ),
    )


def main() -> None:
    filter_ = build_filter()
    grpc_filter = RestToGrpc.convert_filter(filter_)
    round_trip_filter = GrpcToRest.convert_filter(grpc_filter)
    assert round_trip_filter.min_should is not None
    assert round_trip_filter.min_should.min_count == 1
    assert len(round_trip_filter.must or []) == 1

    sparse = models.SparseVector(indices=[2, 5], values=[0.7, 0.3])
    grpc_sparse = RestToGrpc.convert_sparse_vector(sparse)
    assert list(grpc_sparse.indices) == [2, 5]
    assert all(abs(actual - expected) < 1e-6 for actual, expected in zip(grpc_sparse.values, [0.7, 0.3]))

    query_request = models.QueryRequest(
        prefetch=models.Prefetch(
            query=models.NearestQuery(nearest=[0.1, 0.2, 0.3]),
            using="dense",
            filter=filter_,
            limit=20,
        ),
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=5,
        with_payload=True,
    )
    grpc_query = RestToGrpc.convert_query_request(query_request, collection_name="docs")
    assert grpc_query.collection_name == "docs"
    assert len(grpc_query.prefetch) == 1
    assert grpc_query.limit == 5
    assert grpc_query.with_payload.enable is True

    payload = {
        "created_at": datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        "count": 3,
        "tags": ["qdrant", "conversion"],
    }
    restored_payload = grpc_to_payload(payload_to_grpc(payload))
    assert restored_payload["count"] == 3
    assert restored_payload["tags"] == ["qdrant", "conversion"]
    assert restored_payload["created_at"].startswith("2024-01-02")

    point = models.PointStruct(
        id=1,
        vector={"dense": [0.1, 0.2, 0.3], "sparse": sparse},
        payload={"kind": "article"},
    )
    grpc_point = RestToGrpc.convert_point_struct(point)
    rest_point = GrpcToRest.convert_point_struct(grpc_point)
    assert rest_point.id == 1
    assert rest_point.payload == {"kind": "article"}

    print("conversion_smoke: ok")


if __name__ == "__main__":
    main()
