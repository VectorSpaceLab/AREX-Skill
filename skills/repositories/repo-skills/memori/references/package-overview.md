# Memori Package Overview

## Surfaces

| Surface | Package / import | Purpose | Typical install |
| --- | --- | --- | --- |
| Python SDK | `memori` | Cloud memory, BYODB, LLM registration, recall/search, embeddings, CLI helpers | `pip install memori` |
| TypeScript SDK | `@memorilabs/memori` | Node memory client, request scopes, storage, and LLM hooks | `npm install @memorilabs/memori` |
| Native core | bundled Rust/PyO3/napi runtime | Fast embeddings, queueing, retrieval helpers, and platform-specific bindings | installed with the Python wheel or Node build |

## Python install matrix

| Need | Recommended install |
| --- | --- |
| Base package and CLI | `pip install memori` |
| SQLAlchemy-oriented BYODB recipes | `pip install 'memori[sqlalchemy]'` |
| TiDB Zero provisioning recipes | `pip install 'memori[tidb-zero]'` |
| CockroachDB recipes | `pip install 'memori[cockroachdb]'` |

The Python package supports `>=3.10`. The current package metadata reports
version `3.3.7`.

## Public runtime objects

| Area | Key entry points |
| --- | --- |
| Package entry | `Memori` |
| LLM registration | `Memori().llm.register(...)` |
| BYODB provisioning | `Memori.provision(...)` |
| Cloud agent API | `Memori.agent_recall(...)`, `agent_recall_summary(...)`, `agent_compaction(...)`, `capture_agent_turn(...)`, `agent_feedback(...)` |
| Memory lifecycle | `attribution(...)`, `new_session()`, `set_session(...)`, `recall(...)`, `delete_entity_memories(...)` |
| Search | `search_facts(...)`, `FactCandidate`, `FactSearchResult` |
| Embeddings | `embed_texts(...)`, `TEI(...)` |
| Native runtime | `RustCoreAdapter` |

## TypeScript install notes

- Package name: `@memorilabs/memori`
- Node engines: `>=20.19.0`
- Peer dependencies are optional for some providers and storage drivers.
- The package exposes `Memori`, `MemoriRequestScope`, `forRequest(...)`, and
  storage/LLM integration helpers.

## What to read next

- Read `configuration.md` for environment variables and defaults.
- Read `troubleshooting.md` for install/import and runtime failure modes.
- Use the sub-skill references for deeper API, CLI, and workflow details.
