# Path Selection And Adequacy

Use this reference after normalizing the routing inputs and before reading any
branch-specific construction reference. Assess only Creator-visible meta-skill
contracts; never inspect Researcher-only skills or hidden paths to improve the
inventory.

## Contents

- [Derive Required Construction Capabilities](#derive-required-construction-capabilities)
- [Inventory Existing Contracts](#inventory-existing-contracts)
- [Select Exactly One Path](#select-exactly-one-path)
- [Apply Path Preference](#apply-path-preference)

## Derive Required Construction Capabilities

Derive only capabilities required by the current task in these dimensions:

1. Source-anchor resolution, access, versioning, and trust.
2. Evidence selection, exclusion, provenance, conflict handling, and
   uncertainty.
3. Operating-skill boundaries, routing, dependency/composition links, and
   progressive disclosure.
4. Runtime resources, scripts, environments, permissions, and failure recovery.
5. Static, executable, task-level, and soft verification.
6. Construction records, operating-output reusability assessment, deployment,
   user review, locked import, and Researcher handoff.

Express requirements as observable contracts rather than topic labels.

## Inventory Existing Contracts

For each plausible visible meta skill, read its description and full `SKILL.md`
before claiming coverage. Record inputs, supported anchors, outputs,
verification, environment rules, recovery, deployment, handoff, and exclusions.
Do not infer capability from a skill name alone.

Treat an existing workflow as adequate only when its documented contract covers
all required strict capabilities. A workflow may retain its specialized scope
and importer. For example, an adequate repo workflow must keep its nested
`repo-skills/` deployment and locked sibling-router rebuild.

Use this matrix:

```markdown
| Required capability | Task evidence | Candidate meta skill | Coverage | Contract evidence | Gap/constraint |
|---|---|---|---|---|---|
| ... | ... | ... | full / partial / none | ... | ... |

Existing-workflow result: single | compose | inadequate
Selected contracts and order:
Artifact ownership and handoffs:
Uncovered contract:
```

## Select Exactly One Path

### `reuse-existing`

Select `reuse-existing` when existing visible contracts adequately cover the
request:

- Use `reuse mode: single` for the narrowest adequate bundle.
- Use `reuse mode: compose` when a bounded ordered composition covers all
  requirements and its shared state, artifact ownership, verification
  responsibility, recovery, and handoff boundaries can be stated without
  silently changing any selected contract.

A different library, domain, or desired downstream task does not by itself
justify a new meta skill.

### `direct`

Select `direct` when no adequate existing workflow or composition exists and a
concrete source anchor can produce the required task-conditioned operating graph
now. Use this for one-off or task-bound construction needs and when evidence for
recurring reusable construction is absent.

### `design-reusable`

Select `design-reusable` only when no adequate existing workflow or composition
exists and evidence shows that the missing construction capability will recur
across future source anchors. Identify the unsupported contract, why bounded
adaptation/composition is insufficient, and the recurrence evidence. A prose
preference, one task-specific prompt, or speculative future value is not enough.

## Apply Path Preference

- For `auto`, prefer `reuse-existing`; otherwise choose `direct` for a
  task-conditioned need or `design-reusable` for an evidence-backed recurring
  construction gap.
- For `direct`, surface a conflict if source access, verification, permissions,
  or the construction environment cannot support a direct run.
- For `reusable`, try `reuse-existing` first. Select `design-reusable` only for
  a verified recurring gap. If the remaining need is one-off, surface the
  preference conflict and ask for revision rather than silently using `direct`.

Before selecting `design-reusable`, challenge the decision:

- Can an existing meta skill accept the anchor through documented extension
  points?
- Can a bounded composition cover the request?
- Is the alleged gap an operating-graph gap rather than a construction-workflow
  gap?
- Is recurrence supported by more than the current source instance?
- Is there evidence that existing workflows cannot meet required verification
  or recovery?

Record the selected path, matrix evidence, rationale, and decision revision in
the canonical routing record. For `design-reusable`, include all of them in the
handoff; the downstream skill validates that handoff but does not repeat path
selection.
