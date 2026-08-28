# Architecture and Terminology

Read this when a task crosses deployment, ingestion, retrieval, agents, tools, or client APIs.

## Component map

| Component | Role | Depends on |
|---|---|---|
| ASGI application | Full HTTP surface: Flask routes plus `/mcp` and async message-event reconnect | Python runtime, configuration, Postgres for persisted data; Redis for full realtime/background behavior |
| Flask application | Core WSGI routes including `/api/*`, `/stream`, and `/v1/*` | same backend dependencies; lacks ASGI-only mounts |
| Postgres | Canonical user-data store for users, conversations, agents, sources, workflows, logs, schedules, artifacts metadata, and token usage | schema migrations; pgvector extension only when used as vector store/GraphRAG |
| Redis | Cache, Celery broker/result backend, schedule coordination, SSE replay/broadcast, and device brokering | independently reachable Redis service |
| Celery workers | ingestion, parsing, titles, schedules, GraphRAG extraction and other background jobs | broker/result backend; package dependencies; source/vector/object storage |
| Parsing pipeline | converts files/remote content to normalized documents, chunks, embeddings, and source records | parser dependencies, embeddings, vector store, parsing worker for queued tasks |
| Retriever dispatcher | applies per-source retrieval policy and combines context | vector store, source config, optional LLM calls for rephrase/pre-screen |
| Agent layer | classic, agentic, research, or workflow execution | LLM, sources, tools, prompts, persisted conversation state |
| Tool layer | internal search, web/API/MCP actions, memory/notes/schedules, artifacts/code, remote devices | tool-specific credentials/services and approval policy |
| Frontend/widgets/clients | call native or OpenAI-compatible APIs and render streams/events | backend base URL, auth/API key, CORS/reverse-proxy correctness |

## Canonical terms

- **Source**: an ingested corpus plus source-level configuration and ownership/sharing metadata.
- **Attachment**: a user-scoped file uploaded for a turn or workflow run; processing is asynchronous before it can be referenced.
- **Artifact**: a versioned file produced by a tool or workflow, stored outside the model context and referenced by id.
- **Chunking**: ingest-time transformation. Settings are baked into stored chunks.
- **Retrieval**: query-time selection of chunks. Most settings take effect without re-ingestion.
- **Exposure**: `prefetch` injects context before generation; `agentic_tool` lets the model search on demand.
- **Classic agent**: prefetch-style RAG with optional tool use.
- **Agentic agent**: gives the model an internal search tool and lets it decide when to retrieve.
- **Research agent**: bounded clarification, planning, research, and synthesis phases.
- **Workflow agent**: executes a predefined node graph with shared state.
- **Headless run**: schedule or webhook execution without an interactive client; avoid tools that require live user interaction.
- **Native API**: DocsGPT-specific `/api/answer`, `/stream`, attachment, source, agent, tool, and workflow endpoints.
- **OpenAI-compatible API**: `/v1/chat/completions` and `/v1/models`; the API key selects the DocsGPT agent, and the request `model` field does not.

## End-to-end data path

1. A file, remote loader, or connector creates a source and queues ingestion.
2. The parser normalizes content and applies the source's chunking configuration.
3. Embeddings are generated and chunks are written to the selected vector store; source/user metadata remains in Postgres.
4. A chat request resolves an agent or request-level configuration.
5. The dispatcher retrieves per-source context or exposes source search as a tool.
6. The selected agent invokes the LLM and optional tools.
7. Native SSE or OpenAI-compatible streaming returns answer deltas and DocsGPT metadata; durable events support reconnect when Redis/journaling is available.

## Boundary decisions

- Use Postgres for user data regardless of vector-store choice. MongoDB is legacy/optional and only selected explicitly as a vector store or migration source.
- Do not use the frontend as an API contract. Validate clients against endpoint responses and event schemas.
- Keep model-provider configuration distinct from vector embeddings configuration; both can use OpenAI-compatible servers but have separate base URLs/keys.
- A task id proves enqueueing, not completion. Poll task/run status and validate persisted results.
- A passing unit check with mocks does not prove a live external service, credential, vector database, OAuth flow, or sandbox backend.
