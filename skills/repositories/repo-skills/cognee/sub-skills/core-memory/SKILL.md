---
name: "core-memory"
description: "Guides Cognee's primary memory workflows: remember, recall,
  improve, forget, add, cognify, and search."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cognee Core Memory

Use this sub-skill when a user wants to store information in Cognee, turn it into a graph, query it back, or decide whether to use the newer memory API or the legacy pipeline API.

## Route here for

- `remember(...)` / `recall(...)` / `improve(...)` / `forget(...)`.
- Legacy `add(...)` / `cognify(...)` / `search(...)` when the user is already thinking in pipeline terms.
- Choosing between session memory and permanent graph memory.
- Understanding dataset names, dataset ids, `node_set`, background runs, and dry runs.
- Interpreting `RememberResult` and basic return shapes.

## Route away

- Search-mode selection, temporal/code/agentic retrieval tuning: [search-retrieval](../search-retrieval/SKILL.md).
- Provider, storage, and database configuration: [configuration-backends](../configuration-backends/SKILL.md).
- Session/cache, agents SDK, feedback storage, and decorator flows: [agent-session-memory](../agent-session-memory/SKILL.md).
- Custom graph models, ontologies, migration, and visualization: [advanced-graphs-pipelines](../advanced-graphs-pipelines/SKILL.md).
- CLI/service/MCP/Docker/UI launch: [api-cli-services](../api-cli-services/SKILL.md).

## Read first

1. [references/workflows.md](references/workflows.md)
2. [references/api-reference.md](references/api-reference.md)
3. [references/troubleshooting.md](references/troubleshooting.md)

## Safe helper

- [scripts/cognee_memory_smoke.py](scripts/cognee_memory_smoke.py) — verifies the installed API surface and prints a safe summary without calling external services.

## Working rules

- Prefer `remember` when the user wants a single “store + organize + recall later” flow.
- Prefer `add` + `cognify` + `search` when the user wants to reason about the pipeline stages separately.
- Use `session_id` only for session memory. Omit it for permanent graph memory.
- Use `dry_run=True` when the user wants a rough cost/size estimate without LLM calls.
- Use `run_in_background=True` for large or long-running jobs and explain how the returned object is awaited.
- Route any provider/database/path question to the configuration sub-skill instead of re-explaining the backend matrix here.
