# Python OSS Providers

Mem0 Python OSS provider configuration centers on `MemoryConfig` and the provider factories. The inspected distribution was `mem0ai` 2.0.7 with public exports `Memory`, `AsyncMemory`, `MemoryClient`, and `AsyncMemoryClient`.

## Core Configuration Shape

Use a dictionary with these top-level keys for OSS `Memory.from_config(config)`:

```python
config = {
    "vector_store": {"provider": "qdrant", "config": {"path": "/tmp/mem0-qdrant", "embedding_model_dims": 1536}},
    "llm": {"provider": "openai", "config": {"model": "gpt-4.1-mini"}},
    "embedder": {"provider": "openai", "config": {"model": "text-embedding-3-small"}},
    "reranker": {"provider": "cohere", "config": {"model": "rerank-english-v3.0"}},
    "version": "v1.1",
}
```

`MemoryConfig` validates `vector_store`, `llm`, `embedder`, optional `reranker`, `history_db_path`, `version`, and `custom_instructions`. Prefer `Memory.from_config(config_dict)` for dictionaries; `MemoryConfig(**config_dict)` is useful when an agent needs validation errors without constructing providers. Some docs mention `from_config_file`; verify it in the installed package before relying on it because the inspected source exposes `from_config` but not a file-loading classmethod.

## Provider Names

Python LLM providers from the factory/config validators:

- `openai`, `openai_structured`, `azure_openai`, `azure_openai_structured`
- `anthropic`, `groq`, `together`, `aws_bedrock`, `litellm`
- `ollama`, `gemini`, `deepseek`, `minimax`, `xai`, `sarvam`
- `lmstudio`, `vllm`, `langchain`

Python embedder providers:

- `openai`, `azure_openai`, `ollama`, `huggingface`, `gemini`, `vertexai`
- `together`, `lmstudio`, `langchain`, `aws_bedrock`, `fastembed`
- `upstash_vector` can use mock embeddings when the vector config enables provider-side embeddings.

Python vector store providers:

- Local/common: `qdrant`, `chroma`, `pgvector`, `faiss`, `milvus`, `redis`, `valkey`
- Managed/cloud: `pinecone`, `mongodb`, `upstash_vector`, `azure_ai_search`, `azure_mysql`, `databricks`, `elasticsearch`, `opensearch`, `supabase`, `weaviate`, `s3_vectors`, `baidu`, `cassandra`, `neptune`, `turbopuffer`
- `langchain` adapts a LangChain vector store.

Python reranker providers:

- `cohere`, `sentence_transformer`, `zero_entropy`, `llm_reranker`, `huggingface`

Run `scripts/list_mem0_providers.py --json` to inspect the installed registries in the current environment.

## Optional Dependencies

Install the narrow dependency set for the selected provider. Core `mem0ai` already includes Pydantic, OpenAI, Qdrant client, HTTPX, SQLAlchemy, and related base dependencies. Common optional groups and packages include:

- `mem0ai[vector-stores]` for many vector backends: Chroma, Cassandra, Weaviate, Pinecone, FAISS CPU, Upstash Vector, Azure Search, pgvector/psycopg, MongoDB, Redis/Valkey, Elasticsearch, Milvus, and Databricks-related packages.
- `mem0ai[llms]` for extra LLM providers such as Groq, Together, LiteLLM, Ollama, Vertex/Google GenAI.
- `mem0ai[extras]` for broader integrations such as Bedrock/LangChain, sentence-transformers, OpenSearch, FastEmbed, and Elasticsearch.
- `mem0ai[nlp]` for spaCy-backed entity extraction and BM25 lemmatization. Without it, search should still work but hybrid/entity quality can degrade.
- For Qdrant BM25 sparse vectors, `fastembed` enables keyword search. Missing `fastembed` should degrade to semantic/entity search instead of blocking all search.

Do not install all extras reflexively. Pick the backend first, then add only the missing package named by the import error.

## Dimension and Backend Rules

- Default Python Qdrant config uses collection `mem0`, `embedding_model_dims=1536`, and a local path. If the embedder produces 768-dimensional vectors, set the vector store dimension field to 768 before adding memories.
- Qdrant requires one of local `path`, server `host` + `port`, or remote `url` + `api_key`. `client` takes precedence when supplied.
- Chroma requires either local/server config (`path` or `host` + `port`) or Chroma Cloud config (`api_key` + `tenant`), not both.
- PGVector requires `connection_pool`, `connection_string`, or individual `user`/`password` plus `host`/`port`.
- FAISS supports `distance_strategy` values `euclidean`, `inner_product`, or `cosine` and uses `embedding_model_dims`.
- Many vector config models forbid unknown fields; validation errors listing extra fields usually mean a Python/TypeScript casing mismatch or a provider block copied from another backend.

## Reranker Setup

Configure a reranker block, then enable reranking per search when needed:

```python
config = {
    "reranker": {
        "provider": "sentence_transformer",
        "config": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "device": "cpu", "top_k": 10},
    }
}
memory = Memory.from_config(config)
results = memory.search("favorite cafe", filters={"user_id": "alice"}, rerank=True)
```

Rerankers are optional. If `rerank=True` and the configured reranker raises at runtime, Mem0 logs a warning and continues with original vector/hybrid results in the inspected Python path. For hosted rerankers, keep API keys in environment variables or secret stores rather than hard-coding them.

## Validation Patterns

- Validate first with `python scripts/validate_memory_config.py --config config.json`.
- Use `--import-check` when you want the script to verify provider modules can import without constructing clients.
- Avoid validating by calling `Memory(config)` unless you are ready for provider constructors, local stores, telemetry stores, or clients to initialize.
- For basic memory CRUD after config is valid, switch to `../sdk-memory/SKILL.md`.
