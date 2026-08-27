---
name: knowledge-data-memory
description: "Operate Nexent document processing, knowledge-base vector search,
  storage, and memory workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Knowledge, Data, and Memory

Use this sub-skill for Nexent tasks involving document/data processing, file upload or conversion, chunk management, vector database indexing/search, storage-backed knowledge-base files, knowledge summaries, memory records, memory retrieval, memory tools, Dreaming, or long-term memory.

Do **not** use this sub-skill for generic agent runtime/model wiring, ordinary FastAPI architecture rules, frontend UI implementation, or live infrastructure deployment. Route those tasks to sibling sub-skills:

- SDK agent run/model/tool configuration: [sdk-agent-runtime](../sdk-agent-runtime/SKILL.md)
- Generic backend route/service/database rules: [backend-services-api](../backend-services-api/SKILL.md)
- Knowledge or memory UI behavior: [frontend-integration](../frontend-integration/SKILL.md)
- Redis, Elasticsearch, MinIO, Ray, Celery, Docker, or Kubernetes deployment: [deployment-operations](../deployment-operations/SKILL.md)

## Start Here

1. Classify the task:
   - File parsing, chunking, conversion, OCR/image extraction, or process/forward tasks: read [data-processing](references/data-processing.md).
   - Knowledge-base CRUD, vector search, chunk editing, summaries, MinIO objects, or `knowledge_base_search`: read [vector and storage](references/vector-and-storage.md).
   - Memory switches, records, retrieval scoring, memory tools, Dreaming, or long-term versions: read [memory workflows](references/memory-workflows.md).
   - Any failure triage: read [troubleshooting](references/troubleshooting.md) before changing code.
2. Prefer pure/static checks first. The bundled diagnostic script is safe and does not start Redis, Elasticsearch, MinIO, Celery, Ray, or provider APIs:

   ```bash
   python scripts/check_knowledge_stack.py --repo-root <repo-root> --json
   ```

3. Keep live-service assumptions explicit. Unit tests and mocked service tests are valid evidence for most tasks; real Elasticsearch/MinIO/Redis/Celery/Ray/LibreOffice/model-provider behavior requires user-provided infrastructure.

## Operating Rules

- Treat SDK imports as the public API surface: `nexent.data_process`, `nexent.vector_database`, `nexent.storage`, `nexent.memory`, and `nexent.core.tools.knowledge_base_search_tool`.
- Treat backend apps as HTTP boundaries and backend services as orchestration boundaries. For broad backend conventions, defer to [backend-services-api](../backend-services-api/SKILL.md).
- Keep environment-variable reads centralized in the backend constants module when editing backend code. Do not add direct `os.getenv()` calls in new knowledge or memory services.
- Separate CPU-import checks from live stack checks. Import success proves package availability, not that Redis, Elasticsearch, MinIO, Celery, Ray, LibreOffice, or embedding providers are reachable.
- For vector data, always distinguish the knowledge-base display name from the internal index name. Use permission-filtered index names for search tools and route UI display-name conversion through the backend/tool mapping.
- For memory, remember the current architecture: tenant and user long-term memories are versioned/full-context; agent short-term memories are vector-retrieved and may be promoted by Dreaming.

## High-Value Triage Patterns

- **PPTX upload/data-process failure:** decide whether the failure is upload-size/format validation, missing optional data-process dependencies, missing or hung LibreOffice conversion, missing image/OCR model cache, Redis/Celery/Ray task orchestration, or Elasticsearch forwarding. Use the playbook in [troubleshooting](references/troubleshooting.md#pptx-upload-or-processing-failures).
- **Memory retrieval scoring test:** avoid live providers. Build `MemorySearchResult`/`ExternalMemoryItem` fixtures and exercise `RetrievalPipeline`, `ScoreFusion`, `TemporalDecayer`, `MMRDeduplicator`, and `TokenBudgetSelector` directly; use mocked backend services for HTTP/service paths. See [memory workflows](references/memory-workflows.md#pure-and-mocked-memory-tests).
- **Knowledge-base search permission bug:** verify backend read permission filtering, display-name-to-index mapping, `allowed_index_names`, optional `document_paths`, then check `hybrid`/`accurate`/`semantic` search mode behavior.
