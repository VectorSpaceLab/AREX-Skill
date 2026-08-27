---
name: provider-configuration
description: "Configure Mem0 OSS providers, vector stores, embedders, LLMs,
  rerankers, hybrid retrieval, built-in graph memory, optional dependencies, and
  provider troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mem0 Provider Configuration

Use this sub-skill when a task mentions Mem0, `mem0ai`, the Mem0 memory layer, OSS `Memory`, provider setup, vector stores, embedders, LLMs, rerankers, Qdrant dimensions, hybrid retrieval, BM25, entity graph boosts, optional extras, or provider import/configuration failures.

## Route First

- Use this sub-skill for OSS component configuration: Python provider registry/config classes, TypeScript OSS config manager, optional dependency selection, vector/embedder dimension alignment, rerankers, built-in graph/entity retrieval, BM25, and provider troubleshooting.
- Route CRUD/search/add/update/delete usage to `../sdk-memory/SKILL.md` after provider selection is settled.
- Route CLI command syntax and terminal workflows to `../cli-memory/SKILL.md`.
- Route Docker REST server, OpenMemory, auth, containers, migrations, and self-hosted service configuration to `../self-hosted-openmemory/SKILL.md`.
- Route editor/agent plugins, Vercel AI SDK, MCP, OpenClaw, Pi Agent, and framework integrations to `../integrations-plugins/SKILL.md`.

## Provider Workflow

1. Identify the SDK surface: Python OSS uses `Memory.from_config(config_dict)` or `Memory(MemoryConfig(...))`; TypeScript OSS uses `new Memory(config)` from `mem0ai/oss` and `ConfigManager.mergeConfig` internally.
2. Pick the smallest provider set that satisfies the workflow. Prefer local/read-only defaults for validation; do not install broad extras unless the selected providers need them.
3. Align vector dimensions with the embedder: Python vector configs use fields such as `embedding_model_dims`; TypeScript vector configs use `dimension`, or let auto-detection run when safe.
4. Add reranking only when baseline search works. Configure a `reranker` block, then call search with `rerank=True` in Python when the workflow needs the second pass.
5. Treat graph memory as built-in entity linking in current OSS Mem0. Remove stale `enable_graph`/`graph_store` settings; entity links and boosts use the existing vector store.
6. Validate configuration structure before running live memory operations. Use `scripts/validate_memory_config.py` for read-only Python checks and `scripts/list_mem0_providers.py` for provider inventory.

## References

- `references/python-providers.md` — Python provider registries, config fields, examples, extras, and validation patterns.
- `references/typescript-oss-providers.md` — TypeScript OSS providers, config manager behavior, dimensions, peer dependencies, and naming differences.
- `references/retrieval-features.md` — BM25, entity boosts, built-in graph memory, reranking, metadata filters, and temporal/decay boundaries.
- `references/troubleshooting.md` — import failures, credentials, dimensions, backend availability, validation errors, and stale graph settings.

## Bundled Scripts

- `scripts/list_mem0_providers.py --help` lists provider names from installed Mem0 registries without constructing providers.
- `scripts/validate_memory_config.py --config config.json` validates a Python OSS config dictionary with Pydantic only; it avoids opening network connections or constructing `Memory` by default.
