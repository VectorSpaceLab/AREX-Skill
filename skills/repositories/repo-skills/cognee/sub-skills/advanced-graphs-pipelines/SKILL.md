---
name: "advanced-graphs-pipelines"
description: "Guides Cognee custom graph schemas, ontologies, custom pipelines,
  memify, migration, export, and visualization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cognee Advanced Graphs and Pipelines

Use this sub-skill when the user is beyond the default memory flow and wants to shape graph extraction, run custom tasks, enrich a graph, migrate memory, export graph data, or visualize the result.

## Route here for

- Custom `DataPoint` models and graph extraction schemas.
- `Dedup`, `Embeddable`, and `LLMContext` field annotations.
- Custom `Task` / `@task` / `run_custom_pipeline(...)` workflows.
- `cognify(..., graph_model=..., custom_prompt=..., temporal_cognify=...)`.
- `memify(...)`, ontology resolver configuration, migration sources, export, and visualization APIs.
- Troubleshooting model identity, invalid schemas, custom-task failures, and visualization/export issues.

## Route away

- Basic memory storage/query flows: [core-memory](../core-memory/SKILL.md).
- Search-mode selection: [search-retrieval](../search-retrieval/SKILL.md).
- Provider/database configuration: [configuration-backends](../configuration-backends/SKILL.md).
- Session/agent memory and feedback: [agent-session-memory](../agent-session-memory/SKILL.md).
- CLI/API/MCP service startup: [api-cli-services](../api-cli-services/SKILL.md).

## Read first

1. [references/custom-graphs-pipelines.md](references/custom-graphs-pipelines.md)
2. [references/migration-visualization.md](references/migration-visualization.md)
3. [references/troubleshooting.md](references/troubleshooting.md)

## Safe helper

- [scripts/inspect_custom_model.py](scripts/inspect_custom_model.py) — imports a custom model and prints Pydantic fields/metadata without running a pipeline.

## Working rules

- Import `DataPoint` from `cognee.infrastructure.engine`, not from internal module paths.
- Use identity fields for domain objects that must deduplicate across runs.
- Keep custom pipeline tasks small, async-safe, and explicit about whether they call LLM/embedding providers.
- Use `skip_connection_test=True` only when the custom pipeline truly performs no LLM or embedding work.
- Treat migration/export/visualization as graph operations that require an already initialized dataset and backend.
