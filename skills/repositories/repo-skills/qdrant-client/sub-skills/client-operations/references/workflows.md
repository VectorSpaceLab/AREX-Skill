# Sync Client Operation Workflows

All examples use public qdrant-client imports only:

```python
from qdrant_client import QdrantClient, models
```

Use `QdrantClient(":memory:")` for safe local examples that do not need server-only features. For server or cloud connection setup, use the connection/transport sub-skill.

## Create a Collection and Insert Points

```python
client = QdrantClient(":memory:")
collection_name = "demo"

client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=3, distance=models.Distance.COSINE),
)

client.upsert(
    collection_name=collection_name,
    points=[
        models.PointStruct(id=1, vector=[0.1, 0.2, 0.3], payload={"color": "red", "price": 10}),
        models.PointStruct(id=2, vector=[0.2, 0.1, 0.4], payload={"color": "blue", "price": 20}),
        models.PointStruct(id=3, vector=[0.9, 0.1, 0.1], payload={"color": "red", "price": 30}),
    ],
    wait=True,
)

assert client.count(collection_name).count == 3
```

Prefer `create_collection` plus `collection_exists` checks for idempotent workflows. Avoid adding new uses of deprecated `recreate_collection` unless maintaining older code.

## Query with a Payload Filter

```python
hits = client.query_points(
    collection_name=collection_name,
    query=[0.1, 0.2, 0.25],
    query_filter=models.Filter(
        must=[
            models.FieldCondition(key="color", match=models.MatchValue(value="red")),
            models.FieldCondition(key="price", range=models.Range(gte=10, lte=30)),
        ]
    ),
    limit=5,
    with_payload=True,
)

for point in hits.points:
    print(point.id, point.score, point.payload)
```

Use `query_filter` for vector search filtering. Use `scroll_filter` for `scroll`, `count_filter` for `count`, and `facet_filter` for `facet`; these names are method-specific and are a common source of unknown-kwarg or no-filter bugs.

## Retrieve, Scroll, and Count

```python
records = client.retrieve(
    collection_name=collection_name,
    ids=[1, 2],
    with_payload=["color"],
    with_vectors=False,
)

page, next_offset = client.scroll(
    collection_name=collection_name,
    scroll_filter=models.Filter(
        must=[models.FieldCondition(key="color", match=models.MatchValue(value="red"))]
    ),
    limit=100,
    with_payload=True,
    with_vectors=False,
)

red_count = client.count(
    collection_name=collection_name,
    count_filter=models.Filter(
        must=[models.FieldCondition(key="color", match=models.MatchValue(value="red"))]
    ),
    exact=True,
).count
```

Use `scroll` rather than `query_points(query=None)` when iterating through a collection because `scroll` returns `next_offset` for pagination.

## Named Vectors and Multi-Vector Queries

```python
client.create_collection(
    collection_name="multi_demo",
    vectors_config={
        "text": models.VectorParams(size=3, distance=models.Distance.COSINE),
        "image": models.VectorParams(size=2, distance=models.Distance.DOT),
    },
)
client.upsert(
    collection_name="multi_demo",
    points=[
        models.PointStruct(
            id=1,
            vector={"text": [0.1, 0.2, 0.3], "image": [0.5, 0.1]},
            payload={"modality": "text", "tenant": "a"},
        ),
        models.PointStruct(
            id=2,
            vector={"text": [0.2, 0.2, 0.2], "image": [0.4, 0.4]},
            payload={"modality": "image", "tenant": "b"},
        ),
    ],
)

hits = client.query_points(
    collection_name="multi_demo",
    query=[0.1, 0.2, 0.25],
    using="text",
    query_filter=models.Filter(
        must=[models.FieldCondition(key="tenant", match=models.MatchValue(value="a"))]
    ),
    with_payload=True,
)
```

For a true multi-vector field, configure the vector with a multivector config and query with `list[list[float]]`. For a collection with several named vectors, always set `using` to the intended vector name unless using a model structure that already identifies it.

## Recommend, Discover, Context, and Fusion Queries

`query_points` is the universal endpoint for search, recommend, discover, context search, and fusion.

```python
recommend_hits = client.query_points(
    collection_name=collection_name,
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[1],
            negative=[2],
            strategy=models.RecommendStrategy.BEST_SCORE,
        )
    ),
    limit=5,
    with_payload=True,
)
```

Use discovery/context forms when a task asks for target-plus-context or positive/negative context pairs:

```python
discovery_hits = client.query_points(
    collection_name=collection_name,
    query=models.DiscoverQuery(
        discover=models.DiscoverInput(
            target=[0.1, 0.2, 0.25],
            context=[models.ContextPair(positive=1, negative=2)],
        )
    ),
    limit=5,
)
```

Use prefetch and fusion when combining multiple retrieval branches before a final query:

```python
fused = client.query_points(
    collection_name=collection_name,
    prefetch=[
        models.Prefetch(query=[0.1, 0.2, 0.3], limit=20),
        models.Prefetch(query=[0.9, 0.1, 0.1], limit=20),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    score_threshold=0.2,
    limit=5,
    with_payload=True,
)
```

If prefetch or query inputs are `models.Document` or `models.Image`, route the embedding setup and optional dependencies to the inference sub-skill.

