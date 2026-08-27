---
name: knowledge-rag
description: "Operate on BiSheng knowledge libraries, knowledge spaces, document
  ingestion, parser providers, RAG pipeline, Milvus/Elasticsearch recall, and
  knowledge workers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# knowledge-rag

Use this sub-skill when a task touches BiSheng knowledge libraries, knowledge spaces, QA libraries, file upload/parse states, document parser providers, the Load → Transform → Ingest pipeline, Milvus + Elasticsearch dual recall, MinIO file artifacts, or `knowledge_celery` worker behavior.

## Start here

Run bundled helper commands from this sub-skill directory, or adjust the script path to this directory after import.


1. Inspect config-shaped text before debugging parser/storage problems:
   ```bash
   python scripts/check_knowledge_config.py --config <bisheng-checkout>/docker/bisheng/config/config.yaml
   ```
2. Read [references/workflows.md](references/workflows.md) for ingestion, parser, retrieval, and worker workflows.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for parser, object storage, vector index, queue, and permission symptoms.

## Owned responsibilities

- Knowledge API/domain services under `src/backend/bisheng/knowledge/`.
- RAG pipeline files under `knowledge/rag/`, especially file pipelines, loader/provider selection, transformers, Milvus and Elasticsearch factories.
- `bisheng_langchain/rag/` retrievers, RAG pipeline, scoring, and rerank integration when used by BiSheng knowledge workflows.
- Knowledge Celery workers under `src/backend/bisheng/worker/knowledge/`.
- Tests under `src/backend/test/knowledge/`, `test/knowledge/rag/`, and safe config/service tests.
- Frontend knowledge-space or knowledge-library callers only at routing depth; UI rendering details belong to `frontend-apps`.

## Route sibling areas instead of duplicating them

- Use `identity-permissions-tenancy` for space visibility, OpenFGA/ReBAC, approval, tenant filtering, and cursor permission scans.
- Use `workflow-engine` for workflow RAG node execution outside the knowledge pipeline itself.
- Use `backend-core` for generic FastAPI router/envelope/service conventions.
- Use `frontend-apps` for Platform/Client knowledge pages and request wrappers.
- Use `deployment-maintenance` for Docker storage service startup and production config rollout.

## Non-negotiables

- Treat Load, Transform, and Ingest as separate stages when debugging: a loader success does not prove vector writes or preview cache.
- Preserve Milvus dense and Elasticsearch sparse/BM25 behavior when changing retrieval.
- Do not run external parser services, OCR downloads, or large document parsing as a smoke check unless the environment is approved.
- Use small fixtures for tests; do not require production MinIO/Milvus/ES for unit-level parser or service logic.
- Keep parser-provider credentials, endpoints, and object-storage secrets out of skill output and committed test fixtures.
