---
name: workflows-queues
description: "Work with InvokeAI workflow library records, default workflow JSON
  assets, session queue items, batch payloads, queue privacy redaction, and
  workflow/queue API behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Workflows Queues

Use this sub-skill when the task involves InvokeAI workflow JSON/library records, default workflow assets, queue items, batch enqueue payloads, workflow thumbnails, public/private workflow behavior, or multiuser queue redaction.

## Read First

- `references/workflow-records.md` for workflow DTOs, library storage, CRUD, thumbnails, tags, categories, `opened_at`, and public/private access rules.
- `references/session-queue-and-batches.md` for `Batch`, `BatchDatum`, `NodeFieldValue`, `SessionQueueItem`, status lifecycle, `GraphExecutionState` serialization, retry/cancel/clear behavior, and redaction.
- `references/default-workflows.md` for bundled default workflow JSON shape, startup sync rules, and safe default-workflow inspection.
- `references/troubleshooting.md` for common workflow/queue failures and exact diagnosis paths.

## Route Elsewhere

- Use sibling `workflow-nodes` for custom node implementation, invocation schemas, graph construction, and node field semantics beyond queue payload validation.
- Use sibling `model-management` for model identifiers, model nodes, and compatibility warnings in default workflows.
- Use sibling `operations-config` for auth setup, multiuser configuration, admin roles, and deployment-level queue settings.

## Bundled Helpers

- `scripts/inspect_default_workflow.py <workflow.json>` checks default workflow JSON shape, node/edge/exposed-field references, category, tags, and summary metadata without importing InvokeAI.
- `scripts/validate_batch_payload.py <payload.json>` checks queue enqueue batch structure, zipped batch lengths, homogeneous item types, duplicate node/field mappings, node presence, and obvious field mismatches.

Keep workflow JSON and queue records conceptually separate: workflow files are frontend/library records, while queued `session` data is serialized execution state derived from an invocation graph.