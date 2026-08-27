# Storage And Providers

MemMachine server resources are configured by IDs and referenced from memory
sections. A config field such as `embedder: openai_embedder` means the server
will look under `resources.embedders.openai_embedder`.

## Database And Store Resources

| Provider surface | Typical role | Notes |
| --- | --- | --- |
| PostgreSQL / pgvector | profile storage, segment store, semantic storage | Requires host/port/user/password/db and a running database. |
| SQLite / aiosqlite | local relational storage | Good for local/dev; check concurrency limitations. |
| Neo4j | graph/vector graph store | Requires Bolt URI, user/password, connection pool settings, and running Neo4j. |
| Nebula | graph/vector graph store | Requires optional dependency and external Nebula service. |
| Qdrant | vector store | Requires optional client dependency and Qdrant service or cloud credentials. |
| Milvus / Milvus Lite | vector store | Requires optional dependency; local `.db` URI differs from server/cloud URI. |
| SQLite vector store | local vector store | Good for small/dev cases; single-writer and index-persistence settings matter. |
| USEARCH / HNSWlib | ANN vector search engines | HNSWlib is optional and may require wheels/compilers. |

## Embedder Providers

| Provider | Config fields | Cautions |
| --- | --- | --- |
| OpenAI-compatible | `model`, `api_key`, `base_url`, `dimensions`, `max_input_length` | Works for OpenAI and compatible endpoints; verify dimensions match the model. |
| Amazon Bedrock | `region`, `model_id`, AWS credentials/session token, `max_input_length` | Requires AWS auth and region; do not print credentials. |
| Sentence Transformer | `model`, `max_input_length` | Optional dependency; may download local model files; GPU use must be verified separately. |

## Language-model Providers

| Provider | Config fields | Cautions |
| --- | --- | --- |
| `openai-responses` | `api_key`, `model`, `base_url` | Uses OpenAI Responses-style API path. |
| `openai-chat-completions` | `api_key`, `model`, `base_url` | Use for OpenAI-compatible/Ollama-style endpoints. |
| `amazon-bedrock` | `region`, `model_id`, AWS credentials/session token, optional inference config | Requires AWS auth and supported model ID. |

## Rerankers

| Reranker | Use | Cautions |
| --- | --- | --- |
| `identity` | Pass-through/no-op ranking | Useful fallback for development. |
| `bm25` | Lexical ranking | Requires text terms and local scoring. |
| `embedder` | Embedding-based reranking | Needs configured embedder. |
| `rrf-hybrid` | Reciprocal-rank fusion over multiple rerankers | Referenced reranker IDs must exist. |
| `cohere` | Cohere reranking | Requires Cohere API key/quota. |
| Cross-encoder | Local/model reranking | Requires optional model dependency and possible downloads. |

## Optional Extras And Verification

Install optional extras only for selected workflows:

```bash
python -m pip install "memmachine-server[qdrant]"
python -m pip install "memmachine-server[milvus]"
python -m pip install "memmachine-server[hnswlib]"
python -m pip install "memmachine-server[litellm]"
```

The `gpu` extra installs sentence-transformer support in the source baseline;
it does not prove CUDA execution. A real GPU claim requires a device-aware
smoke test in the user's environment.

## Resource Debugging Checklist

1. Does the config section reference an ID that exists in `resources`?
2. Is the provider string spelled exactly as the server expects?
3. Are required fields present after environment-variable interpolation?
4. Is the external service reachable from the server process?
5. Are credentials valid and unexpired?
6. Does the chosen memory backend expect this resource type?
7. Is the optional Python dependency installed in the server environment?
8. Is the failure a configuration validation error, connection error, provider
   quota/auth error, or runtime model error?

For provider retries, use the config API wrapper or REST endpoint only after
fixing the underlying configuration. Retrying a bad key or missing service will
usually reproduce the same failure.
