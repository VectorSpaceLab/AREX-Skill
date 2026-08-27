---
name: memory-and-search
description: "Routes Memori attribution, sessions, recall/search, embeddings,
  and native Rust-core workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Memory and Search

Use this sub-skill for Memori's memory lifecycle, recall/search behavior,
embeddings, augmentation timing, and native Rust-core troubleshooting.

## Use when

- The request mentions attribution, sessions, recall, empty recall, search,
  embeddings, TEI, augmentation wait, native runtime behavior, or memory
  deletion.
- The user is debugging why memories are not showing up or why the Rust core
  path is unavailable.
- The task is about retrieval behavior rather than database setup or provider
  registration.

## Read first

- `references/memory-lifecycle.md` for attribution and session flow.
- `references/search-and-embeddings.md` for search and embedding APIs.
- `references/native-and-embeddings.md` for native-core and model notes.
- `references/troubleshooting.md` for recall, wait, and native failures.
- `scripts/search_candidates_smoke.py` for a safe offline search smoke.

## What this sub-skill owns

- `attribution(...)`, `new_session()`, `set_session(...)`, `recall(...)`, and
  `delete_entity_memories(...)`.
- `search_facts(...)`, `FactCandidate`, `FactSearchResult`, and candidate-mode
  search.
- `embed_texts(...)`, `TEI(...)`, and the native Rust core fallback path.
- Short-script augmentation advice such as `augmentation.wait()`.

## What it does not own

- Cloud API keys and MCP setup: use `cli-and-cloud`.
- Storage schema and provisioning: use `byodb-storage`.
- Provider/framework registration: use `llm-integration`.
- TypeScript-specific memory APIs: use `typescript-sdk`.

## Safe first check

Run the bundled search smoke before assuming retrieval is broken:

```bash
python scripts/search_candidates_smoke.py
```

That helper exercises pre-scored candidates and does not require a database,
network, or embedding model download.
