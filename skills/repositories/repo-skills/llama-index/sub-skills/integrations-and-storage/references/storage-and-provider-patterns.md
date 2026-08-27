# Storage and Provider Patterns

## Storage Layers

LlamaIndex separates storage into several concerns:

- Document/node storage: the parsed `Document` or node payloads, often through docstores.
- Vector storage: embedding vectors and sometimes text, metadata, and IDs.
- Index metadata storage: index structures and IDs used by `load_index_from_storage`.
- Filesystem persistence: local or remote `persist_dir` writes through `StorageContext.persist(...)`.
- Provider persistence: a database, vector database, or cloud service that persists outside LlamaIndex's local files.

Core APIs live under `llama_index.core`, while provider-backed storage classes live in integration packages.

```python
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore

vector_store = QdrantVectorStore(client=client, collection_name="docs")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

Route detailed index construction, retrieval, and query engine setup to `../indexing-and-querying/SKILL.md` after the storage backend is chosen.

## Decision Tree

1. Quick local experiment: use default simple in-memory stores from core; call `index.storage_context.persist(persist_dir="storage")` when disk reload is needed.
2. Local files but not local disk: pass an `fsspec` filesystem to `persist(..., fs=...)` and reload with the same `StorageContext.from_defaults(persist_dir=..., fs=...)` setup.
3. Local embedded vector database: choose packages such as Chroma, FAISS, Hnswlib, DocArray, DuckDB, or txtai when the user wants local control and accepts backend-specific persistence rules.
4. Self-hosted service: choose packages such as Qdrant, Milvus, Weaviate, Redis, Elasticsearch/OpenSearch, Postgres/pgvector, Cassandra, or Neo4j when a service endpoint must already exist or be started separately.
5. Cloud service: choose packages such as Pinecone, Azure AI Search, MongoDB Atlas, Vertex AI Vector Search, Databricks, Upstash, S3, Supabase, or managed database providers when credentials, region, project, and network access are available.

## Persistence Semantics

Do not assume every vector store persists through `persist_dir`.

- Core `SimpleVectorStore`, `SimpleDocumentStore`, and `SimpleIndexStore` can be persisted to local files and loaded back from the same `persist_dir`.
- Many vector-store integrations store vectors and often text in their own backend. For those, `StorageContext.persist()` may be unnecessary or a no-op; persistence is controlled by the provider database/service.
- Some in-memory integrations need explicit backend persistence or are unsuitable for restart survival unless saved through their own library.
- If the vector store does not store text/documents, use `store_nodes_override=True` or a docstore strategy when the index/query path needs node text on reload. Confirm against the specific integration before relying on reload behavior.
- Multiple indexes in one local persistence directory require stable `index.set_index_id(...)` values and matching `index_id` when reloading.

The storage docs explicitly note that alternative storage backends such as MongoDB may persist by default and `storage_context.persist()` can do nothing in that configuration.

## Provider Wiring Pattern

Most provider integrations follow this shape:

```python
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.qdrant import QdrantVectorStore

Settings.llm = Ollama(model="llama3.1", request_timeout=360.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

vector_store = QdrantVectorStore(client=client, collection_name="docs")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

Keep the pattern stable and vary only the provider class and client construction. For provider-specific constructor arguments, consult the installed package, its README, or examples; do not guess credentials, regions, dimensions, or endpoint names.

## Vector Store Choice Questions

Ask these before recommending a backend:

- Does the user need metadata filtering, hybrid search, delete/update support, async operations, or stored document text?
- Must data survive process restart without an external service?
- Is a local file/embedded database acceptable, or does the deployment require an already managed service?
- Who creates collections/indexes and embedding dimensions: LlamaIndex, the provider client, infrastructure code, or the user?
- Can the environment make outbound network calls, download models, or start local daemons?
- Are credentials available via environment variables or an existing client object?

## Reader, LLM, and Embedding Integrations

Reader integrations add data connectors and parsers, but `SimpleDirectoryReader` and core document/node objects remain in `llama_index.core`. Route chunking and ingestion pipelines to `../ingestion-and-loading/SKILL.md`.

LLM and embedding integrations are usually assigned through `Settings` or passed directly to constructors. Use explicit models to avoid accidental remote defaults:

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
```

If the user needs prompt formats, structured outputs, tool-calling options, or detailed model behavior, route to `../customization-and-structured-outputs/SKILL.md`.

## Compatibility Notes for Core 0.14.x

For this generated skill, verified live facts include `llama-index-core==0.14.22`. Prefer integration versions whose metadata declares compatibility with `llama-index-core>=0.13` or `>=0.14` and `<0.15`. If an environment has mixed older plugins, upgrade or reinstall the narrow integration package that owns the import rather than reinstalling every LlamaIndex package.
