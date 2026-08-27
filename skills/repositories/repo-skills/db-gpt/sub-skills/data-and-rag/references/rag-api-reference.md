# RAG API reference

This reference records the verified DB-GPT 0.8.1 package surface for local
knowledge, chunking, assemblers, retrievers, and embeddings.

## Core types and verified signatures

The following imports and signatures were resolved in the prepared Python 3.11
inspection environment:

```python
from dbgpt_ext.rag import ChunkParameters
from dbgpt_ext.rag.knowledge import KnowledgeFactory
from dbgpt_ext.datasource.rdbms.conn_sqlite import SQLiteConnectorParameters
from dbgpt_ext.rag.knowledge.markdown import MarkdownKnowledge
from dbgpt_ext.rag.assembler.embedding import EmbeddingAssembler
from dbgpt_ext.rag.assembler.bm25 import BM25Assembler
from dbgpt_ext.rag.assembler.db_schema import DBSchemaAssembler
from dbgpt_ext.rag.retriever.bm25 import BM25Retriever
from dbgpt_ext.rag.retriever.db_schema import DBSchemaRetriever
from dbgpt_ext.storage.vector_store.chroma_store import ChromaVectorConfig, ChromaStore
```

Verified callable shapes:

```text
ChunkParameters(*, chunk_strategy: str = None,
  text_splitter: Optional[Any] = None,
  splitter_type: SplitterType = USER_DEFINE,
  chunk_size: int = 512, chunk_overlap: int = 50,
  separator: str = "\n", enable_merge: bool = None)

KnowledgeFactory(file_path=None, knowledge_type=DOCUMENT, metadata=None)
KnowledgeFactory.create(datasource="", knowledge_type=DOCUMENT, metadata=None)
KnowledgeFactory.from_file_path(file_path="", knowledge_type=DOCUMENT, metadata=None)
KnowledgeFactory.from_text(text="", knowledge_type=TEXT, metadata=None)

SQLiteConnectorParameters(path: str, check_same_thread=False, driver="sqlite")
SQLiteConnector.from_parameters(parameters)
SQLiteConnector.from_file_path(file_path: str, engine_args=None, **kwargs)

MarkdownKnowledge(file_path=None, knowledge_type=DOCUMENT, encoding="utf-8",
  loader=None, metadata=None, **kwargs)

EmbeddingAssembler.load_from_knowledge(knowledge, index_store,
  chunk_parameters=None, embedding_model=None, embeddings=None,
  retrieve_strategy=RetrieverStrategy.EMBEDDING)
EmbeddingAssembler.as_retriever(top_k=4, **kwargs)

BM25Assembler.load_from_knowledge(knowledge, es_config, name="dbgpt",
  k1=2.0, b=0.75, chunk_parameters=None)
BM25Retriever(top_k=4, es_index="dbgpt", es_client=None,
  query_rewrite=None, rerank=None, k1=2.0, b=0.75, executor=None)

DBSchemaAssembler.load_from_connection(connector,
  table_vector_store_connector, field_vector_store_connector=None,
  chunk_parameters=None, embedding_model=None, embeddings=None,
  max_seq_length=512)
DBSchemaRetriever(table_vector_store_connector,
  field_vector_store_connector=None, separator="--table-field-separator--",
  column_separator=",\\r\\n    ", top_k=4, connector=None,
  query_rewrite=False, rerank=None, **kwargs)

ChromaVectorConfig(user=None, password=None, max_chunks_once_load=None,
  max_threads=None, persist_path=None, collection_metadata=None)
ChromaStore(vector_store_config, name, embedding_fn=None,
  chroma_client=None, collection_metadata=None,
  max_chunks_once_load=None, max_threads=None)
```

These are package APIs, not claims that every optional parser or backend is
installed. Use import checks and a tiny fixture before choosing a concrete
workflow.

## ChunkParameters and strategies

`ChunkParameters` controls `ChunkManager` selection. Its defaults are a
512-character target, 50-character overlap, newline separator, user-defined
splitter type, and no explicit strategy. The manager uses the knowledge class's
default strategy when `chunk_strategy` is empty or `Automatic`.

Supported `ChunkStrategy` names are:

| Name | Typical use | Main controls |
|---|---|---|
| `CHUNK_BY_SIZE` | prose, TXT, CSV, DOCX | `chunk_size`, `chunk_overlap` |
| `CHUNK_BY_PAGE` | page-like or datasource summaries | page boundaries |
| `CHUNK_BY_PARAGRAPH` | paragraph-preserving DOCX/text | `separator` |
| `CHUNK_BY_SEPARATOR` | row/paragraph delimiters | `separator`, optionally `enable_merge` |
| `CHUNK_BY_MARKDOWN_HEADER` | Markdown hierarchy | header metadata, size/overlap fallback |

`TextSplitter` rejects `chunk_overlap > chunk_size` with `ValueError`. Empty
segments are removed by the join/merge logic, so a blank document may result in
zero chunks. A single very long atomic segment may still exceed the target and
emit a warning; validate the observed maximum rather than assuming a hard cap.

