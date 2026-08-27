# Query And Indexing Guide

Use this guide to implement concrete txtai embeddings workflows without depending on the original repository docs or examples.

## Quick Semantic Search

Use this when ids and scores are enough:

```python
from txtai import Embeddings

embeddings = Embeddings()
embeddings.index([
    "US tops 5 million confirmed virus cases",
    "Maine man wins $1M from lottery ticket",
])
print(embeddings.search("feel good story", 1))
```

Expected shape: `[(id, score)]`. With raw strings, ids are generated as sequence positions unless `autoid` is configured.

If the environment must avoid model downloads, use an external transform or precomputed vectors:

```python
import numpy as np
from txtai import Embeddings

def transform(data):
    vectors = []
    for value in data:
        text = str(value).lower()
        vectors.append(np.array([len(text), text.count("win"), text.count("ice")], dtype=np.float32))
    return vectors

embeddings = Embeddings(method="external", transform=transform)
embeddings.index([("lucky", "Maine man wins lottery", None), ("climate", "Ice shelf collapsed", None)])
print(embeddings.search("win lottery", 1))
```

## Content Storage And SQL

Set `content=True` before the first `index` call when a task needs stored text, metadata, SQL, dictionary rows, object retrieval, or reindexing from stored records.

```python
from txtai import Embeddings

rows = [
    ("a", {"text": "Maine man wins lottery", "topic": "lucky", "published": "2024-01-01"}, None),
    ("b", {"text": "Ice shelf collapsed", "topic": "climate", "published": "2024-01-02"}, None),
]

embeddings = Embeddings(content=True)
embeddings.index(rows)

results = embeddings.search("""
select id, text, topic, score
from txtai
where similar(:query, 20) and topic = :topic
order by score desc
limit 5
""", parameters={"query": "feel good story", "topic": "lucky"})
```

Expected shape: dictionaries keyed by selected columns.

Dynamic column notes:

- Dictionary fields become queryable SQL columns when content storage is enabled.
- `id`, `text`, `score`, `data`, and `entry` are common built-in/returned fields depending on selection.
- Nested dictionaries can be filtered with bracket escape syntax, for example `[parent.child element] = 'abc'`.
- For non-`text` source columns, use `columns={"text": "value"}` so txtai knows which field to vectorize.

## `similar(...)` Clause

SQL similarity uses a txtai-specific function:

```sql
select id, text, score from txtai where similar('feel good story') limit 5
```

Conceptual arguments:

```sql
similar('query', 'number of candidates', 'index', 'weights')
```

Practical forms:

```python
embeddings.search("select id, text, score from txtai where similar(:q)", parameters={"q": "lucky"})
embeddings.search("select id, text, score from txtai where similar(:q, 50)", parameters={"q": "lucky"})
embeddings.search("select id, text, score from txtai where similar(:q, 50, 'dense')", parameters={"q": "lucky"})
embeddings.search("select id, text, score from txtai where similar(:q, 50, 'dense', 0.7)", parameters={"q": "lucky"})
```

Candidate count should be larger than the final result `limit` whenever filters may remove rows. For example, request 50 or 100 candidates if the final query filters by date, category, tenant, or permissions and only returns `limit 5`.

## Bind Parameters

Prefer bind parameters for both natural-language inputs and filters:

```python
query = """
select id, text, score
from txtai
where similar(:semantic_query, 100) and tenant = :tenant and published >= :after
limit 10
"""
results = embeddings.search(query, parameters={
    "semantic_query": "climate story",
    "tenant": "public",
    "after": "2024-01-01",
})
```

For `batchsearch`, pass one parameter dictionary per query:

```python
queries = [
    "select id, text, score from txtai where similar(:q, 20)",
    "select id, text, score from txtai where similar(:q, 20)",
]
params = [{"q": "lottery"}, {"q": "iceberg"}]
results = embeddings.batchsearch(queries, parameters=params)
```

## Index Vs Upsert Vs Delete

Use stable ids for mutable records:

```python
embeddings.index([("doc-1", "original text", None)])
embeddings.upsert([("doc-1", "updated text", None)])
embeddings.delete(["doc-1"])
```

Rules:

- `index(rows)` replaces the current index.
- `upsert(rows)` inserts or updates records; if the index is empty, it falls back to indexing.
- `delete(ids)` takes external ids and returns deleted ids.
- Auto-generated ids are convenient for demos but awkward for update/delete because agents must search first to discover ids.
- Some ANN backends, such as immutable Annoy indexes, do not support all modification workflows; choose a backend that matches update requirements.

## Reindex From Stored Content

`reindex` needs content storage because it rebuilds from stored rows:

```python
embeddings = Embeddings(content=True)
embeddings.index(rows)
embeddings.reindex(path="sentence-transformers/all-MiniLM-L6-v2", backend="hnsw")
```

Use `reindex` to switch vector model/backend or refresh computed graph/scoring state without returning to the original raw data. If objects need special loading, pass a streaming `function` that prepares stored rows for the new vectorization step.

## Save And Load

```python
from txtai import Embeddings

embeddings = Embeddings(content=True)
embeddings.index(rows)
embeddings.save("my-index")

loaded = Embeddings().load("my-index")
print(loaded.search("query", 5))
loaded.close()
```

Operational notes:

- Directory saves contain a txtai config plus enabled ANN/database/scoring/graph/subindex components.
- Archive saves are supported with paths ending in compressed archive suffixes such as `.tar.gz`.
- Cloud save/load requires cloud configuration and is best treated as deployment-specific.
- After loading, run a known query and check `count()` before trusting the handoff.

