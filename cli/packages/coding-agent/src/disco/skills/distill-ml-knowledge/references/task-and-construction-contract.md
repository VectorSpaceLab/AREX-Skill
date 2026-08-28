# Distillation Contract

Read this reference before routing or branch-specific construction. It owns
the paper-aligned vocabulary shared by `distill-ml-knowledge`,
`design-meta-skill`, and the specialized Creator workflows. It does not define
a second construction shorthand. Engineering details belong in the
construction record `R` using their full descriptive names.

## Canonical Objects

The canonical distillation record is:

```markdown
- anchor `z`:
- distillation form: task-agnostic | task-oriented
- scoped capabilities `Q`:
- grounded evidence `X`:
- candidate graph `G_tilde`:
- accepted graph `G`:
- construction record `R`:
```

- `z` is either a source anchor or a task anchor. A source anchor identifies
  material such as a repository, paper, tutorial, dataset, or benchmark. A task
  anchor identifies the problem from which source discovery may begin.
- `Q` is the capability scope: what the graph should enable, its triggers,
  boundaries, non-goals, and required observations.
- `X` is retained evidence with source identity, revision, provenance, access and
  trust boundaries, exclusions, conflicts, and assumptions.
- `G_tilde` is the candidate graph. Write it as
  `G_tilde = (S_tilde, L_tilde)`, where nodes are candidate root/sub-skills and
  links are explicit routing, dependency, composition, or reference links.
- `G` is the accepted verified graph, written as `G = (S, L)`.
- `R` is the construction record for decisions and execution evidence. It
  includes the routing and specification revisions, evidence plan, construction
  details, verification and repairs, deployment decision, import result, and
  stop reason. Keep `R` outside live runtime skill roots.

## Task Anchor

Only task-oriented distillation uses the task tuple:

```text
tau = (q, D, E, g)
```

- `q`: task or problem description.
- `D`: task-provided data or material.
- `E`: downstream environment in which Researcher will execute, including
  available tools and limits.
- `g`: desired outcome or acceptance goal.

Do not create a task tuple for a task-agnostic source run merely to fill a
template. If a task-oriented run lacks a value that can change source discovery,
scope, verification, or acceptance, stop at the clarification gate.

## Construction Record `R`

Record implementation details by stage rather than by another symbolic model:

- **Anchor provenance:** source identity, revision, access method, and trust
  boundary.
- **Scope decisions:** capability set `Q`, triggers, non-goals, skill boundaries,
  graph entry points, and expected observations.
- **Grounding decisions:** evidence set `X`, source discovery range, selected and
  excluded material, provenance, conflicts, inaccessible content, and
  assumptions.
- **Construction details:** chosen construction strategy, graph links,
  resources, scripts, ownership, Creator workspace, tools, permissions, budget,
  staging, resume, and recovery.
- **Verification results:** static and source-support checks, executable or
  representative-use checks, task-level trials when applicable, failure cases,
  repairs, strict or soft gates, and unverified points.
- **Deployment and handoff:** project/managed scope, one-scope invariant, exact
  targets, import approval, overwrite state, accepted `G`, and Researcher
  handoff.

Distinguish `E` from the Creator workspace and tools recorded in `R`.
Distinguish the task goal `g` from verification observations recorded in `R`.

## Anchor Classification And Stage Rules

### Task-agnostic source anchor

Use source understanding and capability identification to scope `Q`, then
extract and select evidence `X` from the source anchor. Construct and verify
source-supported operating uses. Verification should include safe executable
examples or tests, API/CLI smoke checks, graph/link checks, evidence-support
checks, and failure-recovery cases when available. Do not require a
task-level outcome trial without a downstream task.

### Task-oriented task anchor

Use `tau` for task decomposition and capability gap analysis. In the grounding
stage, perform only the approved source discovery needed to cover the gaps, then
select evidence `X`. Approve the scope/preflight, source-discovery range,
budget, and verification targets before discovery; approve the grounded
evidence plan or exact construction specification before material construction.
Import and overwrite approval remain separate.

## Clarification Gate

Resolve permitted read-only facts directly. A missing value is blocking when an
assumption could change the anchor classification, `Q`, source identity/access
or trust, source-discovery scope, permissions, credentials, hardware, budget,
verification gate, recurrence evidence for `design-reusable`, or live
destination/overwrite decision. Ask for all blocking information or decisions
together before the affected action.

Other unknowns may remain only as explicit, reversible assumptions with an
owner and validation plan. Approval of a record containing a blocking unknown
does not resolve that unknown.

## Routing Record

Create this lightweight record before branch-specific material construction:

```markdown
# Routing Record

- anchor kind: source | task
- distillation form: task-agnostic | task-oriented
- anchor `z`:
- task `tau`, when applicable: `tau = (q, D, E, g)`
- scoped capabilities `Q`:
- grounded evidence requirements `X`:
- required verification and recovery:
- construction strategy: direct | reuse-existing | design-reusable
- reuse mode: single | compose | not-applicable
- selected visible contracts:
- uncovered recurring construction gap:
- recurrence evidence:
- construction constraints and approval state:
- unknowns and assumptions:
- decision revision:
```

The routing record is an engineering artifact in `R`; it does not replace the
paper's two distillation forms. `design-meta-skill` consumes a complete
`design-reusable` handoff and must not independently select another strategy.

## Preference Mapping And Change Control

- `auto`: prefer an adequate existing workflow; otherwise use `direct` for a
  concrete task-conditioned need or `design-reusable` for an evidence-backed
  recurring construction gap.
- `direct`: require a feasible source, evidence, verification, permission, and
  Creator construction environment; surface conflicts instead of guessing.
- `reusable`: try `reuse-existing` first; use `design-reusable` only when
  recurrence is evidenced. Do not silently convert a one-off request to a direct
  run.

Approval applies to the exact revision. Revisit the affected record when the
anchor, source access, scope, evidence plan, permissions, budget, graph scope,
verification, or deployment target changes materially.
