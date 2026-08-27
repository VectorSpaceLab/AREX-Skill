---
name: "search-retrieval"
description: "Helps users choose Cognee search and recall modes, tune retrieval
  controls, and diagnose empty or invalid query behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cognee Search and Retrieval

Use this sub-skill when the user wants to query stored memory, compare retrieval modes, or understand why a `search`/`recall` query behaves the way it does.

## Route here for

- `search(...)` and `recall(...)` mode selection.
- `SearchType` values and query routing.
- Session-aware retrieval, graph-only retrieval, code search, temporal search, and agentic completion.
- Query controls such as `top_k`, `node_name`, `scope`, `datasets`, `dataset_ids`, and `include_references`.
- Explaining empty results or invalid query combinations.

## Route away

- Ingestion/storage/build workflows: [core-memory](../core-memory/SKILL.md).
- Provider and backend setup: [configuration-backends](../configuration-backends/SKILL.md).
- Session memory/feedback decorators and agent SDK flows: [agent-session-memory](../agent-session-memory/SKILL.md).
- Custom graph schemas and pipelines: [advanced-graphs-pipelines](../advanced-graphs-pipelines/SKILL.md).
- CLI/service usage: [api-cli-services](../api-cli-services/SKILL.md).

## Read first

1. [references/search-modes.md](references/search-modes.md)
2. [references/api-reference.md](references/api-reference.md)
3. [references/troubleshooting.md](references/troubleshooting.md)

## Safe helper

- [scripts/choose_search_mode.py](scripts/choose_search_mode.py) — suggests a search mode from intent flags and prints the rationale.

## Working rules

- Use `recall` when the user wants session-aware retrieval or a memory-oriented phrasing.
- Use `search` when the user wants the lower-level graph query surface or explicit `SearchType` control.
- Always check whether the user asked for graph context, chunks, summaries, code traversal, or agentic completion; those intents map to different `SearchType` values.
- Validate `code_query` only with `SearchType.CODE` and `skills`/`tools` only with `SearchType.AGENTIC_COMPLETION`.
- Route provider/embedding/database problems back to the configuration sub-skill.
