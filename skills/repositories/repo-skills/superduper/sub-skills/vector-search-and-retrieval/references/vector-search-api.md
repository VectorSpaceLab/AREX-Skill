# Vector Search API Reference

This reference summarizes the Superduper vector-search APIs needed for `VectorIndex` workflows. It intentionally stops at the common vector-search contract; plugin installation, credentials, and service lifecycle are owned by plugin-specific guidance.

## Public Constructors And Signatures

The installed Superduper package exposes these relevant constructors:

```python
from superduper import Listener, ObjectModel, Table, VectorIndex
from superduper.base.datatype import Array, Vector
from superduper.backends.base.vector_search import VectorItem
from superduper.backends.local.vector_search import InMemoryVectorSearcher
```

Common signatures:

```python
ObjectModel(
    identifier: str,
    *,
    object: callable,
    datatype: str | None = None,
    predict_kwargs: dict = {},
    num_workers: int = 0,
    serve: bool = False,
)

Listener(
    identifier: str,
    *,
    key,
    model,
    select=None,
    predict_kwargs: dict = {},
    flatten: bool = False,
)

VectorIndex(
    identifier: str,
    *,
    indexing_listener,
    compatible_listener=None,
    measure: str = "cosine",
    metric_values: dict | None = {},
)

Vector(dtype: str = "float64", shape: int)
Array(dtype: str = "float64", shape: int | tuple[int, ...])
VectorItem(id: str, vector)
```

`Table(identifier, fields={...}, primary_id="id")` is the common way to declare source fields before inserting rows. The exact Datalayer connection/configuration belongs outside this sub-skill.

## Vector Datatypes

Use a concrete vector datatype whenever a model output will be indexed:

```python
ObjectModel("embed", object=embed, datatype="vector[int:300]")
ObjectModel("embed32", object=embed32, datatype="vector[float:32]")
```

The string parser recognizes `vector[dtype:shape]`, where `shape` is a single integer. This creates a vector datatype with a `.shape` used by `VectorIndex.dimensions`.

Use `Array` or `array[...]` for table fields that store numpy arrays directly:

```python
from superduper import Table
from superduper.base.datatype import Array, Vector

db.apply(Table("features", fields={
    "id": "str",
    "raw": "array[float:32]",
    "embedding": Array(dtype="float64", shape=(32,)),
}))

# Direct class form for model/datatype construction when needed:
vector_datatype = Vector(dtype="float", shape=300)
```

Guidance:

- Use `vector[...]` or `Vector` for model outputs that feed a `VectorIndex`.
- Use `array[...]` or `Array` for persisted numpy-like source fields.
- Match `dtype` and returned data type where the data backend enforces encoding strictly.
- Keep output length equal to the declared shape every time; variable-length embeddings are not valid for one vector index.

## Listener Output Contract

A `Listener` writes to a generated output table named by `listener.outputs`. Its output table schema includes:

- one vector field named by `listener.outputs`, using the listener model datatype;
- `_source`, the source row ID as a string.

`VectorIndex.setup()` validates that the indexing listener has an output table whose schema contains a field with a non-empty `shape`. If this fails, the model probably lacks a vector datatype or the listener is not set up correctly.

`VectorIndex.get_vectors(ids=None)` reads rows from the listener output table and extracts the generated output field. Rows missing the generated output key are skipped and logged as missing outputs.

## VectorIndex API

Important `VectorIndex` attributes and methods:

| API | Purpose |
| --- | --- |
| `indexing_listener` | Required listener whose outputs are copied into the vector-search backend. |
| `compatible_listener` | Optional listener/model/key used only to embed query documents with a different key. |
| `measure` | Similarity measure. Prefer `"cosine"`, `"dot"`, or `"l2"`. |
| `cdc_table` | Set from the indexing listener outputs. |
| `dimensions` | Reads vector dimensionality from the indexing listener output schema. |
| `models_keys` | Returns the indexing listener and compatible listener models/keys used for query embedding. |
| `get_vectors(ids=None)` | Returns vector payloads from listener outputs for backend insertion. |
| `copy_vectors(ids=None)` | Triggered on apply/insert/update to add vectors to the backend. |
| `delete_vectors(ids=None)` | Triggered on delete to remove backend vectors. |
| `get_nearest(like, outputs=None, ids=None, n=100)` | Embeds the query document and delegates nearest-neighbor search. |
| `cleanup()` | Drops this index from the vector-search backend. |

`VectorIndex.get_vector(...)` chooses a model by matching keys in the `like` document against the listener keys. For singleton models, a key should be a single string.

