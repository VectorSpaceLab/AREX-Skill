# Provider Troubleshooting

Use this guide when Mem0 OSS provider configuration fails before or during add/search. Keep secrets out of logs: print whether an env var is present, never its value.

## Fast Triage

1. Confirm SDK and surface: Python `mem0ai` OSS `Memory` versus TypeScript `mem0ai/oss` `Memory`.
2. Validate config structure with the bundled script before constructing `Memory`.
3. Check provider spelling and Python/TypeScript casing differences.
4. Check optional dependency import errors and install the narrow missing package or extra.
5. Align embedding dimension with the vector collection.
6. Check backend availability: local path locks, server URL/port, credentials, collection name, and network reachability.
7. Remove stale v2/external graph settings (`enable_graph`, `graph_store`, `enableGraph`, `graphStore`).
8. If CRUD/search API usage is wrong after providers initialize, route to `../sdk-memory/SKILL.md`.

## Common Failures

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| `Unsupported LLM provider` / `Unsupported Embedder provider` | Provider string not in installed registry | Run `scripts/list_mem0_providers.py`; fix spelling/casing or upgrade the SDK intentionally. |
| `Unsupported vector store provider` | Python and TypeScript names mixed, e.g. `azure-ai-search` in Python or `azure_ai_search` in TS | Use `azure_ai_search` for Python and `azure-ai-search` for TypeScript. |
| `Extra fields not allowed` | Config block copied from another provider or wrong casing | Compare fields with the provider reference; remove unknown keys before constructing `Memory`. |
| Qdrant config says host/port, url/api_key, or path required | No connection mode supplied | For local dev provide a safe local `path`; for server use `host` + `port`; for cloud use `url` + `api_key`. |
| Shape/dimension mismatch such as `1536` vs `768` | Embedder dimension differs from collection/vector config | Python: set `embedding_model_dims`; TypeScript: set `vectorStore.config.dimension` or `embedder.config.embeddingDims`. Recreate or migrate incompatible collections. |
| `ModuleNotFoundError` for provider SDK | Optional dependency missing | Install only the provider's package or the narrow extra (`mem0ai[vector-stores]`, `mem0ai[llms]`, `mem0ai[extras]`, or `mem0ai[nlp]`). |
| Reranker import fails | Missing Cohere/sentence-transformers/Hugging Face/Zero Entropy dependency | Install the named reranker SDK or switch to vector-only search until dependency is available. |
| Search returns empty after add | Wrong filters, threshold too high, async/indexing delay, dimension mismatch, or semantic candidate miss | Use scoped filters, lower threshold, verify collection dimension, use `explain`, and test vector-only before rerank. |
| BM25 not affecting ranking | Vector store lacks `keyword_search`, missing `fastembed` for Qdrant, or missing NLP lemmatization | Confirm semantic search works; add optional keyword dependency only if the selected store supports it. |
| Entity graph boost missing | Entity extraction dependency absent, entity store unavailable, old memories lack entity links, or search query has no extractable entity | Add new test memories after installing NLP support; inspect `explain` score details. |
| `reference_date`, `timestamp`, or `decay` rejected | Platform-only temporal/decay feature used on OSS Memory | Remove those params or route to hosted Platform guidance in `../sdk-memory/SKILL.md`. |
| Old `relations` field missing | External graph store API removed | Use current combined score/entity boost behavior; redesign code that read graph relations directly. |

## Invalid Qdrant / Dimension Recovery

When a local Qdrant setup fails after switching from OpenAI embeddings to a 768-dimensional local embedder:

1. Decide whether existing data must be preserved. If not, use a new `collection_name` or local `path` to avoid mixed dimensions.
2. Set the vector dimension explicitly in the vector config.
3. Match the embedder model and dimension in the embedder config.
4. Validate config without constructing live providers.
5. Add one memory and search with a low threshold before enabling reranking.

Python example:

```python
config = {
    "vector_store": {"provider": "qdrant", "config": {"path": "/tmp/mem0-qdrant-768", "embedding_model_dims": 768}},
    "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text", "embedding_dims": 768}},
    "llm": {"provider": "ollama", "config": {"model": "llama3.2:3b", "ollama_base_url": "http://localhost:11434"}},
}
```

TypeScript example:

```ts
const memory = new Memory({
  embedder: { provider: "ollama", config: { model: "nomic-embed-text", embeddingDims: 768 } },
  vectorStore: { provider: "qdrant", config: { collectionName: "memories_768", dimension: 768 } },
  llm: { provider: "ollama", config: { model: "llama3.2:3b", url: "http://localhost:11434" } },
});
```

## Optional Dependency Diagnosis

When an import fails, map the missing module to the provider rather than installing every extra:

- `chromadb` → Chroma vector store.
- `faiss` → FAISS vector store.
- `psycopg` / `pgvector` context → PGVector.
- `redis` / `valkey` → Redis or Valkey vector store.
- `elasticsearch` / `opensearchpy` → Elasticsearch/OpenSearch vector store.
- `fastembed` → Qdrant BM25/sparse keyword search or FastEmbed embedder.
- `sentence_transformers` → local sentence-transformer embedder/reranker.
- `spacy` → NLP entity extraction and BM25 lemmatization.
- `ollama`, `groq`, `google`, `boto3`, `langchain` → corresponding LLM/embedder adapter.

If the environment is locked down, choose a provider already available in the environment or configure a local in-memory/SQLite TypeScript store for tests.

## API Key and Environment Checks

- OpenAI-compatible providers generally need an API key unless pointed at a local compatible base URL.
- Azure OpenAI may use API keys or Azure Identity depending on provider config; do not set conflicting credentials.
- Bedrock needs AWS credentials and region; default region may come from `AWS_REGION`.
- Hosted rerankers need their own keys; do not assume the LLM key covers reranking.
- Print only presence/absence: `OPENAI_API_KEY=set`, not the value.

## Backend Safety

- Local Qdrant path mode can lock RocksDB files; avoid sharing one path across unrelated processes unless the provider shares a client explicitly.
- Docker/server setup for REST/OpenMemory belongs in `../self-hosted-openmemory/SKILL.md`, not this sub-skill.
- Resetting/deleting collections is destructive; ask before running commands that delete vector data.
- When troubleshooting production data, prefer a new test collection over modifying the existing one.
