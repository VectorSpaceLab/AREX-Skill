# Vector-indexing API reference

Read this reference for the verified local `InMemoryExactNNIndex` surface and the common `BaseDocIndex` contract. For document schema details, route to [`document-modeling`](../../document-modeling/).

## Verified local API

```python
from docarray.index import InMemoryExactNNIndex
```

The live inspected constructor is:

```text
InMemoryExactNNIndex(docs=None, db_config=None, **kwargs)
```

Parameterize the index with a `BaseDoc` schema:

```python
index = InMemoryExactNNIndex[MyDoc](docs=None)
```

The important methods and verified signatures are:

| Method | Signature shape | Result/notes |
| --- | --- | --- |
| `index` | `index(docs: BaseDoc | Sequence[BaseDoc], **kwargs)` | Adds documents; an existing ID is updated rather than duplicated. |
| `num_docs` | `num_docs() -> int` | Current indexed document count. |
| `find` | `find(query, search_field: str = "", limit: int = 10, **kwargs)` | Returns a `FindResult` with `.documents` and `.scores`; tuple unpacking also works. Query may be a raw tensor or schema-compatible document. |
| `find_batched` | `find_batched(queries, search_field: str = "", limit: int = 10, **kwargs)` | Returns per-query document lists and score lists. |
| `filter` | `filter(filter_query, limit: int = 10, **kwargs)` | Returns a `DocList` selected by DocArray query-language operators. |
| `filter_batched` | `filter_batched(filter_queries, limit: int = 10, **kwargs)` | Returns one filtered `DocList` per query. |
| `find_subindex` | `find_subindex(query, subindex: str = "", search_field: str = "", limit: int = 10, **kwargs)` | Searches a nested `DocList` subindex and returns root docs, subdocs, and scores. |
| `build_query` | `build_query()` | Returns the backend query builder. |
| `execute_query` | `execute_query(query, *args, **kwargs)` | Executes the query object built by the query builder. |
| `persist` | `persist(file: Optional[str] = None) -> None` | Writes the local index to a binary file. |
| `__getitem__` | `index[id]` or `index[ids]` | Reads one or many documents by ID. |
| `__delitem__` | `del index[id]` or `del index[ids]` | Deletes one or many documents by ID. |

## Schema requirements

- Every index is generic over a `BaseDoc` type. Omitting `InMemoryExactNNIndex[MyDoc]` raises a type error during construction.
- Vector fields should declare dimensions, for example `embedding: NdArray[128]`; `Field(dim=128)` is an alternative for backends that use field configuration.
- Index and data schemas are compatible when they are the same class, have the same field names/types, or the data field types are subclasses of the index field types.
- `Field(space=...)` configures local vector metric choices: `cosine_sim` (default), `euclidean_dist`, or `sqeuclidean_dist`.
- `Field(col_type=...)` is primarily for backend-specific column mappings; validate it against that backend's supported types.
- Predefined docs such as `TextDoc` have unparameterized embeddings. Subclass or redefine the embedding as `NdArray[n]`/`Field(dim=n)` before depending on vector indexing.

## Query builder contract

The local query builder collects operations and returns a query object consumed by `execute_query()`:

```python
query = (
    index.build_query()
    .filter(filter_query={"price": {"$lte": 3}})
    .find(query=np.zeros(128), search_field="embedding", limit=5)
    .build()
)
documents, scores = index.execute_query(query)
```

`InMemoryExactNNIndex` supports `find`, `find_batched`, and `filter` in its builder. It does not support text search. Backend query-builder composition varies; use [optional-backends.md](optional-backends.md) before copying a hybrid query to another service.

## Filter operators

The local in-memory backend delegates to DocArray's filter language. Common operators evidenced by tests/docs include:

- `{"field": {"$eq": value}}`
- `{"field": {"$neq": value}}`
- `{"field": {"$lt": value}}`
- `{"field": {"$lte": value}}`
- `{"field": {"$gt": value}}`
- `{"field": {"$gte": value}}`

Use a typed field name and validate the filter on a tiny fixture before applying it to a larger index.
