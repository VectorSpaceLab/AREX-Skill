---
name: "knowledge-models"
description: "Covers MaxKB knowledge/RAG flows plus model-provider and
  local-model integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# knowledge-models

Use this sub-skill for knowledge-base, vector-search, and model-provider tasks.

## Owns
- `apps/knowledge/*` knowledge/document/paragraph/problem/termbase surfaces.
- `apps/models_provider/*` provider abstraction, model CRUD, and credential handling.
- `apps/local_model/*` local model service endpoints.
- RAG search, embedding, reranker, and provider/local-model troubleshooting.

## Do not own
- Runtime bootstrap and service commands -> `runtime-architecture`.
- Workflow/chat/MCP execution -> `workflow-chat-mcp`.
- Vue/Vite UI contract -> `frontend-integration`.
- Management-only user/permission/tool/trigger pages -> `admin-access`.

## Key files
- `references/knowledge-and-models.md`
- `references/troubleshooting.md`
- `scripts/knowledge_model_surface.py`

## Guidance
- Treat retrieval and provider selection as one chain when diagnosing RAG issues.
- Make clear when a problem is in knowledge indexing versus model availability.
- Keep provider claims tied to the registered model catalog, not to assumptions about vendor SDKs.
