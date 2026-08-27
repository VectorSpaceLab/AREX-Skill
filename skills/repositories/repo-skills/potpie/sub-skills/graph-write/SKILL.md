---
name: graph-write
description: "Write, propose, commit, repair, and nudge Potpie Context Graph
  records safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Potpie graph write

Use this sub-skill when the task is about adding durable memory, proposing graph mutations, committing plans, handling inbox items, running graph quality checks, or nudging agents from graph evidence.

## Read this when

- The user asks about `potpie record`, `potpie graph propose`, `potpie graph commit`, `potpie graph mutate`, `potpie graph mutation-template`, `potpie graph bulk apply`, `potpie graph import`, `potpie graph repair`, `potpie graph history`, `potpie graph inbox`, `potpie graph quality`, or `potpie graph nudge`.
- A write fails because a mutation payload is malformed, a plan needs review, a plan expired, or verification did not pass.
- You need to distinguish the canonical propose/commit flow from the legacy `graph mutate` wrapper.

## Do not use this for

- Discovery-only reads: read `../graph-read/SKILL.md`.
- Pot/source setup or default binding: read `../workspace-boundaries/SKILL.md`.
- Runtime/daemon startup: read `../runtime/SKILL.md`.
- Credential acquisition: read `../auth-integrations/SKILL.md`.

## Operating procedure

1. Prefer the canonical plan door: `graph propose` to validate and stage, then `graph commit` with explicit approval and verification as needed.
2. Use `graph mutation-template` before authoring payloads when the DSL or entity label is uncertain.
3. Keep mutations flat and retrieval-grade: durable descriptions, explicit scopes, source references, and no nested legacy wrappers unless the CLI specifically emits them.
4. Use `graph inbox`, `graph quality`, `graph history`, and `graph inspect` to review pending, stale, or questionable graph state before applying more writes.
5. Treat `record` as a convenient durable-memory write path and `graph nudge` as a bridge from graph evidence to agent guidance.

## References

- `references/workflow.md` — write command matrix, flat mutation DSL, approval/verification, inbox, quality, bulk, and nudge flows.
- `references/troubleshooting.md` — malformed payloads, review gates, expired plans, bulk failures, inbox states, and quality repairs.

## Verification notes

- Safe native candidates include graph CLI contract, graph workbench plan/inbox/quality tests, nudge service, apply-once, semantic mutation validation, semantic mutations, graph-plan compatibility, and graph-workbench ontology tests.
- No accelerator backend is required for write-side CLI/contract verification.
