#!/usr/bin/env python3
"""Safe qdrant-client smoke checks.

Run after installing qdrant-client to verify imports, local mode operations,
REST-to-gRPC conversion, and optionally async local behavior without a Qdrant
server, credentials, model downloads, or external data.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.metadata as metadata
import sys
import tempfile


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe qdrant-client smoke checks.")
    parser.add_argument(
        "--mode",
        choices=("local", "persistent", "async", "all"),
        default="local",
        help="Which smoke check set to run.",
    )
    return parser


def _local_smoke() -> None:
    from qdrant_client import QdrantClient, models
    from qdrant_client.conversions.conversion import RestToGrpc

    client = QdrantClient(":memory:")
    try:
        client.create_collection(
            "skill_smoke",
            vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
        )
        client.upsert(
            "skill_smoke",
            wait=True,
            points=[
                models.PointStruct(id=1, vector=[1.0, 0.0, 0.0, 0.0], payload={"tag": "a"}),
                models.PointStruct(id=2, vector=[0.0, 1.0, 0.0, 0.0], payload={"tag": "b"}),
            ],
        )
        result = client.query_points("skill_smoke", query=[1.0, 0.0, 0.0, 0.0], limit=1)
        assert result.points[0].id == 1, result.points
        converted = RestToGrpc.convert_query_interface(models.NearestQuery(nearest=[1.0, 2.0]))
        assert converted.WhichOneof("variant") == "nearest"
    finally:
        client.close()


def _persistent_smoke() -> None:
    from qdrant_client import QdrantClient, models

    with tempfile.TemporaryDirectory() as tmpdir:
        client = QdrantClient(path=tmpdir)
        try:
            client.create_collection(
                "persisted",
                vectors_config=models.VectorParams(size=2, distance=models.Distance.DOT),
            )
            client.upsert("persisted", wait=True, points=[models.PointStruct(id=1, vector=[1.0, 2.0])])
            assert client.count("persisted").count == 1
        finally:
            client.close()

        reopened = QdrantClient(path=tmpdir)
        try:
            assert reopened.count("persisted").count == 1
        finally:
            reopened.close()


async def _async_smoke() -> None:
    from qdrant_client import AsyncQdrantClient, models

    client = AsyncQdrantClient(":memory:")
    try:
        await client.create_collection(
            "async_skill_smoke",
            vectors_config=models.VectorParams(size=2, distance=models.Distance.EUCLID),
        )
        await client.upsert(
            "async_skill_smoke",
            wait=True,
            points=[models.PointStruct(id=1, vector=[0.0, 1.0])],
        )
        assert (await client.count("async_skill_smoke")).count == 1
    finally:
        await client.close()


def main() -> int:
    args = _build_parser().parse_args()
    print(f"qdrant-client {metadata.version('qdrant-client')}")
    if args.mode in ("local", "all"):
        _local_smoke()
        print("local: ok")
    if args.mode in ("persistent", "all"):
        _persistent_smoke()
        print("persistent: ok")
    if args.mode in ("async", "all"):
        asyncio.run(_async_smoke())
        print("async: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
