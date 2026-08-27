# Models Reference

`qdrant_client.models` re-exports the generated REST models plus inference input classes, so most application code should import from one namespace:

```python
from qdrant_client import models
```

Generated REST classes are pydantic models. In qdrant-client 1.18.0, the important request/config/input classes are strict about unknown fields (`extra="forbid"`), so constructor keyword spelling matters.

## Common Classes

| Purpose | Common models | Notes |
| --- | --- | --- |
| Collections | `VectorParams`, `SparseVectorParams`, `Distance`, `Datatype`, `MultiVectorConfig`, `HnswConfigDiff`, `QuantizationConfig` | Use for `vectors_config`, sparse vectors, and update diffs. `VectorParams(size=..., distance=models.Distance.COSINE)` is the usual dense-vector config. |
| Points | `PointStruct`, `Batch`, `PointVectors`, `SparseVector`, `NamedVector`, `NamedSparseVector` | `PointStruct` has `id`, `vector`, and optional `payload`; `Batch` has parallel `ids`, `vectors`, and optional `payloads`. |
| Filters | `Filter`, `FieldCondition`, `MatchValue`, `MatchAny`, `MatchExcept`, `Range`, `DatetimeRange`, `MinShould`, `NestedCondition`, `HasIdCondition`, `IsEmptyCondition`, `IsNullCondition` | `Filter.must`, `should`, and `must_not` accept one condition or a list; `min_should` uses `MinShould(conditions=[...], min_count=...)`. |
| Query inputs | `NearestQuery`, `RecommendQuery`, `DiscoverQuery`, `ContextQuery`, `FusionQuery`, `SampleQuery`, `FormulaQuery`, `RrfQuery`, `Prefetch`, `QueryRequest` | `query_points` and conversion helpers accept high-level query interface objects, dense vectors, sparse vectors, IDs, and inference objects depending on context. |
| Payload selection | `PayloadSelectorInclude`, `PayloadSelectorExclude`, `WithPayloadInterface`, `WithVector`, `OrderBy` | Many client methods also accept shorthand booleans or field lists; conversion normalizes these to gRPC selector messages. |
| Inference objects | `Document`, `Image`, `InferenceObject` | These are construction/schema objects here. Use the `inference` sub-skill for local FastEmbed or Cloud inference execution. |
| Responses | `ScoredPoint`, `Record`, `QueryResponse`, `CountResult`, `UpdateResult`, `CollectionInfo`, `CollectionsResponse` | Response classes are useful for type-aware tests and conversion round trips. |

## Constructor Patterns

Dense collection config:

```python
from qdrant_client import models

vectors_config = models.VectorParams(size=384, distance=models.Distance.COSINE)
```

Point with payload and dense vector:

```python
point = models.PointStruct(
    id=1,
    vector=[0.1, 0.2, 0.3],
    payload={"kind": "note", "public": True},
)
```

Named dense plus sparse vectors:

```python
point = models.PointStruct(
    id="doc-1",
    vector={
        "dense": [0.1, 0.2, 0.3],
        "sparse": models.SparseVector(indices=[4, 19], values=[0.8, 0.2]),
    },
    payload={"section": "intro"},
)
```

Nested filter with `min_should`:

```python
filter_ = models.Filter(
    must=[models.FieldCondition(key="kind", match=models.MatchValue(value="article"))],
    min_should=models.MinShould(
        conditions=[
            models.FieldCondition(key="lang", match=models.MatchAny(any=["en", "de"])),
            models.FieldCondition(key="published", match=models.MatchValue(value=True)),
        ],
        min_count=1,
    ),
)
```

Query request with prefetch and fusion:

```python
query = models.QueryRequest(
    prefetch=[
        models.Prefetch(query=models.NearestQuery(nearest=[0.1, 0.2, 0.3]), using="dense", limit=50),
        models.Prefetch(
            query=models.NearestQuery(
                nearest=models.SparseVector(indices=[10, 22], values=[0.7, 0.3])
            ),
            using="sparse",
            limit=50,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=10,
    with_payload=True,
)
```

## Enums and Strings

Use enum members when available:

```python
models.Distance.COSINE
models.Distance.DOT
models.Fusion.RRF
models.PayloadSchemaType.KEYWORD
models.RecommendStrategy.AVERAGE_VECTOR
```

Most generated enum classes inherit from `str`, so serialized values are lower-case or API-specific strings such as `"Cosine"` or `"rrf"`. Prefer enum members in Python code to avoid spelling and capitalization mismatches.

## Strict Validation and Pydantic Versions

qdrant-client includes compatibility helpers for pydantic v1 and v2:

- `construct(model_class, **values)` wraps `construct`/`model_construct` for trusted internal construction.
- `to_dict(model, **kwargs)` wraps `dict`/`model_dump`.
- `model_json_schema(model_class)` wraps `schema_json`/`model_json_schema`.
- `model_fields(model_class)` and `model_fields_set(model)` hide v1/v2 attribute differences.
- `to_jsonable_python(value)` serializes pydantic-supported values such as `date` and `datetime` for payload conversion.

For user data, prefer normal model constructors so validation catches mistakes. Use compatibility helpers when writing tooling that must work under either pydantic major version.

## Payload and Filter Schemas

Payloads are plain JSON-like dictionaries: strings, integers, floats, booleans, `None`, lists, dicts, and date/datetime values that can be serialized. Conversion maps them to gRPC `Value` messages and back.

Filter field names are payload keys, not Python object paths. Use nested filters when the payload itself contains arrays or nested objects:

```python
nested = models.NestedCondition(
    nested=models.Nested(
        key="diet",
        filter=models.Filter(
            must=[models.FieldCondition(key="food", match=models.MatchValue(value="meat"))]
        ),
    )
)
```

`Filter` itself is recursive and can appear as a condition in another filter. Keep recursion shallow in examples and debugging output so it remains readable.

## Query and Prefetch Shapes

`Prefetch` and `QueryRequest` share many fields: `prefetch`, `query`, `using`, `filter`, `params`, `score_threshold`, `limit`, and `lookup_from`. `QueryRequest` additionally supports `shard_key`, `offset`, `with_vector`, and `with_payload`.

A single `Prefetch` is accepted in model construction, but top-level gRPC `QueryPoints` stores prefetches as a repeated list. When debugging conversion, expect a single `QueryRequest.prefetch` to become a one-item `grpc.QueryPoints.prefetch` list.

## Inference Schema Parser

`ModelSchemaParser` scans pydantic JSON schema for fields containing `Document`, `Image`, or `InferenceObject`. It is stateful and caches parsed model names, string paths, and `FieldPath` objects.

Useful model families for schema parsing include `PointStruct`, `Batch`, `Prefetch`, `QueryRequest`, `QueryRequestBatch`, `RecommendQuery`, `DiscoverQuery`, and update operation models. `Filter` recursion is intentionally excluded from expensive recursive inference-object scans unless it contains relevant inference paths.

Use schema parsing to locate inference object fields, not to perform embedding. Route embedding execution to the `inference` sub-skill.
