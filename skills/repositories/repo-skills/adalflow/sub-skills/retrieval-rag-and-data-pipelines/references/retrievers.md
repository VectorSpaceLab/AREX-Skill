# Retrievers

This reference covers the retriever layer that sits on top of a prepared corpus or vector store. The common theme is the same: build an index from documents or embeddings, then call the retriever with a string query or query vectors.

## Base contract

`Retriever` is the shared base class for retrieval components.

### Expected behavior

- Subclasses implement `build_index_from_documents(...)` and `call(...)`.
- Optional async retrieval may be provided through `acall(...)`.
- Optional persistence hooks are `save_to_file(...)` and `load_from_file(...)`.
- `forward(...)` wraps retriever output into the optimization/tracing parameter flow, but ordinary retrieval uses `call(...)`.

### Working rule

Use `call(...)` for ordinary RAG assembly. Use the base `forward(...)` path only when the retriever participates in a traced or optimized component graph.

## BM25Retriever

Use BM25 when lexical matching is good enough or when you need a no-embedding fallback.

### Signature snapshot

`BM25Retriever(top_k=5, k1=1.5, b=0.75, epsilon=0.25, documents=None, document_map_func=None, use_tokenizer=True)`

### Behavior to remember

- `document_map_func` must return a string.
- `use_tokenizer=True` uses tokenizer-aware splitting instead of raw spaces.
- `build_index_from_documents(...)` precomputes term frequencies and idf values.
- `call(...)` accepts a string or list of strings and returns `RetrieverOutput` objects with indices and scores.
- `save_to_file(...)` and `load_from_file(...)` are provided because BM25 state is cheap to serialize and expensive to rebuild repeatedly.

### Good fit

- Keyword-heavy corpora.
- Small or medium corpora where exact terms matter.
- Retrieval pipelines that need a local, dependency-light fallback.

## FAISSRetriever

Use FAISS when you want local semantic retrieval over embedding vectors.

### Signature snapshot

`FAISSRetriever(embedder=None, top_k=5, dimensions=None, documents=None, document_map_func=None, metric="prob")`

### Behavior to remember

- `document_map_func` must return vectors, not text.
- `call(...)` accepts either query strings or query embeddings.
- String queries require an `Embedder` or `BatchEmbedder` to be injected.
- For `metric="cosine"` or `metric="prob"`, embeddings are normalized for cosine-style search.
- For `metric="euclidean"`, normalization is not required.
- `dimensions` must match the embedding width stored in the index.
- `build_index_from_documents(...)` validates shapes and will reset the index on failure.

### Good fit

- Local RAG prototypes.
- Service-free vector search.
- Reusable experiments where the embedding model is stable.

### Practical guidance

- If the embedder changes, rebuild the vector index.
- If you see a dimension mismatch, compare the current embedding width with the persisted index width before searching.
- Choose the metric once and keep threshold logic aligned with that metric.

## LanceDBRetriever

Use LanceDB when you want a vector store that lives outside process memory but is still local-first.

### Signature snapshot

`LanceDBRetriever(embedder, dimensions, db_uri="./lancedb-index", top_k=5, overwrite=True)`

### Behavior to remember

- Creates a LanceDB table with a fixed vector dimension.
- `add_documents(...)` expects dictionaries with a `content` field.
- Retrieval uses the injected `Embedder` to vectorize the query.
- Returned results include document indices and distance scores.

### Good fit

- Local disk-backed retrieval.
- Quick vector-store experiments without a service cluster.

## QdrantRetriever

Use Qdrant when the corpus is already stored in a Qdrant collection or when you want a managed vector service.

### Signature snapshot

`QdrantRetriever(collection_name, client, embedder, top_k=10, vector_name=None, text_key="text", metadata_key="meta_data", filter=None)`

### Behavior to remember

- The retriever resolves the vector name automatically when possible.
- Retrieval can be filtered with a Qdrant `Filter`.
- Returned `RetrieverOutput.documents` are reconstructed `Document` objects built from payload fields.
- `reset_index()` removes the collection when the client supports it.

### Good fit

- External service-backed vector search.
- Filter-heavy retrieval.
- Payload-rich documents where the text and metadata live in the store.

## PostgresRetriever

Use Postgres when you want SQL-based storage plus pgvector-style search.

### Signature snapshot

`PostgresRetriever(embedder, top_k=1, database_url=None, table_name="document", distance_operator=DistanceToOperator.INNER_PRODUCT)`

### Behavior to remember

- Query strings are assembled as SQL and executed through the SQLAlchemy database manager.
- The embedder creates the query vector.
- The selected `DistanceToOperator` controls how scores are computed and interpreted.
- Returned results are converted back into `Document` objects.

### Good fit

- Teams already using Postgres as the data backbone.
- Retrieval that benefits from SQL filtering and pgvector.

## Choosing a backend

| Need | Pick |
| --- | --- |
| Keyword-first retrieval with minimal dependencies | `BM25Retriever` |
| Local semantic search over embeddings | `FAISSRetriever` |
| Local disk-backed vector store | `LanceDBRetriever` |
| Managed vector service and payload filters | `QdrantRetriever` |
| SQL-centric storage and vector search | `PostgresRetriever` |

## Optional dependency gates

Do not assume the optional retrievers are available unless their package imports and a tiny native retrieval run have already succeeded in the active environment.

- `FAISSRetriever` needs the FAISS package.
- `LanceDBRetriever` needs LanceDB.
- `QdrantRetriever` needs the Qdrant client.
- `PostgresRetriever` needs SQLAlchemy and pgvector, plus a reachable database.

## Retrieval assembly pattern

```python
retriever = BM25Retriever(top_k=5)
retriever.build_index_from_documents(documents, document_map_func=lambda doc: doc.text)
outputs = retriever("query text")
```

```python
retriever = FAISSRetriever(embedder=embedder, top_k=5, dimensions=256)
retriever.build_index_from_documents([doc.vector for doc in chunks])
outputs = retriever("query text")
```

The downstream RAG boundary should not care which retriever produced the outputs as long as it receives `RetrieverOutput` objects.
