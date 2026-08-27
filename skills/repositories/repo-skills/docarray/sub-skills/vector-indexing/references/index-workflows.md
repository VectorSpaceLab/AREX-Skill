# Index workflows

This reference gives safe, local-first recipes for DocArray document indexes. It is intentionally independent of the original checkout.

## 1. Define a searchable schema

Use the same schema for the `DocList` and index, and put the per-document vector shape in the annotation:

```python
import numpy as np
from docarray import BaseDoc, DocList
from docarray.index import InMemoryExactNNIndex
from docarray.typing import NdArray

class Product(BaseDoc):
    title: str
    price: int
    embedding: NdArray[4]

docs = DocList[Product]([
    Product(title=f"item-{i}", price=i, embedding=np.array([i, i + 1, i + 2, i + 3]))
    for i in range(8)
])
index = InMemoryExactNNIndex[Product]()
index.index(docs)
```

The index stores one column per schema field. A vector's dimension is a schema contract, not the number of documents in the index.

## 2. Find by vector or document

```python
matches, scores = index.find(
    np.zeros(4),
    search_field="embedding",
    limit=3,
)

query_doc = Product(title="query", price=0, embedding=np.zeros(4))
result = index.find(query_doc, search_field="embedding", limit=3)
assert len(result.documents) == len(result.scores)
```

Use `find_batched()` for a matrix of raw queries or a typed `DocList` of query documents:

```python
queries = np.zeros((2, 4))
batched_docs, batched_scores = index.find_batched(
    queries, search_field="embedding", limit=3
)
assert len(batched_docs) == 2
```

Always name `search_field` when the schema has more than one tensor-like field. An empty or invalid field leads to a validation error or ambiguous backend choice.

## 3. Filter and combine operations

```python
cheap = index.filter({"price": {"$lte": 3}}, limit=10)
not_zero = index.filter({"price": {"$neq": 0}}, limit=10)
```

For in-memory hybrid retrieval, compose a pre-filter, vector search, and optional post-filter:

```python
query = (
    index.build_query()
    .filter(filter_query={"price": {"$gte": 2}})
    .find(query=np.zeros(4), search_field="embedding", limit=5)
    .filter(filter_query={"title": {"$eq": "item-2"}}, limit=5)
    .build()
)
matched_docs, matched_scores = index.execute_query(query)
```

The backend's query builder is not a general text-search engine. InMemoryExactNNIndex does not support `text_search()`; route text search to a backend that documents it.

When multiple candidates receive exactly equal scores, validate the result on a fixture with distinct scores or a restrictive filter. The in-tree implementation may sort `(score, document)` pairs and compare documents on a score tie.

## 4. Read, delete, and update by ID

```python
ids = docs.id
index.index(docs)

one = index[ids[0]]
many = index[ids[:2]]

del index[ids[0]]
index.index(Product(id=str(ids[1]), title="updated", price=99, embedding=np.ones(4)))
```

Re-indexing an existing ID updates that document. Recheck `num_docs()` after deletes and updates.

## 5. Persist and restore a local index

```python
from tempfile import TemporaryDirectory
from pathlib import Path

with TemporaryDirectory() as tmp:
    path = Path(tmp) / "products.bin"
    index.persist(str(path))
    restored = InMemoryExactNNIndex[Product](index_file_path=str(path))
    assert restored.num_docs() == index.num_docs()
    restored_docs, restored_scores = restored.find(
        np.zeros(4), search_field="embedding", limit=2
    )
```

Initialize with either `docs` or `index_file_path`, not both. A missing `index_file_path` creates an empty index and logs a warning.

## 6. Nested subindex search

A schema can hold a homogeneous `DocList` of child documents:

```python
from docarray import BaseDoc, DocList
from docarray.typing import NdArray

class Chunk(BaseDoc):
    text: str
    embedding: NdArray[4]

class Article(BaseDoc):
    title: str
    chunks: DocList[Chunk]
```

Index the root documents, then search the named child subindex:

```python
root_docs, child_docs, scores = index.find_subindex(
    np.zeros(4),
    subindex="chunks",
    search_field="embedding",
    limit=5,
)
```

The returned root documents preserve the parent relationship; child documents are returned as the child schema. Deleting a root removes its subindex children. Use [document-modeling](../../document-modeling/) for optional/nested schema decisions before indexing.

## 7. Choose a backend

Start with `InMemoryExactNNIndex` for deterministic local development and small datasets. Move to an optional backend only after deciding:

1. whether the service is local, managed, or embedded;
2. which package extra and client version are required;
3. how vector dimensions and metric names map to that backend;
4. whether filters/text/hybrid query composition is supported;
5. how IDs, persistence, credentials, and service health are managed.

Read [optional-backends.md](optional-backends.md) for the supported class-to-extra map and do not install `full` merely to make an import error disappear.
