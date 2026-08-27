# M-flow Configuration

## When to read

Read this reference when a task needs environment variables, optional extras,
credentials, storage backends, LLM/embedding provider routing, or local runtime
layout before using M-flow.

## Installation and extras

Base install:

```bash
pip install mflow-ai
python -c "import m_flow; print(m_flow.__version__)"
mflow --help
```

Use only the extras required by the task. Important optional groups include:

| Extra | Use when |
| --- | --- |
| `anthropic`, `gemini`, `groq`, `cohere`, `huggingface`, `ollama` | the selected LLM provider needs a provider SDK or local model tooling |
| `neo4j`, `neptune`, `graphiti` | graph storage or graph integration uses those services |
| `postgres` / `postgres-binary` | relational Postgres or pgvector workflows are selected |
| `chromadb`, `redis`, `pinecone`, `milvus` | vector/cache providers need those clients |
| `embeddings` | local FastEmbed / ONNX embedding checks are needed |
| `docs`, `scraping`, `docling`, `dlt` | richer document parsing, web scraping, docling, or relational ETL is needed |
| `baml` | BAML structured-output backend is selected |
| `langchain`, `llama-index` | framework integration code paths are selected |
| `coreference-full` | optional source-installed coreference support is selected |
| `codegraph`, `evals`, `deepeval`, `monitoring`, `deploy`, `distributed`, `aws` | specialized analysis, evaluation, observability, deployment, Modal, or S3 workflows are selected |

Do not install all extras just to inspect the package. External DBs, browser
scraping, face recognition, cloud sync, and distributed workers each need extra
services or credentials beyond Python packages.

## Core environment variables

M-flow accepts `MFLOW_`-prefixed variables and many bare-name fallbacks. The
bare names below match the public template and are usually enough locally.

| Area | Variables | Notes |
| --- | --- | --- |
| Runtime | `ENV`, `TOKENIZERS_PARALLELISM`, `TELEMETRY_DISABLED`, `DEFAULT_USER_EMAIL`, `DEFAULT_USER_PASSWORD` | keep telemetry and demo defaults explicit in production |
| Auth | `REQUIRE_AUTHENTICATION`, `ENABLE_BACKEND_ACCESS_CONTROL`, `FASTAPI_USERS_JWT_SECRET`, `FASTAPI_USERS_RESET_PASSWORD_TOKEN_SECRET`, `FASTAPI_USERS_VERIFICATION_TOKEN_SECRET` | strict environments require real secrets; local/dev may warn about defaults |
| LLM | `LLM_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_ENDPOINT`, `LLM_API_VERSION`, `LLM_MAX_TOKENS`, `LLM_INSTRUCTOR_MODE` | graph construction and triplet-answer generation need a working LLM path |
| Embeddings | `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_ENDPOINT`, `EMBEDDING_API_KEY`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_BATCH_SIZE` | embedding key falls back to the LLM key when unset |
| Storage roots | `DATA_ROOT_DIRECTORY`, `SYSTEM_ROOT_DIRECTORY`, `CACHE_ROOT_DIRECTORY`, `STORAGE_BACKEND`, S3 credentials | keep file-backed defaults for simple local work |
| Relational DB | `DB_PROVIDER`, `DB_NAME`, `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD` | default is SQLite |
| Vector DB | `VECTOR_DB_PROVIDER`, `VECTOR_DB_URL`, `VECTOR_DB_KEY`, provider-specific variables | default is LanceDB |
| Graph DB | `GRAPH_DATABASE_PROVIDER`, `GRAPH_DATABASE_URL`, `GRAPH_DATABASE_NAME`, `GRAPH_DATABASE_USERNAME`, `GRAPH_DATABASE_PASSWORD` | default is Kuzu |
| Pipeline tuning | `MFLOW_CONTENT_ROUTING`, `MFLOW_EPISODIC_ENABLE_ROUTING`, `MFLOW_EPISODE_SIZE_CHECK_AUTO`, `MFLOW_PROCEDURAL_ENABLED`, `MFLOW_PRECISE_MODE`, `MFLOW_AUTO_DETECT_DIALOG`, concurrency variables | most can also be overridden per API call |
| UI / cloud / playground | `UI_APP_URL`, `MFLOW_CLOUD_API_URL`, `MFLOW_CLOUD_AUTH_TOKEN`, `FACE_API_KEY` | required only for those integrations |

## Provider routing

For OpenAI-compatible custom LLM providers, set:

```bash
export LLM_PROVIDER=custom
export LLM_MODEL=openai/provider-model-name
export LLM_ENDPOINT=https://provider.example.com
export LLM_API_KEY=...
```

If structured output fails, try `LLM_INSTRUCTOR_MODE=markdown_json_mode` or a
provider-specific JSON/tool mode. If the provider model is not recognized by
LiteLLM, prefix the model with `openai/` to force the OpenAI-compatible path.

## Local defaults

For a fresh local stack, the default providers are:

- relational metadata: SQLite
- vector store: LanceDB
- graph store: Kuzu
- cache: filesystem/disk cache unless Redis is configured

These defaults do not require external DB services, but they do write local
system/data directories. Use the root `scripts/check_mflow_env.py` helper before
live operations to see which provider settings are visible without mutating
storage.

## Switching storage backends

1. Install only the required extra or client package.
2. Set provider variables and service URL/credentials.
3. Use the retrieval sub-skill's backend probe before a live run.
4. Start or verify the external service separately.
5. Run a small, user-approved ingestion/retrieval smoke after the service is healthy.

Never treat a package import as proof that Neo4j, Postgres, ChromaDB, Pinecone,
Milvus, Redis, or a remote Kuzu service is reachable.
