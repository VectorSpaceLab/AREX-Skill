# VectorIndex Workflow

This reference gives the standard Superduper pattern for building a vector index from listener-generated embeddings and retrieving nearest neighbors. It assumes the Datalayer itself is already configured by the caller or by the repo skill area responsible for Datalayer setup.

## Core Mental Model

A Superduper vector retrieval workflow has four cooperating pieces:

1. **Source records** live in a `Table` and contain the raw field to embed, such as `x`, `text`, or a listener output from an upstream chunking step.
2. An **indexing model** turns one source field into a fixed-length vector. For vector search, declare a concrete vector datatype such as `vector[int:300]` or `vector[float:32]`.
3. An **indexing listener** runs the model over the source `select` and stores outputs in a generated output table. `VectorIndex` reads these listener outputs and copies them into the vector-search backend.
4. A **VectorIndex** names the index, records the indexing listener, optionally records a compatible listener for query-time embeddings, and declares the similarity measure.

The normal retrieval entry point is a table query:

```python
rows = (
    db["documents"]
    .like({"x": 50}, vector_index="vector_index", n=10)
    .select()
    .execute()
)
```

The returned rows are sorted by vector-search score and include a `score` field.

## Minimal Indexing Pattern

```python
import numpy as np
from superduper import Listener, ObjectModel, Table, VectorIndex

DIMENSION = 300

def embed_x(x: int):
    vector = [0] * DIMENSION
    vector[int(x) % DIMENSION] = 1
    return np.array(vector)

db.apply(Table("documents", fields={"id": "str", "x": "int", "label": "int"}))
db["documents"].insert([
    {"id": str(i), "x": i, "label": int(i % 2 == 0)}
    for i in range(100)
])

embedding_model = ObjectModel(
    identifier="embedding-model",
    object=embed_x,
    datatype="vector[int:300]",
)

indexing_listener = Listener(
    identifier="embedding-listener",
    model=embedding_model,
    key="x",
    select=db["documents"].select(),
)

vector_index = VectorIndex(
    identifier="vector_index",
    indexing_listener=indexing_listener,
    measure="cosine",
)

db.apply(vector_index)
```

Notes:

- The indexing model datatype is not optional for reliable `VectorIndex` setup. The index discovers its dimensionality from the listener output table schema.
- `Listener.select` should be a source query for indexing. A listener with `select=None` is useful for compatible query-time embedding, not for backfilling stored vectors.
- Keep the model output length exactly equal to the datatype shape. A `vector[int:300]` model should always return 300 values.
- `measure` should be `"cosine"`, `"dot"`, or `"l2"` unless a selected backend has been separately verified for another value.

## Query-Time Compatible Listener

Use `compatible_listener` when the query arrives under a different key than the indexed data. The compatible listener does not need to index records; it supplies a query-time model/key mapping so `VectorIndex` can embed a `like` document with a different shape of input.

```python
compatible_model = ObjectModel(
    identifier="query-embedding-model",
    object=lambda y: embed_x(-int(y)),
)

compatible_listener = Listener(
    identifier="query-embedding-listener",
    model=compatible_model,
    key="y",
    select=None,
)

vector_index = VectorIndex(
    identifier="vector_index",
    indexing_listener=indexing_listener,
    compatible_listener=compatible_listener,
    measure="cosine",
)
```

Then both of these can target the same stored vectors:

```python
# Uses the indexing listener/model because key "x" is present.
rows_from_index_key = (
    db["documents"].like({"x": 50}, vector_index="vector_index", n=10)
    .select()
    .execute()
)

# Uses the compatible listener/model because key "y" is present.
rows_from_query_key = (
    db["documents"].like({"y": -50}, vector_index="vector_index", n=10)
    .select()
    .execute()
)
```

Compatible-listener rules:

- The compatible model must produce the same dimension as the indexing model.
- The `like` dictionary must contain the compatible listener key exactly.
- For singleton models, the listener key should be a string. Multi-argument signatures require keys that match the model signature.
- If both indexing and compatible keys are present in the same query document, keep key names unambiguous and test which listener is selected before relying on production behavior.

## RAG-Style Listener Output Indexing

A common retrieval-augmented generation pattern indexes outputs from an upstream listener, such as a chunking or preprocessing listener:

```python
# upstream_listener writes chunk text into upstream_listener.outputs
embedding_listener = Listener(
    identifier="embedding-listener",
    key=upstream_listener.outputs,
    select=db[upstream_listener.outputs].select(),
    model=embedding_model,
    upstream=[upstream_listener],
)

vector_index = VectorIndex(
    identifier="chunk-vector-index",
    indexing_listener=embedding_listener,
)

context_query = (
    db[upstream_listener.outputs]
    .select()
    .like({upstream_listener.outputs: "question text"}, vector_index="chunk-vector-index", n=5)
)
```

This pattern indexes the generated chunk/output table rather than the original table. Keep the Datalayer/table setup and any external LLM or embedding-service configuration in the appropriate sibling skill areas.

## Add, Delete, Copy, and Recovery Notes

`VectorIndex` is a CDC component. Its important operational methods are:

- `copy_vectors(ids=None)`: reads listener outputs and adds `VectorItem` objects to the vector-search backend.
- `delete_vectors(ids=None)`: removes vectors from the backend for deleted source IDs.
- `get_vectors(ids=None)`: returns dictionaries containing `id` and `vector` from the listener output table.
- `cleanup()`: drops the vector index from the backend during teardown.

Practical implications:

- If source records are inserted before `db.apply(vector_index)`, the initial apply can build listener outputs and copy vectors.
- If source records are inserted after the index exists, the CDC/listener pipeline must run before nearest-neighbor results reflect the new records.
- Local vector search can recover after restart by reinitializing the cluster vector-search backend; it scans persisted `VectorIndex` components, compares listener output IDs with deployed vector IDs, and copies missing vectors.
- Empty or zero-score results after adding data usually mean new records were not embedded and copied yet, not that the query API changed.

## Local Vector Search Behavior

The local searcher stores vectors in memory and supports `cosine`, `dot`, and `l2` measures.

- For `cosine`, stored vectors are normalized once during setup; query vectors are normalized during scoring.
- `dot` returns dot-product scores.
- `l2` returns negative Euclidean distance, so larger scores are still better.
- The public backend contract is nearest IDs plus scores sorted by descending score. In the local in-memory implementation, top IDs are truncated to `n`, while the raw sorted score list can be longer than the ID list; table-query execution zips IDs and scores so result rows still receive the top scores.
- `within_ids` restricts scoring to a subset after the query is decomposed.
- Adding an ID that already exists replaces the old vector in the in-memory index.
- Deleting IDs removes vectors from the in-memory matrix; delete only IDs known to be present.

## Verification Checklist For A New Workflow

Before handing off a vector retrieval workflow, verify these points:

- The embedding model has a vector datatype with the intended shape.
- At least one listener output row exists and contains the generated output field.
- `VectorIndex.dimensions` equals the model output length.
- `table.like(...).select().execute()` returns non-empty rows for an indexed example.
- The top hit for an exact or near-exact query has a high score.
- Adding a new record is followed by listener output generation and vector copying before expecting it to appear as the top hit.
- Any compatible listener is tested with a query key that is different from the indexing listener key.
