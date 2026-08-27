# Local Mode Reference

`qdrant-client` local mode embeds an in-process Qdrant-like store behind the same high-level `QdrantClient` methods used for server mode. It is best for tests, prototypes, demos, notebooks, CI fixtures, and small local experiments. It is not a replacement for a long-running multi-process Qdrant server.

## Client Selection

Use one of these forms:

```python
from qdrant_client import QdrantClient

memory_client = QdrantClient(":memory:")
persistent_client = QdrantClient(path="./local-qdrant-store")
```

Important constructor rules:

- `QdrantClient(":memory:")` creates an ephemeral local store. Data disappears when the process exits or the client is discarded.
- `QdrantClient(path="...")` creates or opens a persistent local store at that directory path.
- Only one of `location`, `url`, `host`, or `path` may be set. Passing more than one raises a constructor error.
- A non-`:memory:` string passed as `location` is treated like a server URL, not a local directory. Use `path=...` for persistent local mode.
- `prefer_grpc`, server `url`, API keys, Cloud inference, and raw transport clients are server/Cloud concerns; do not mix them into local-mode recipes.

Always close persistent clients when a script finishes:

```python
client = QdrantClient(path="./local-qdrant-store")
try:
    ...
finally:
    client.close()
```

## Dense In-Memory Recipe

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
client.create_collection(
    collection_name="places",
    vectors_config=models.VectorParams(size=4, distance=models.Distance.DOT),
)
client.upsert(
    collection_name="places",
    points=[
        models.PointStruct(id=1, vector=[0.05, 0.61, 0.76, 0.74], payload={"city": "Berlin"}),
        models.PointStruct(id=2, vector=[0.19, 0.81, 0.75, 0.11], payload={"city": ["Berlin", "London"]}),
        models.PointStruct(id=3, vector=[0.18, 0.01, 0.85, 0.80], payload={"city": ["London", "Moscow"]}),
    ],
)
hits = client.query_points(
    collection_name="places",
    query=[0.2, 0.1, 0.9, 0.7],
    query_filter=models.Filter(
        must=[models.FieldCondition(key="city", match=models.MatchValue(value="London"))]
    ),
    limit=3,
).points
assert [point.id for point in hits] == [3, 2]
client.close()
```

Local payload filters are evaluated in Python and support common filter shapes such as `match`, numeric/date ranges, `values_count`, geo filters, `has_id`, `has_vector`, `is_null`, `is_empty`, `must`, `should`, `must_not`, and nested filters. For dotted payload keys that are literal field names rather than paths, quote the segment, for example `the."nested.key"`.

## Persistent Store Recipe

```python
from pathlib import Path
from qdrant_client import QdrantClient, models

store = Path("./local-qdrant-store")
client = QdrantClient(path=str(store))
client.create_collection(
    "persisted",
    vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE),
    sparse_vectors_config={"text": models.SparseVectorParams()},
    metadata={"purpose": "local smoke"},
)
client.upsert(
    "persisted",
    points=[
        models.PointStruct(
            id=1,
            vector={"": [1.0, 0.0], "text": models.SparseVector(indices=[1, 3], values=[0.5, 1.0])},
            payload={"tag": "first"},
        )
    ],
)
assert client.count("persisted").count == 1
client.close()

reopened = QdrantClient(path=str(store))
assert reopened.count("persisted").count == 1
records, _ = reopened.scroll("persisted", limit=10, with_vectors=True)
assert records[0].vector["text"].indices == [1, 3]
reopened.close()
```

Persistent local mode stores metadata, collection configuration, dense vectors, sparse vectors, payloads, and updated sparse-vector modifiers. It takes an exclusive filesystem lock on the store directory, so do not open the same `path` twice at the same time.

## Sparse Vectors

Create sparse-only collections by using an empty dense `vectors_config` and a named `sparse_vectors_config`:

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
client.create_collection(
    "sparse_docs",
    vectors_config={},
    sparse_vectors_config={"text": models.SparseVectorParams()},
)
client.upsert(
    "sparse_docs",
    points=[
        models.PointStruct(
            id=1,
            vector={"text": models.SparseVector(indices=[1, 5], values=[0.2, 0.8])},
            payload={"city": "Berlin"},
        ),
        models.PointStruct(
            id=2,
            vector={"text": models.SparseVector(indices=[1, 7], values=[0.1, 0.9])},
            payload={"city": "London"},
        ),
    ],
)
hits = client.query_points(
    "sparse_docs",
    using="text",
    query=models.SparseVector(indices=[1, 7], values=[0.1, 1.0]),
    query_filter=models.Filter(
        must=[models.FieldCondition(key="city", match=models.MatchValue(value="London"))]
    ),
    limit=2,
).points
assert hits[0].id == 2
client.close()
```

