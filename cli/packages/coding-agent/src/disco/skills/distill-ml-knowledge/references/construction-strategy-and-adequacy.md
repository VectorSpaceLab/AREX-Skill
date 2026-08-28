# Construction Strategy Selection And Adequacy

Read this reference after identifying the anchor and scoping `Q`, and before
branch-specific construction. It defines Creator orchestration strategy. It
does not replace the paper's task-agnostic and task-oriented distillation forms
and it does not introduce a second symbolic contract.

## Derive Required Capabilities

Describe requirements as observable contracts for the current anchor:

1. Source-anchor or task-anchor resolution, versioning, access, and trust.
2. Evidence selection, exclusion, provenance, conflict handling, and
   uncertainty.
3. Operating-skill boundaries, routing, graph links, and progressive
   disclosure.
4. Runtime resources, scripts, environments, permissions, budget, and recovery.
5. Static, executable, representative-use, task-level when applicable, and
   failure-recovery verification.
6. Construction records, deployment scope, review, locked import, and Researcher
   handoff.

For a source anchor, do not require a downstream task solely to make the
requirements look task-oriented. For a task anchor, use the complete
`tau = (q, D, E, g)` before deciding whether source discovery or verification
can proceed.

## Inventory Visible Creator Contracts

Inspect only Creator-visible meta skills. For each plausible workflow, record
its supported anchor classes, scope, evidence behavior, graph output,
verification, environment, recovery, deployment, importer, handoff, and
exclusions. Do not infer coverage from a skill name.

Use this matrix in `R` or its review artifact:

```markdown
| Required capability | Anchor/task evidence | Candidate meta skill | Coverage | Contract evidence | Gap/constraint |
|---|---|---|---|---|---|
| ... | ... | ... | full / partial / none | ... | ... |
```

An existing workflow is adequate only when it covers every strict requirement.
Keep specialized deployment and import contracts intact; a repository workflow
must retain its nested `repo-skills/` installation and locked sibling-router
rebuild.

## Select One Construction Strategy

### `reuse-existing`

Use `reuse-existing` when one visible workflow covers the request, or when a
bounded ordered composition covers it without silently changing any selected
contract. Use `reuse mode: single` for one bundle and `reuse mode: compose` for
a composition with explicit artifact ownership, verification responsibility,
recovery, and handoff boundaries.

### `direct`

Use `direct` when no existing workflow or bounded composition is adequate, a
concrete anchor is available, and the current run can produce and verify the
operating graph. This can serve either distillation form.

### `design-reusable`

Use `design-reusable` only when no existing workflow or bounded composition is
adequate and the missing construction capability is evidenced to recur across
future anchors. Pass the verified recurring gap to `design-meta-skill`; the
result is a future Creator workflow, not the current Researcher operating graph.

Before selecting it, check whether an existing workflow can accept the anchor
through a documented extension point, whether a bounded composition is enough,
whether the gap is really a construction-workflow gap, and whether recurrence
evidence exists beyond the current request.

## Approval And Ordering

For task-oriented distillation, source material may be unknown at the start.
Obtain approval of the scope/preflight, task, capability gaps, permitted source
discovery range, budget, and verification targets before discovery. After
grounding produces `X`, obtain approval of the evidence plan or exact
construction specification before material construction. Import and overwrite
approval remain separate.

For task-agnostic source distillation, approve the scope and source/evidence
boundary before construction. Use representative operating workflows, safe
executable checks, and source-support evidence when there is no downstream task
against which to run a task-level outcome trial.

Record the layered decision in `R`:

```markdown
- anchor kind: source | task
- distillation form: task-agnostic | task-oriented
- anchor `z`:
- scoped capabilities `Q`:
- construction strategy: direct | reuse-existing | design-reusable
- reuse mode: single | compose | not-applicable
- selected visible contracts:
- uncovered recurring construction gap:
- recurrence evidence:
- rationale:
- decision revision:
```

Revisit the decision if the anchor, source access, permissions, budget,
capability scope, evidence, verification, graph scope, or destination changes
materially. Do not silently select a different strategy.
