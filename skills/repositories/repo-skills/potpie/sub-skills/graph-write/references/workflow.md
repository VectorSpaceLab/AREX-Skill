# Graph write workflow reference

Potpie's safer write path is plan-based: validate a mutation with `graph propose`, then apply it with `graph commit` after approval and verification checks. Use direct or legacy wrappers only when their behavior is explicit.

## Command matrix

| Goal | Command | Notes |
| --- | --- | --- |
| Add a durable record | `potpie record ...` | Convenient memory-write path for durable agent context. |
| Inspect mutation schema | `potpie graph mutation-template ...` | Use before authoring a payload by hand. |
| Validate/stage a plan | `potpie graph propose ...` | Canonical entry for graph mutations. |
| Apply a plan | `potpie graph commit <plan-id>` | Use approval and `--verify` style checks when available. |
| Legacy direct wrapper | `potpie graph mutate ...` | Preserve compatibility; prefer propose/commit for safety. |
| Bulk mutations | `potpie graph bulk apply ...` | Use for batches; track chunk-level errors. |
| Import graph data | `potpie graph import <file>` | Mutating/admin path; confirm file source and backup/export before applying. |
| Repair graph state | `potpie graph repair ...` | Use after quality/history evidence and explicit approval for repair scope. |
| Inspect history | `potpie graph history ...` | Review applied/failed changes before more writes. |
| Manage inbox | `potpie graph inbox ...` | Review queued/pending work items. |
| Run quality checks | `potpie graph quality ...` | Detect stale, duplicate, weak, or repairable graph state. |
| Nudge from evidence | `potpie graph nudge ...` | Generate/route agent guidance from graph state. |

## Safe propose/commit flow

1. Read first when identity matters: use `graph-read` to resolve canonical entity keys.
2. Generate a template: `potpie graph mutation-template <entity-or-kind>`.
3. Author a flat mutation payload with durable descriptions, explicit scope, source references, and verification metadata where supported.
4. Run `potpie graph propose <payload>` and inspect warnings, required approvals, conflicts, and plan expiration.
5. If the plan is risky or review-required, obtain explicit approval before commit.
6. Run `potpie graph commit <plan-id>` with verification options when available.
7. Confirm with `graph history`, `graph describe`, or a follow-up read.

## Mutation payload expectations

- Prefer flat records and explicit fields over nested legacy wrappers.
- Use retrieval-grade descriptions: state what future agents should learn, why it matters, and the scope where it applies.
- Include source/evidence keys when a write is derived from repo, issue, PR, or chat evidence.
- Keep scopes precise. Over-broad memory pollutes later reads; over-narrow memory is hard to discover.
- Do not bypass validation by writing directly to a backend store.

## Inbox and quality loops

Use inbox and quality commands when graph state is uncertain:

```bash
potpie graph inbox list
potpie graph quality report
potpie graph history --limit 20
```

Then decide whether to approve, repair, archive, or write a new mutation. Avoid stacking new writes on top of unresolved quality errors.

## Admin import and repair

Treat `graph import` and `graph repair` as mutating/admin operations. Confirm the input file or repair scope, preserve an export/backup when practical, and avoid broad repairs without explicit user approval.

## Bulk writes

Bulk apply is useful for structured batches, but failures should be handled per item/chunk:

- capture the batch input path and command flags,
- record which chunks applied and which failed,
- do not assume idempotency unless the output confirms it,
- confirm final state with history and read-side checks.

## Nudge workflow

`graph nudge` connects graph findings to agent-facing guidance. Use it when a user asks to prompt, remind, or steer an agent from existing Potpie context. If graph evidence is missing, route to `graph-read` first or create data through `record`/`propose` only with user-approved evidence.
