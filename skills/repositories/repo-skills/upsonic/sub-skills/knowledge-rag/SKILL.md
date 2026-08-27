---
name: knowledge-rag
description: "Owns KnowledgeBase workflows: loaders, splitters, embeddings,
  vector DBs, OCR, and retrieval tooling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# knowledge-rag

Use this route for document ingestion, chunking, embedding, vector search, OCR, and `KnowledgeBase` workflows.

## Include

- `KnowledgeBase` construction and retrieval/search helpers.
- Loader, splitter, embedding, OCR, and vector DB selection.
- Document lifecycle methods such as add, refresh, update metadata, and retrieval tooling.

## Exclude

- Chat/session persistence → [chat-memory-storage](../chat-memory-storage/SKILL.md)
- Core model/provider selection → [models-and-providers](../models-and-providers/SKILL.md)
- Core agent execution → [agent-runtime](../agent-runtime/SKILL.md)

## Start here

- [references/knowledge-base-workflows.md](references/knowledge-base-workflows.md)
- [references/backends-and-extras.md](references/backends-and-extras.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/check_rag_optional_imports.py](scripts/check_rag_optional_imports.py)