## Hybrid Sparse + Dense Search

Hybrid search combines sparse keyword/vector evidence with dense semantic evidence:

```python
embeddings = Embeddings(path="sentence-transformers/all-MiniLM-L6-v2", hybrid=True, content=True)
embeddings.index(rows)

# Non-SQL hybrid weight.
embeddings.search("lottery ticket", 5, weights=0.6)

# SQL hybrid weight in similar clause.
embeddings.search("select id, text, score from txtai where similar(:q, 50, 0.6)", parameters={"q": "lottery ticket"})
```

Configuration shortcuts:

- `keyword=True` creates a sparse keyword index.
- `sparse=True` creates a sparse vector index using a default sparse model; `sparse="path"` selects a model.
- `hybrid=True`, `hybrid="tfidf"`, or `hybrid="sparse"` creates dense plus sparse components.
- Scoring normalization can change ranking; document `scoring.normalize` choices when tuning relevance.

When metadata filters are involved, increase `similar` candidates before changing weights. A low candidate count can look like poor hybrid ranking when filters simply removed most candidates.

## Graph Search

Enable graph storage at construction:

```python
embeddings = Embeddings(content=True, graph=True)
embeddings.index([
    {"id": "a", "text": "txtai connects vector search and workflows", "relationships": ["b"]},
    {"id": "b", "text": "semantic graph search finds related nodes"},
])
```

Manual relationships may be strings or dictionaries:

```python
{"id": "a", "text": "...", "relationships": ["b"]}
{"id": "a", "text": "...", "relationships": [{"id": "b", "type": "MEMBER_OF"}]}
```

Useful graph operations:

```python
embeddings.graph.topics
embeddings.graph.centrality()
embeddings.graph.pagerank()
embeddings.graph.showpath("a", "b")
embeddings.search("query", graph=True)
```

Graph query examples:

```python
embeddings.search("""
MATCH P=({id: 0})-[*1..3]->({id: 5})
RETURN P
""")

embeddings.search("""
MATCH P=(A)-[]->(B)
WHERE SIMILAR(A, "query")
RETURN B
ORDER BY A.score DESC
LIMIT 10
""")
```

Graph configuration has optional backend, topic, limit, minscore, approximate, and batch-size settings. The default graph backend is NetworkX; RDBMS graph storage requires database dependencies and a connection.

## Object Storage

Use object storage when records need binary payloads or decoded objects returned through SQL:

```python
embeddings = Embeddings(content=True, objects=True)
embeddings.index([("asset-1", {"text": "txtai workflow diagram", "object": b"binary data"}, None)])
result = embeddings.search("select object from txtai where similar(:q) limit 1", parameters={"q": "workflow"})[0]
```

Object modes:

- `objects=True` stores bytes-like objects with the standard encoder.
- `objects="image"` uses the image encoder and can return image objects when image dependencies are installed.
- `objects="pickle"` is legacy/trusted-only behavior and requires explicit allowance; do not enable for untrusted indexes or data.

Object storage requires `content=True`.

## Custom SQL Functions And Expressions

Custom functions expose Python callables or pipeline objects in SQL:

```python
embeddings = Embeddings(
    content=True,
    functions=[{"name": "myfunc", "function": my_callable}],
)
```

Expressions define reusable SQL snippets and optional indexes:

```python
embeddings = Embeddings(
    content=True,
    expressions=[
        {"name": "filepath", "index": True},
        {"name": "textlength", "expression": "length(text)", "index": True},
    ],
)
```

Use functions/expressions for computed columns, graph attributes, ranking helpers, and expensive filters that deserve database indexes.

## Subindexes

Subindexes let one embeddings database own multiple named indexes:

```python
embeddings = Embeddings(
    content=True,
    defaults=False,
    indexes={
        "keyword": {"keyword": True},
        "dense": {"dense": True},
        "title": {"path": "sentence-transformers/all-MiniLM-L6-v2", "columns": {"text": "title"}},
    },
)
embeddings.index(rows)

embeddings.search("query", index="keyword")
embeddings.search("select id, text, score from txtai where similar(:q, 50, 'dense')", parameters={"q": "query"})
```

Subindex troubleshooting:

- If `defaults=False`, make sure at least one subindex is configured or searches will fail with no index found.
- A missing index name raises an index-not-found style error.
- Save/load persists subindexes under the parent index.
- Use a shared model cache (`models`) for repeated vector models when constructing multiple embeddings instances or subindexes.

## External And Precomputed Vectors

External transform mode is useful for offline tests and custom vectorizers:

```python
import numpy as np
from txtai import Embeddings

def transform(data):
    return [np.asarray(row, dtype=np.float32) if not isinstance(row, str) else np.ones(4, dtype=np.float32) for row in data]

embeddings = Embeddings(method="external", transform=transform)
```

Precomputed vectors can be indexed directly when `method="external"` and no transform is supplied:

```python
vectors = np.random.rand(5, 10).astype(np.float32)
embeddings = Embeddings(method="external")
embeddings.index([(str(i), vector, None) for i, vector in enumerate(vectors)])
```

For semantic search with precomputed vectors, the query must also be provided as a compatible vector unless a transform function handles query text.

## Word Vectors And Scoring

Word-vector backed models with scoring need a separate `score(rows)` call before `index(rows)`:

```python
embeddings = Embeddings(path="local-word-vector-model", scoring="bm25", pca=3)
embeddings.score(rows)
embeddings.index(rows)
```

Repeat `score(rows)` before upserts for word-vector/scoring configurations that depend on term weighting.
