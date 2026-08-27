# Embedding and Storage

CrewAI retrieval uses embedding providers plus vector storage. Keep these concerns explicit:

- `Memory` stores learned facts through a memory storage backend, defaulting to LanceDB.
- `Knowledge` stores source chunks through `KnowledgeStorage`, which uses the global or instance-specific RAG client.
- Native RAG clients and `RagTool` store vectors in ChromaDB or Qdrant collections.

## Embedding Provider Specs

CrewAI accepts provider dictionaries shaped like:

```python
embedder = {
    "provider": "openai",
    "config": {
        "model_name": "text-embedding-3-large",
        "dimensions": 3072,
    },
}
```

Provider names supported by the installed CrewAI embedding factory include:

| Provider | Notes |
| --- | --- |
| `openai` | Supports `api_key`, `model_name`, `api_base`, `api_version`, `organization_id`, `dimensions`, and related OpenAI embedding options. |
| `azure` | Azure/OpenAI-compatible embedding configuration. |
| `amazon-bedrock` | AWS Bedrock embeddings. |
| `cohere` | Cohere embeddings such as `embed-english-v3.0` or provider defaults. |
| `google-generativeai` / `google` | Google Generative AI embeddings. |
| `google-vertex` | Vertex AI embeddings; supports project/location and newer model dimensionality controls. |
| `huggingface` | HuggingFace embedding function. |
| `instructor` | Instructor embeddings. |
| `jina` | Jina embeddings. |
| `ollama` | Local Ollama embedding endpoint, with `url` and `model_name`. |
| `onnx` | Local ONNX embedding function. |
| `openclip` | OpenCLIP embeddings. |
| `roboflow` | Roboflow embeddings. |
| `sentence-transformer` | Local sentence-transformer models, with `model_name`, `device`, and `normalize_embeddings`. |
| `text2vec` | Text2Vec embeddings. |
| `voyageai` | Voyage AI embeddings. |
| `watsonx` | IBM watsonx embeddings. |
| `custom` | Custom embedding callable/provider shape. |

Use the same provider/model/dimension for every write and query against a given collection. A collection created with 1536-dimensional vectors cannot be searched or appended with 3072-dimensional vectors.

## Memory Storage

`Memory(storage="lancedb")` uses the built-in LanceDB storage. `Memory(storage="qdrant-edge")` uses the built-in edge Qdrant storage. Any other string passed as `storage` is treated as a LanceDB path.

```python
from crewai import Memory

memory = Memory(
    storage="lancedb",
    embedder={
        "provider": "openai",
        "config": {"model_name": "text-embedding-3-large"},
    },
)
```

Custom memory storage can be injected directly or through a process-wide factory:

```python
from crewai.memory.storage.factory import set_memory_storage_factory

set_memory_storage_factory(lambda spec: my_backend if spec == "custom" else None)
```

Factory rules:

- Register once at application startup.
- Return `None` for storage specs the factory does not own so built-ins still work.
- Explicit `Memory(storage=backend_instance)` wins over the factory.
- Clear the factory with `set_memory_storage_factory(None)` when tests or application teardown need built-in behavior again.

## Knowledge Storage

`Knowledge` defaults to `KnowledgeStorage(embedder=..., collection_name=...)`. It uses the global RAG client unless an embedder is supplied, in which case it creates an instance-specific ChromaDB config with that embedding function.

```python
from crewai.knowledge.knowledge import Knowledge
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.storage.knowledge_storage import KnowledgeStorage

source = StringKnowledgeSource(content="Support tier Enterprise includes SSO.")
storage = KnowledgeStorage(
    embedder={
        "provider": "openai",
        "config": {"model_name": "text-embedding-3-small"},
    },
    collection_name="support",
)
knowledge = Knowledge(
    collection_name="support",
    sources=[source],
    storage=storage,
)
knowledge.add_sources()
```

Collection naming:

- `collection_name="crew"` becomes vector collection `knowledge_crew`.
- Agent roles become collection suffixes for agent-level knowledge.
- If `collection_name` is omitted, the collection name is `knowledge`.

Custom knowledge storage can be supplied directly or through `set_knowledge_storage_factory(factory)`. As with memory, register this at startup and return `None` when the built-in storage should handle a collection.

## Native RAG Vector Stores

### ChromaDB

`ChromaDBConfig()` is the default native RAG configuration. It uses persistent ChromaDB settings, reset enabled, anonymized telemetry disabled, and an OpenAI embedding function defaulting to `text-embedding-3-small`.

