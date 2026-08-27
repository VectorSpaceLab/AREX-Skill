---
name: core-memory-api
description: "Use M-flow public Python APIs and mflow CLI for core memory
  workflows, data management, manual ingestion, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core Memory API

Use this sub-skill when a task needs the public `m_flow` Python package or the
`mflow` CLI for core memory operations: add data, memorize it into graph memory,
query/search it, run one-step ingest, manage datasets/data, update/delete/prune,
manual graph insertion, or process-local configuration.

## Route first

- Core `add -> memorize -> query/search` workflows: read
  [references/workflows.md](references/workflows.md).
- Exact Python signatures, return shapes, exported names, and data-management
  APIs: read [references/api-reference.md](references/api-reference.md).
- CLI commands and flags: read [references/cli-reference.md](references/cli-reference.md).
- Errors, credentials, invalid kwargs, empty results, or destructive-operation
  cautions: read [references/troubleshooting.md](references/troubleshooting.md).
- Loader internals, content routing, chunking, custom `Stage` pipelines, and
  `preferred_loaders` details belong in
  [../ingestion-pipelines/SKILL.md](../ingestion-pipelines/SKILL.md).
- Retrieval scoring, `RecallMode` tuning, episodic display controls, Cypher, and
  storage/backend tuning belong in
  [../retrieval-graph-search/SKILL.md](../retrieval-graph-search/SKILL.md).
- FastAPI, MCP, UI, Docker, auth service deployment, and server lifecycle belong
  in [../service-integrations/SKILL.md](../service-integrations/SKILL.md).

## Operating model

M-flow's in-process API is asynchronous. Treat `add()` as raw data registration,
`memorize()` as memory-graph construction, and `query()`/`search()` as retrieval
over already memorized data. `ingest()` is the convenience API that performs
`add()` then `memorize()` and returns an `IngestResult` status object.

Prefer stable dataset names such as `project_notes_2026q1`; pass the same name
to add/ingest, memorize, and query. Use `created_at` when importing historical
content so later retrieval can preserve temporal intent. Use `run_in_background`
only when the caller can poll or otherwise wait before querying. Never call
`delete`, `update`, `datasets.delete_dataset`, or `prune` without an explicit
scope and confirmation from the user.

## Safe bundled checker

Run the bundled smoke checker in dry-run mode before live examples:

```bash
python scripts/core_workflow_smoke.py --help
python scripts/core_workflow_smoke.py
```

It only imports `m_flow`, checks public exports/config visibility, reports
whether an LLM credential appears configured, and prints a guarded plan. Live DB
writes require an explicit flag:

```bash
python scripts/core_workflow_smoke.py --run-live --dataset-name skill_smoke_core
```

Live mode calls `add()`, `memorize()`, and `query()` and may create local graph,
vector, relational, and file-storage data for the selected dataset.
