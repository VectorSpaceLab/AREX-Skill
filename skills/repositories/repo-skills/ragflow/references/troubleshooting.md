# RAGFlow Troubleshooting Router

Use this reference to route cross-cutting failures to the nearest focused sub-skill.

## Deployment and Services

Read [deployment-configuration](../sub-skills/deployment-configuration/SKILL.md) when:

- Docker Compose starts but RAGFlow is unreachable or unhealthy.
- `DOC_ENGINE` does not match Elasticsearch, Infinity, OpenSearch, OceanBase, or service configuration.
- MySQL, Redis, MinIO, NATS, document engine, or embedding service health fails.
- Source launch fails due Python version, dependency setup, import path, API/task-executor process split, or frontend/backend port confusion.

## Backend APIs and Auth

Read [backend-api-services](../sub-skills/backend-api-services/SKILL.md) when:

- A route 404s because it is registered under `/api/v1` versus legacy `/v1`.
- Request validation rejects JSON, form, or missing required fields.
- API-token, JWT, session, login, or password hashing behavior is confusing.
- Peewee service logic, route handlers, response helpers, or compatibility aliases need changes.

## Public API and SDK Clients

Read [sdk-http-integration](../sub-skills/sdk-http-integration/SKILL.md) when:

- A client sees 401/403/404/500 responses, duplicate `/api/v1` prefixes, wrong SDK `base_url`, or deprecated endpoint aliases.
- OpenAI-compatible chat streaming, references, metadata filters, or non-stream fallback needs debugging.
- Dataset/document/chunk/retrieval calls need request examples or error-code interpretation.

## Ingestion and Retrieval

Read [dataset-ingestion-retrieval](../sub-skills/dataset-ingestion-retrieval/SKILL.md) when:

- Uploads parse but retrieval returns no chunks.
- `parser_config`, `chunk_method`, metadata filters, embedding model, vector size, or doc-engine indexes disagree.
- Task executor, queue, RAPTOR, GraphRAG, checkpoint, phase-marker, or retrieval-ranking behavior is the likely source.

## Document Parsing

Read [document-parsing](../sub-skills/document-parsing/SKILL.md) when:

- PDF/DOCX/XLSX/PPT/HTML/Markdown/JSON/TXT/EPUB parsing fails or produces unexpected text, tables, images, or metadata.
- OCR/layout backends such as MinerU, Docling, PaddleOCR, Tencent, or OpenDataLoader are missing or misconfigured.
- Scanned PDFs produce empty chunks or parser-specific unit tests fail.

## Agent, Memory, MCP, and Sandbox

Read [agent-workflows](../sub-skills/agent-workflows/SKILL.md) when:

- Agent canvas variables, path ordering, loop/iteration behavior, component inputs/outputs, template JSON, tool credentials, sandbox execution, webhooks, debug traces, memory, or MCP retrieval fail.

## Frontend Integration

Read [frontend-integration](../sub-skills/frontend-integration/SKILL.md) when:

- Frontend endpoint constants, request wrappers, services, hooks, React Query invalidation, route enums, parser_config forms, agent canvas UI, or Jest/lint/type-check workflows need work.

## Packaging Caveat

For source inspection and maintenance, prefer the repository-supported `uv` setup. A plain editable install can fail if package metadata expects a top-level `graphrag` package while GraphRAG code is organized under `rag/graphrag`; treat that as a packaging/setup issue and continue with source-level inspection or the supported install workflow.