Use the package's public splitter imports when constructing one directly:

```python
from dbgpt.rag.text_splitter import CharacterTextSplitter, MarkdownHeaderTextSplitter

splitter = CharacterTextSplitter(separator=" ", chunk_size=32, chunk_overlap=4)
chunks = splitter.create_documents(["a small local fixture"])
```

For Markdown, `MarkdownHeaderTextSplitter` attaches heading metadata and falls
back to recursive splitting for oversized sections. It recognizes the standard
heading levels by default and avoids treating fenced code markers as headings.

## Knowledge lifecycle

```python
knowledge = KnowledgeFactory.from_file_path("notes.md")
documents = knowledge.load()
processed = knowledge.extract(
    documents,
    ChunkParameters(
        chunk_strategy="CHUNK_BY_MARKDOWN_HEADER",
        chunk_size=512,
        chunk_overlap=50,
    ),
)
```

`Knowledge.load()` calls the format implementation and post-processing. The
`extract` method is format-specific; Markdown attaches split chunks to the
loaded documents. Assemblers perform their own load-and-split pipeline, so do
not load and persist the same data twice unless comparing outputs deliberately.

## Assemblers and retrievers

### Embedding path

`EmbeddingAssembler` accepts a `Knowledge`, an `IndexStoreBase`, optional
`ChunkParameters`, and either an `Embeddings` object or an embedding model name.
Providing a concrete `Embeddings` object is the most deterministic option.
`persist()` delegates to the index store's bounded loader and returns chunk ids.
`as_retriever(top_k=4)` returns an `EmbeddingRetriever` using the selected
`RetrieverStrategy` (default `EMBEDDING`; `GRAPH`, `KEYWORD`, and other enum
values are possible only when the supplied store supports them).

Use this shape with a local vector store, but do not construct Chroma without a
real embedding function:

```python
assembler = EmbeddingAssembler.load_from_knowledge(
    knowledge=knowledge,
    index_store=vector_store,
    chunk_parameters=ChunkParameters(chunk_strategy="CHUNK_BY_SIZE"),
    embeddings=embeddings,
)
ids = assembler.persist(max_chunks_once_load=10, max_threads=1)
retriever = assembler.as_retriever(top_k=4)
hits = retriever.retrieve_with_scores("local query", score_threshold=0.3)
```

`BaseRetriever` exposes synchronous and asynchronous `retrieve`,
`retrieve_with_scores`, `aretrieve`, and `aretrieve_with_scores`. Scores are
backend-defined; compare them only within the same backend/configuration.

### BM25/full-text path

`BM25Assembler` and `BM25Retriever` wrap Elasticsearch. Construction creates or
checks an index and can contact the configured service; persistence indexes
chunk content and JSON metadata. Defaults are `k1=2.0`, `b=0.75`, and top-k 4
at retriever level. Use BM25 for exact terms, names, identifiers, and precise
queries; use vector retrieval for semantic similarity; use a hybrid design only
when both stores and their operational costs are explicitly available.

There is no offline claim for `BM25Assembler`: use the bundled standard-library
fixture helper for a local sparse smoke, and reserve the DB-GPT BM25 classes for
an explicitly provisioned Elasticsearch service.

### Database schema path

`DBSchemaAssembler` creates `DatasourceKnowledge` from a `BaseConnector`,
produces table/field summary chunks, and persists table chunks to a required
vector store plus optional field store. `DBSchemaRetriever` performs similarity
search and, when fields were separated, fetches fields and reconstructs table
context. Use a local SQLite connector for deterministic schema checks. The
embedding dimension/sequence-length setting (`max_seq_length`, default 512)
is a splitting/summary limit; it is not proof that the vector store's actual
embedding dimension is 512.

## Embeddings and dimensions

`Embeddings` supplies `embed_documents(texts)` and `embed_query(text)`. Before
first persistence, run a harmless probe such as `embed_query("dimension probe")`
and verify:

- the result is a non-empty numeric vector;
- all document vectors have the same length as the query vector;
- a pre-existing collection's recorded dimension/model identity agrees;
- the query path uses the same embedding function as the index path.

If dimensions differ, stop before `load_document`, `upsert`, network access, or
collection creation. Do not “fix” the issue by padding/truncating vectors. A
missing embedding function is a configuration error; Chroma raises
`ValueError("Embeddings is None")`, while several other stores require a
non-null embedding function as well.

## Persistence semantics

`IndexStoreBase.load_document_with_limit` batches chunks and uses bounded worker
threads. In the verified 0.8.1 implementation, a failed group is retried per
chunk and bad chunks are skipped with warnings; a direct `load_document` call
remains stricter and can propagate a backend error. Report accepted and skipped
ids. For strict ingestion, validate all chunks first and call the strict path
only after validation.

Repeated indexing requires an explicit duplicate policy. Chroma upserts ids;
other stores may index the same content under new ids. Use stable chunk ids,
content hashes, or a collection replacement policy. Do not infer knowledge-space
upload/delete semantics from a low-level store.
