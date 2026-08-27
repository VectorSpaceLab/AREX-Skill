---
name: chat-memory-storage
description: "Owns Chat sessions, Memory orchestration, and storage backends for
  persisted conversations and user/session memory."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# chat-memory-storage

Use this route for `Chat`, `Memory`, and storage backend questions: session history, user memory, persistence, and backend swapping.

## Include

- `Chat` session lifecycle and invocation methods.
- `Memory` configuration, session/user ids, summary memory, user analysis memory, and load/save flags.
- Storage backends such as in-memory, JSON, SQLite, Redis, PostgreSQL, MongoDB, and Mem0 variants.

## Exclude

- Knowledge-base ingestion and retrieval → [knowledge-rag](../knowledge-rag/SKILL.md)
- Core model/provider selection → [models-and-providers](../models-and-providers/SKILL.md)
- Core agent execution semantics → [agent-runtime](../agent-runtime/SKILL.md)

## Start here

- [references/chat-and-memory.md](references/chat-and-memory.md)
- [references/storage-backends.md](references/storage-backends.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/check_storage_backends.py](scripts/check_storage_backends.py)
