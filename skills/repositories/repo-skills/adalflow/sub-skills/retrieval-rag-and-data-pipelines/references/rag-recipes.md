# RAG Recipes

This reference keeps the RAG boundary focused on retrieval, context assembly, and corpus persistence. The generator or answer component is assumed to be built elsewhere.

## Canonical retrieval-first flow

1. Normalize source data into `Document` objects.
2. Chunk text with `TextSplitter` when the source text is longer than the intended context window.
3. Add vectors with `ToEmbeddings` when the retriever needs semantic search.
4. Persist raw and transformed items with `LocalDB` if the same corpus will be reused.
5. Build the retriever index from the saved or transformed corpus.
6. Retrieve `RetrieverOutput` objects.
7. Convert the outputs into a context string with `RetrieverOutputToContextStr`.
8. Pass query + context to the downstream answer component from the model-client workflow sub-skill.

## RAG skeleton

```python
from adalflow.core.component import Component
from adalflow.core.db import LocalDB
from adalflow.components.data_process import (
    RetrieverOutputToContextStr,
    TextSplitter,
    ToEmbeddings,
)
from adalflow.components.retriever import BM25Retriever, FAISSRetriever


class RAG(Component):
    def __init__(self, *, embedder=None, retriever=None, generator=None, index_path: str = "rag-cache.pkl"):
        super().__init__()
        self.db = LocalDB(name="rag-cache")
        self.index_path = index_path
        self.embedder = embedder
        self.retriever = retriever
        self.generator = generator  # constructed elsewhere
        self.context_builder = RetrieverOutputToContextStr(deduplicate=True)
        self.transformed_docs = []

    def build_index(self, documents):
        self.db.load(documents)
        splitter = TextSplitter(split_by="word", chunk_size=400, chunk_overlap=200)
        self.db.register_transformer(transformer=splitter, key="chunks")
        self.db.transform(key="chunks")
        self.transformed_docs = self.db.get_transformed_data(key="chunks")

        if isinstance(self.retriever, BM25Retriever):
            self.retriever.build_index_from_documents(
                self.transformed_docs,
                document_map_func=lambda doc: doc.text,
            )
        elif isinstance(self.retriever, FAISSRetriever):
            vectorizer = ToEmbeddings(embedder=self.embedder, batch_size=50)
            embedded_docs = vectorizer(self.transformed_docs)
            self.retriever.build_index_from_documents(
                embedded_docs,
                document_map_func=lambda doc: doc.vector,
            )

    def call(self, query: str):
        retriever_outputs = self.retriever(query)
        for output in retriever_outputs:
            output.documents = [self.transformed_docs[i] for i in output.doc_indices]
        context_str = self.context_builder(retriever_outputs)
        # The generator boundary is owned by the model-client workflow sub-skill.
        return self.generator(prompt_kwargs={"input_str": query, "context_str": context_str}), context_str
```

## Local BM25 recipe

Use this when the corpus is already text-heavy and you want a no-embedding baseline.

```python
splitter = TextSplitter(split_by="word", chunk_size=400, chunk_overlap=200)
local_db = LocalDB(name="bm25-rag")
local_db.load(documents)
local_db.register_transformer(transformer=splitter, key="chunks")
local_db.transform(key="chunks")

retriever = BM25Retriever(top_k=5)
retriever.build_index_from_documents(
    local_db.get_transformed_data(key="chunks"),
    document_map_func=lambda doc: doc.text,
)
```

### When to use

- You need a strong lexical baseline.
- You want to avoid embedding calls while validating the corpus.
- You want to debug chunking before introducing vector search.

## Local vector RAG recipe

Use this when you want semantic search without an external vector service.

```python
splitter = TextSplitter(split_by="word", chunk_size=400, chunk_overlap=200)
vectorizer = ToEmbeddings(embedder=embedder, batch_size=50)
local_db = LocalDB(name="vector-rag")
local_db.load(documents)
local_db.register_transformer(transformer=splitter, key="chunks")
local_db.transform(key="chunks")
chunked_docs = local_db.get_transformed_data(key="chunks")
embedded_docs = vectorizer(chunked_docs)

retriever = FAISSRetriever(embedder=embedder, top_k=5, dimensions=256)
retriever.build_index_from_documents(
    embedded_docs,
    document_map_func=lambda doc: doc.vector,
)
```

### When to use

- You want a fast, local prototype.
- You need the same retrieval behavior every run.
- You want to keep the context assembly logic identical across experiments.

## External vector-store recipe

Swap the retriever only; keep the document normalization and context assembly the same.

- `LanceDBRetriever` when the index should live on local disk in a vector table.
- `QdrantRetriever` when the index is already in a Qdrant collection.
- `PostgresRetriever` when SQL + pgvector is the natural storage layer.

## Config pattern

A practical retrieval-first config usually has four blocks:

```yaml
storage:
  index_path: <persistent-cache-path>
  use_local_db: true

text_splitter:
  split_by: word
  chunk_size: 400
  chunk_overlap: 200
  batch_size: 1000

retriever:
  kind: faiss  # or bm25, lancedb, qdrant, postgres
  top_k: 5
  metric: prob

context:
  deduplicate: true
```

### Config notes

- Keep the split settings and the retriever settings together because they jointly control recall.
- Keep the vector dimension stable once a corpus has been embedded.
- Use one config block for persistence so index rebuilds are explicit.
- Generator setup belongs to the model-client workflow sub-skill; this file only defines the retrieval boundary.

## RAG rebuild policy

- Reuse the saved corpus when the source documents have not changed.
- Rebuild the index when the source documents, splitter settings, or embedding model change.
- If you change the corpus shape, clear the old saved index before writing a new one to avoid stale or duplicated chunks.

## Useful checkpoints

- `Document` count before splitting.
- Chunk count after splitting.
- Vector width after embedding.
- Retriever output count for each query.
- Final context length before generation.