## Batch Queries

```python
responses = client.query_batch_points(
    collection_name=collection_name,
    requests=[
        models.QueryRequest(query=[0.1, 0.2, 0.3], limit=3, with_payload=True),
        models.QueryRequest(
            query=models.RecommendQuery(recommend=models.RecommendInput(positive=[1], negative=[2])),
            limit=3,
        ),
    ],
)
```

Use `query_batch_points` to reduce network overhead for multiple independent query requests against the same collection. Use `query_points_groups` when the result should be grouped by a payload key.

## Payload Mutation

```python
client.set_payload(
    collection_name=collection_name,
    payload={"reviewed": True},
    points=[1, 2],
    wait=True,
)

client.set_payload(
    collection_name=collection_name,
    payload={"label": "fresh"},
    points=models.Filter(must=[models.FieldCondition(key="color", match=models.MatchValue(value="red"))]),
    key="metadata.flags",
)

client.delete_payload(collection_name=collection_name, keys=["reviewed"], points=[2])
client.clear_payload(collection_name=collection_name, points_selector=[3])
```

Use `set_payload` to merge/assign fields. Use `overwrite_payload` only when removing all unspecified existing payload keys is intentional.

## Payload Indexes and Facets

```python
client.create_payload_index(
    collection_name=collection_name,
    field_name="color",
    field_schema=models.PayloadSchemaType.KEYWORD,
    wait=True,
)

facet = client.facet(
    collection_name=collection_name,
    key="color",
    facet_filter=models.Filter(
        must=[models.FieldCondition(key="price", range=models.Range(gte=10))]
    ),
    limit=10,
    exact=True,
)
```

Create payload indexes for fields used heavily in filters, facets, or ordering. Use `delete_payload_index` to remove indexes that are no longer needed.

## Add and Remove Named Vector Slots

```python
client.create_vector_name(
    collection_name=collection_name,
    vector_name="short_text",
    vector_name_config=models.DenseVectorNameConfig(
        dense=models.DenseVectorConfig(size=3, distance=models.Distance.COSINE)
    ),
)

client.update_vectors(
    collection_name=collection_name,
    points=[models.PointVectors(id=1, vector={"short_text": [0.3, 0.2, 0.1]})],
)

client.delete_vector_name(collection_name=collection_name, vector_name="short_text")
```

Use the models/conversions sub-skill if a task requires translating between dense/sparse vector-name config variants or generated REST/gRPC structures in depth.

## Aliases

Alias updates are atomic across the submitted list of operations.

```python
client.update_collection_aliases(
    change_aliases_operations=[
        models.CreateAliasOperation(
            create_alias=models.CreateAlias(collection_name=collection_name, alias_name="demo_live")
        )
    ]
)

aliases = client.get_collection_aliases(collection_name=collection_name).aliases

client.update_collection_aliases(
    change_aliases_operations=[
        models.RenameAliasOperation(
            rename_alias=models.RenameAlias(old_alias_name="demo_live", new_alias_name="demo_previous")
        ),
        models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name="obsolete_alias")),
    ]
)
```

Use aliases for zero-downtime collection swaps or stable application names, and verify with `get_aliases` or `get_collection_aliases` after the update.

## Matrix Search

```python
matrix = client.search_matrix_pairs(
    collection_name=collection_name,
    query_filter=models.Filter(
        must=[models.FieldCondition(key="color", match=models.MatchValue(value="red"))]
    ),
    sample=50,
    limit=3,
)

offsets = client.search_matrix_offsets(collection_name=collection_name, sample=50, limit=3)
```

Use `search_matrix_pairs` when pair records are easier to consume. Use `search_matrix_offsets` when a compact offset-based representation fits downstream analysis. Specify `using` for named-vector collections.

## Snapshots

Snapshots are server-side administration operations and are not full local-mode backup tooling.

```python
snapshot = client.create_snapshot(collection_name=collection_name, wait=True)
if snapshot is not None:
    snapshots = client.list_snapshots(collection_name=collection_name)
    client.delete_snapshot(collection_name=collection_name, snapshot_name=snapshot.name, wait=True)
```

For full-storage snapshots, use `create_full_snapshot`, `list_full_snapshots`, and `delete_full_snapshot`. For shard snapshots, pass `shard_id` to `create_shard_snapshot`, `list_shard_snapshots`, `delete_shard_snapshot`, and `recover_shard_snapshot`. Verify target server permissions and storage policy before recovery because recovery can overwrite server-side collection data.

## Shard and Cluster-Adjacent Operations

```python
client.create_collection(
    collection_name="custom_shards",
    vectors_config=models.VectorParams(size=3, distance=models.Distance.COSINE),
    sharding_method=models.ShardingMethod.CUSTOM,
)
client.create_shard_key(collection_name="custom_shards", shard_key="tenant-a")
keys = client.list_shard_keys(collection_name="custom_shards")
```

Cluster methods such as `cluster_status`, `collection_cluster_info`, `cluster_collection_update`, `remove_peer`, `recover_current_peer`, `cluster_telemetry`, and `get_optimizations` are operational controls. Use them only against a server where the caller understands peer IDs, shard IDs, permissions, and the deployment topology.