## Query API

The user-facing query method is `like`:

```python
query = db["documents"].like({"x": 50}, vector_index="vector_index", n=10)
rows = query.select().execute()
```

Semantics:

- `r` is the query document used to build the query embedding.
- `vector_index` is the identifier of a persisted `VectorIndex` component.
- `n` is the maximum number of nearest neighbors to return.
- Result rows receive a `score` value and are sorted descending by score.

`like` can appear before or after filters in a decomposed query. When the query has a preceding filter, Superduper can pass the filtered IDs as `within_ids` to the nearest-neighbor call. When `like` is first, the backend finds nearest IDs and the data backend filters rows to those IDs afterward.

For direct lower-level use, the Datalayer exposes:

```python
ids, scores = db.select_nearest(
    like={"x": 50},
    vector_index="vector_index",
    ids=None,
    outputs=None,
    n=10,
)
```

Most workflows should prefer table `.like(...).select().execute()` because it returns full rows with scores.

## Measures

Supported local measure functions are:

| Measure | Local score meaning | Notes |
| --- | --- | --- |
| `cosine` | Cosine similarity | Stored vectors are normalized for local search. |
| `dot` | Dot product | Higher is better. |
| `l2` | Negative Euclidean distance | Higher is better because distances are negated. |

An enum value named `css` exists in the base measure enum, but the local measure dictionary does not implement it. Do not use `css` unless the selected backend has been separately verified to accept it.

## Backend Contract

All vector-search backends conform to the same high-level operations:

```python
backend.add(uuid=index_uuid, vectors=[VectorItem(id="1", vector=vec)])
backend.delete(uuid=index_uuid, ids=["1"])
ids, scores = backend.find_nearest_from_array(
    h=query_vector,
    component="VectorIndex",
    vector_index="vector_index",
    n=10,
    within_ids=(),
)
ids, scores = backend.find_nearest_from_id(
    id="1",
    component="VectorIndex",
    vector_index="vector_index",
    n=10,
)
backend.describe(component="VectorIndex", vector_index="vector_index")
```

The local cluster builds a `LocalVectorSearchBackend` around a `VectorSearcher` implementation selected from the configured vector-search engine. The default local path uses an in-memory vector searcher.

## In-Memory Searcher API

`InMemoryVectorSearcher` can be used to test vector-search semantics without a Datalayer:

```python
import numpy as np
from superduper.backends.base.vector_search import VectorItem
from superduper.backends.local.vector_search import InMemoryVectorSearcher

searcher = InMemoryVectorSearcher(
    identifier="demo",
    dimensions=3,
    measure="cosine",
)
searcher.add([
    VectorItem(id="a", vector=np.array([1.0, 0.0, 0.0])),
    VectorItem(id="b", vector=np.array([0.0, 1.0, 0.0])),
])
ids, scores = searcher.find_nearest_from_array(np.array([1.0, 0.0, 0.0]), n=1)
```

Operational details:

- `add(items)` inserts or replaces vectors by ID.
- `delete(ids)` removes vectors by ID.
- `list()` returns indexed IDs.
- `describe()` returns the index UUID, dimensions, measure, and size.
- `find_nearest_from_id(id, n, within_ids)` looks up the stored vector by ID and then searches by array.
- `find_nearest_from_array(h, n, within_ids)` returns nearest IDs and sorted scores. Be aware that the local implementation truncates IDs to `n` but can return a raw sorted score list longer than `n`; Datalayer table queries zip IDs and scores before attaching `score` to result rows.
- If no vectors are loaded, nearest-neighbor search returns empty lists and logs an error.

## Optional Vector-Search Backends

The repository includes optional vector-search plugins whose classes implement the same general searcher contract:

| Backend | Typical engine value | Notes |
| --- | --- | --- |
| Local in-memory | `local` | No external service; best for CPU smoke tests and small local workflows. |
| Qdrant | `qdrant` or `qdrant://...` | Can use in-memory client mode or a service, depending on configuration. |
| ChromaDB | `chromadb://localhost:<port>` | The implementation expects a local ChromaDB HTTP service. |
| Lance | `lance` | Stores Lance datasets under a local vector-index home. |
| MongoDB Atlas | MongoDB/Atlas data backend integration | Requires MongoDB vector-search capabilities and service credentials. |
| Snowflake | Snowflake data backend integration | Uses Snowflake vector search; requires Snowflake setup. |

Use this table only to reason about routing and API compatibility. Installation, credentials, service health, and backend-specific indexes must be handled by plugin guidance.