```python
from crewai.rag.chromadb.config import ChromaDBConfig
from crewai.rag.config.utils import set_rag_config

set_rag_config(ChromaDBConfig())
```

Useful ChromaDB config fields:

| Field | Notes |
| --- | --- |
| `tenant` | Defaults to `default_tenant`. |
| `database` | Defaults to `default_database`. |
| `settings` | ChromaDB `Settings`; default is persistent with reset enabled. |
| `embedding_function` | Chroma-compatible embedding function. |

### Qdrant

`QdrantConfig()` uses file-based Qdrant client options by default and a FastEmbed embedding function using `sentence-transformers/all-MiniLM-L6-v2`.

```python
from crewai.rag.config.utils import set_rag_config
from crewai.rag.qdrant.config import QdrantConfig

set_rag_config(QdrantConfig())
```

Useful Qdrant config fields:

| Field | Notes |
| --- | --- |
| `options` | Qdrant client parameters such as local path or server details. |
| `embedding_function` | Callable that embeds one text string. |
| `vectors_config` | Optional Qdrant vector parameters. Default Qdrant constants use cosine distance and 384 dimensions for the default FastEmbed model. |

### Optional Provider Imports

If ChromaDB or Qdrant provider dependencies are not installed, CrewAI exposes missing-provider placeholders that raise a clear `RuntimeError` when instantiated. The message names the provider and suggests installing the matching extra.

Use the bundled [../scripts/check_rag_imports.py](../scripts/check_rag_imports.py) to check what is importable before choosing a provider.

## RagTool Vector DB Config

`RagToolConfig` supports the same two native providers:

```python
from crewai_tools import RagTool

rag_tool = RagTool(
    collection_name="kb",
    config={
        "vectordb": {
            "provider": "chromadb",
            "config": {},
        },
        "embedding_model": {
            "provider": "openai",
            "config": {"model_name": "text-embedding-3-small"},
        },
    },
)
```

`RagTool` builds the embedding function first, injects it into `ChromaDBConfig` or `QdrantConfig`, then creates a `CrewAIRagAdapter` and ensures the collection exists.

## Dimension Mismatch Rules

Symptoms include errors mentioning different vector dimensions, failed collection saves, empty or broken searches after changing an embedding model, or warnings suggesting `crewai reset-memories -a`.

Known dimension-sensitive changes:

- OpenAI `text-embedding-3-small` commonly yields 1536-dimensional vectors.
- OpenAI `text-embedding-3-large` commonly yields 3072-dimensional vectors.
- Qdrant's default FastEmbed model uses 384-dimensional vectors.
- Custom providers may vary by model, configuration, or output dimensionality.

Safe migration pattern:

1. Identify the failing surface: unified memory, crew knowledge, agent knowledge, or `RagTool`/direct RAG collection.
2. Decide whether existing vectors can be discarded or need migration outside CrewAI.
3. Use the smallest reset target that matches the collection:
   - `crewai reset-memories --memory` for unified memory.
   - `crewai reset-memories --knowledge` for crew and agent knowledge collections together.
   - `crewai reset-memories --agent-knowledge` for agent-only knowledge collections.
   - `crewai reset-memories --all` only when several stores share stale dimensions.
4. Re-index knowledge or RAG sources with the new embedder.
5. Keep the new embedder configuration stable for future writes and queries.

`Memory.reset_all()` rebuilds the entire memory store; `Memory.reset(scope=...)` deletes records in a scope but may not solve a collection-level dimension mismatch if the backing vector table itself remains dimensioned for the old model. Prefer full store reset or a fresh storage path when changing vector dimensions.

## Storage Path and Cache Guidance

- Do not hard-code machine-specific storage directories in reusable code or skill content.
- Prefer CrewAI defaults for local apps unless production requires explicit storage paths.
- When troubleshooting, report storage locations generically, for example “the CrewAI storage directory for this project,” not a full local path.
- Reset commands act on current project crews/flows discovered by CrewAI. Run them from the project that owns the memories.
- If multiple projects share a custom path, resets may affect more data than expected. Confirm collection names and storage configuration first.

## Source Evidence Notes

This reference distills CrewAI embedding factory types, memory storage factories, knowledge storage, native RAG configs, optional import behavior, and dimension mismatch tests into standalone guidance. Source repository files are evidence only and are not runtime dependencies.
