---
name: rag-memory
description: "AgentScope retrieval, vector-store, and long-term memory workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# rag-memory

Use this sub-skill for document indexing, vector search, agent-attached RAG, filesystem memory, mem0, and ReMe.

## Read first

- `references/workflows.md` for the end-to-end indexing and memory patterns.
- `references/vector-stores.md` for Qdrant, Milvus Lite, MongoDB, and Elasticsearch choices.
- `references/troubleshooting.md` for dimension, backend, and memory-mode failures.
- The bundled scripts in `scripts/` for local demos.

## Typical triggers

- "How do I index documents and search them?"
- "How do I attach RAG to an agent?"
- "How do filesystem memory, mem0, or ReMe work?"
- "Which vector store or embedding dimension should I use?"

## What belongs here

- `KnowledgeBase`, `TextParser`, `ApproxTokenChunker`, `QdrantStore`
- `RAGMiddleware`
- `AgenticMemoryMiddleware`, `Mem0Middleware`, `ReMeMiddleware`
- vector-store selection and memory-backend selection
- safe RAG and filesystem-memory demos

## What does not belong here

- provider credentials and model-family selection → `provider-connectors`
- agent/tool/permission basics → `agent-core`
- service bootstrap, storage, and deployment → `service-platform`
- workspace backend configuration → `workspace-sandboxes`

## Use pattern

1. Decide whether the workflow is pure retrieval or retrieval plus an agent.
2. Pick the vector store or memory backend that matches the deployment target.
3. Match the embedding dimension before changing the code.
4. Use the bundled scripts for the local demos first.
5. Read the troubleshooting page before touching the backend config if a memory or vector call fails.

## Bundled scripts

- `scripts/index_and_search.py` — standalone RAG indexing/search demo.
- `scripts/integrate_with_agent.py` — attach `RAGMiddleware` to an agent.
- `scripts/agentic_memory_demo.py` — filesystem-backed long-term memory demo.

## Cross-links

- If the embedding model itself is the issue, switch to `provider-connectors`.
- If the task is really about workspace file placement or sandboxed backends, switch to `workspace-sandboxes`.
- If the task is about service deployment or KB endpoints, switch to `service-platform`.