Sparse vector queries use the named vector in `using="text"`. Local mode sorts sparse query indices internally for persisted vectors and skips undefined sparse scores.

## Named Dense Vectors

Named dense vectors use a mapping in `vectors_config`, and points must provide vectors under the same names:

```python
client.create_collection(
    "media",
    vectors_config={
        "text": models.VectorParams(size=4, distance=models.Distance.COSINE),
        "image": models.VectorParams(size=4, distance=models.Distance.COSINE),
    },
)
client.upsert(
    "media",
    points=[
        models.PointStruct(id=1, vector={"text": [1, 0, 0, 0], "image": [1, 0, 0, 0]}),
        models.PointStruct(id=2, vector={"text": [0, 1, 0, 0], "image": [0, 1, 0, 0]}),
    ],
)
text_hits = client.query_points("media", using="text", query=[1, 0, 0, 0], limit=2).points
image_hits = client.query_points("media", using="image", query=[0, 1, 0, 0], limit=2).points
```

An unnamed dense vector in a single-vector collection is addressed with normal list queries. In mixed/named-vector collections, pass `using=<vector-name>` to avoid querying the wrong vector.

## Multivectors

Local collections support multivectors by adding a `multivector_config` to a vector definition. The common comparator is `MAX_SIM`:

```python
client.create_collection(
    "passages",
    vectors_config={
        "colbert": models.VectorParams(
            size=3,
            distance=models.Distance.DOT,
            multivector_config=models.MultiVectorConfig(
                comparator=models.MultiVectorComparator.MAX_SIM
            ),
        )
    },
)
client.upsert(
    "passages",
    points=[
        models.PointStruct(id=1, vector={"colbert": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]}),
        models.PointStruct(id=2, vector={"colbert": [[0.0, 0.0, 1.0], [0.5, 0.5, 0.0]]}),
    ],
)
hits = client.query_points(
    "passages",
    using="colbert",
    query=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    limit=2,
).points
assert hits[0].id == 1
```

Local mode distinguishes dense vectors, sparse vectors, and multivectors by collection configuration and query shape. If the name is missing from the expected vector family, it raises a clear `Dense vector ... is not found`, `Sparse vector ... is not found`, or `Multivector ... is not found` error.

## Fusion and Score Thresholds

Local query execution supports prefetch-based fusion. For reciprocal-rank fusion or distribution-based score fusion, provide prefetches and then a fusion query:

```python
hits = client.query_points(
    "media",
    prefetch=[
        models.Prefetch(query=[1, 0, 0, 0], using="text", limit=10),
        models.Prefetch(query=[1, 0, 0, 0], using="image", limit=10),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    score_threshold=0.45,
    limit=10,
).points
```

Use `score_threshold` after confirming the scale of the local query type. Dense distance direction depends on distance metric, while fusion scores are filtered as higher-is-better. Local fusion without prefetches raises an error because there are no result sources to merge.

## Local Versus Server Mode

Start local when you need fast setup, deterministic tests, single-process examples, or temporary persistence. Move to Qdrant Server or Qdrant Cloud when any of these become true:

- The collection grows beyond small prototype size. Local mode warns after more than 20,000 points and recommends Docker or Cloud for better performance.
- More than one process, worker, notebook, or service must access the same data directory.
- You need raw REST/gRPC clients, networked clients, authentication, TLS, service compatibility checks, snapshots via server APIs, or production observability.
- You need server-like durability, indexing, replication, sharding, payload-index performance, or operational behavior.
- You need Cloud inference. Local `QdrantClient` rejects `cloud_inference=True`; use FastEmbed/local inference or switch to Cloud.

For a migration-friendly prototype, keep collection names, `models.VectorParams`, `sparse_vectors_config`, payload schema assumptions, and point IDs explicit. Then replace `QdrantClient(":memory:")` or `QdrantClient(path=...)` with a server client constructor and keep high-level collection/point/query methods the same.
