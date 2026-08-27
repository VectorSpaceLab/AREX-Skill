---
name: graph-read
description: "Read and resolve Potpie Context Graph entities, views, timelines, and status."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Potpie graph read

Use this sub-skill when the task is about discovering, resolving, searching, or inspecting information already stored in Potpie's Context Graph.

## Read this when

- The user asks about `potpie resolve`, `potpie search`, `potpie graph catalog`, `potpie graph read`, `potpie graph search-entities`, `potpie graph describe`, `potpie graph neighborhood`, `potpie graph inspect`, `potpie graph export`, `potpie timeline recent`, or `potpie graph status`.
- A graph read returns empty, unsupported, or ambiguous results.
- You need to choose between root convenience commands and the graph workbench read surface.

## Do not use this for

- Writing memories, proposals, inbox, quality, or nudge operations: read `../graph-write/SKILL.md`.
- Pot/source binding before reads: read `../workspace-boundaries/SKILL.md`.
- Runtime/daemon availability: read `../runtime/SKILL.md`.
- Provider credential acquisition: read `../auth-integrations/SKILL.md`.

## Operating procedure

1. Use `resolve` for intent-driven context packages and `search` for broad memory search.
2. Use `graph catalog` to discover supported subgraphs, views, includes, and entity labels before constructing a detailed read.
3. Use `graph read` for named views and included context; use `graph search-entities` when you first need canonical entity keys.
4. Use `graph describe`, `graph neighborhood`, and `timeline recent` for entity-level explanation, graph locality, and recent events.
5. Diagnose empty results by checking scope filters, source/pot binding, include support, and daemon/backend readiness before assuming the memory is absent.

## References

- `references/workflow.md` — read command matrix, named views, includes, scopes, and identity-resolution choices.
- `references/troubleshooting.md` — unsupported includes, empty-vs-unsupported results, scope mismatch, ranking, and daemon symptoms.

## Verification notes

- Safe native candidates include graph CLI contract, graph-surface-lite contract, read orchestrator, P9 reader, envelope, ranking, timeline endpoint, graph views, and scope-match tests.
- No accelerator backend is required for read-side CLI/contract verification.
