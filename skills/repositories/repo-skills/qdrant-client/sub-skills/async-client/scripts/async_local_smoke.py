"""Deterministic AsyncQdrantClient local-mode smoke check."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from qdrant_client import AsyncQdrantClient, models


COLLECTION_NAME = "async_skill_smoke"
ALIAS_NAME = "async_skill_smoke_alias"


async def run_smoke() -> dict[str, Any]:
    client = AsyncQdrantClient(":memory:")
    try:
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=3, distance=models.Distance.COSINE),
        )
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(id=1, vector=[1.0, 0.0, 0.0], payload={"kind": "alpha"}),
                models.PointStruct(id=2, vector=[0.0, 1.0, 0.0], payload={"kind": "beta"}),
                models.PointStruct(id=3, vector=[0.0, 0.0, 1.0], payload={"kind": "gamma"}),
            ],
        )
        await client.set_payload(
            collection_name=COLLECTION_NAME,
            payload={"reviewed": True},
            points=[1, 2],
        )
        responses = await client.query_batch_points(
            collection_name=COLLECTION_NAME,
            requests=[
                models.QueryRequest(query=[1.0, 0.0, 0.0], limit=1),
                models.QueryRequest(query=[0.0, 1.0, 0.0], limit=1),
            ],
        )
        await client.update_collection_aliases(
            change_aliases_operations=[
                models.CreateAliasOperation(
                    create_alias=models.CreateAlias(
                        collection_name=COLLECTION_NAME,
                        alias_name=ALIAS_NAME,
                    )
                )
            ]
        )
        aliases_before_delete = await client.get_aliases()
        await client.update_collection_aliases(
            change_aliases_operations=[
                models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=ALIAS_NAME))
            ]
        )
        aliases_after_delete = await client.get_aliases()
        reviewed = await client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[1, 2],
            with_payload=["reviewed", "kind"],
        )
        count = await client.count(collection_name=COLLECTION_NAME)

        query_ids = [response.points[0].id for response in responses]
        alias_names_before = [alias.alias_name for alias in aliases_before_delete.aliases]
        alias_names_after = [alias.alias_name for alias in aliases_after_delete.aliases]
        reviewed_flags = [record.payload.get("reviewed") for record in reviewed]

        assert count.count == 3
        assert query_ids == [1, 2]
        assert reviewed_flags == [True, True]
        assert ALIAS_NAME in alias_names_before
        assert ALIAS_NAME not in alias_names_after

        return {
            "ok": True,
            "collection": COLLECTION_NAME,
            "count": count.count,
            "query_ids": query_ids,
            "reviewed_flags": reviewed_flags,
            "alias_removed": ALIAS_NAME not in alias_names_after,
        }
    finally:
        await client.close()


def main() -> None:
    result = asyncio.run(run_smoke())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
