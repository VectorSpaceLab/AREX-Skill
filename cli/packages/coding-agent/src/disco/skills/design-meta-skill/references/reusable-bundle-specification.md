# Reusable-Bundle Specification

Use this reference only after `distill-ml-knowledge` selects
`construction strategy: design-reusable` and supplies an exact routing handoff.
Read `../../distill-ml-knowledge/references/task-and-construction-contract.md`
for the canonical definitions of `z`, `Q`, `X`, `G_tilde`, `G`, `R`, and
`tau = (q, D, E, g)`. Do not use this specification to select a strategy.

## Validate The Routing Handoff

Confirm that the handoff records:

- strategy `design-reusable` and its decision revision;
- anchor kind, anchor identity, and distillation form;
- current `tau` when applicable, or future source-anchor class and intended use
  for a task-agnostic source run;
- scoped capabilities `Q`, required evidence/source behavior, and
  verification/recovery needs;
- Creator-visible capability matrix and inventory snapshot;
- the exact uncovered recurring construction gap, why extension/composition is
  inadequate, and recurrence evidence;
- construction constraints, unknowns, assumptions, and approval state.

Return exact missing fields or changed evidence to `distill-ml-knowledge`; do not
rebuild a second adequacy matrix here.

## Future Anchor Contract

Specify the parameterized Creator workflow, not the current task or checkout:

- supported source anchors and task anchors, versions, and identity rules;
- how a task-oriented `tau = (q, D, E, g)` is decomposed and how missing
  `D`, `E`, or `g` is handled;
- how a task-agnostic source is understood without inventing a task;
- access methods, trust boundaries, source discovery limits, and source
  material that is explicitly excluded.

## Scope Contract `Q`

Define how the future workflow identifies capabilities, triggers, expected
observations, non-goals, skill boundaries, graph entry points, and the strict
versus optional parts of the requested operating output.

## Ground Contract `X`

Define how the workflow selects evidence from a source anchor or discovers
permitted material for task-oriented capability gaps. Require provenance, source
revision, access/trust boundary, inclusion and exclusion reasons, conflict
resolution, inaccessible evidence, and assumption ownership.

## Construct Contract `G_tilde`

Define how the workflow performs tool encapsulation, skill packaging, or skill
generation and produces `G_tilde = (S_tilde, L_tilde)`:

- root/router and sub-skill boundaries;
- explicit routing, dependency, composition, and relative-reference links;
- progressive disclosure;
- required `SKILL.md`, `references/`, `scripts/`, and bundled resources;
- role, ownership, staging, resume, and construction-record requirements.

Every generated operating root, router, and sub-skill must declare
`metadata.disco-role: operating`. Every generated meta runtime file remains
`meta` and must not include target-specific agent manifests.

## Verify Contract And Accepted Graph `G`

Specify checks that transform the candidate into `G = (S, L)` or leave it
explicitly unverified:

| Capability or use | Representative anchor/check | Expected observation | Gate |
|---|---|---|---|
| source/task resolution | ... | ... | strict / soft |
| evidence support | ... | ... | strict / soft |
| graph structure and links | ... | ... | strict / soft |
| executable or API/CLI behavior | ... | ... | strict / soft |
| failure and recovery | ... | ... | strict / soft |
| deployment and handoff | ... | ... | strict / soft |

For task-agnostic anchors, use source-supported representative workflows, safe
executable examples/tests, API/CLI smoke checks, graph/link checks,
evidence-support checks, and failure-recovery cases. Do not require a
task-level outcome trial when no task exists. For task-oriented anchors, include
task-level trials whenever the approved `g` makes them applicable.

## Construction Environment And Record `R`

Record the future Creator environment in `R`, including tools, permissions,
source access, hardware, software, concurrency, storage, budget, prohibited
actions, stop conditions, and recovery. Keep current machine paths, credentials,
and transient task state out of the reusable bundle.

The construction record must preserve the routing/specification revisions,
retained and excluded `X`, candidate `G_tilde`, checks, failures, repairs,
accepted `G` or blocker, deployment decision, import result, and Researcher
handoff.

## Later Operating-Graph Deployment

The future workflow must assess reuse only after verification:

- project scope is the default for task-bound, private, environment-bound, or
  uncertain output;
- managed scope requires a self-contained graph, provenance, representative
  cross-project evidence, and one-scope placement;
- repo output uses its specialized nested collection and locked sibling-router
  transaction;
- exact paths, collisions, shadowing, import approval, and overwrite approval
  are shown separately;
- `researcher-handoff.md` records `z`, `Q`, `X`, accepted/unverified `G`, `R`,
  entry point, scope, paths, verification, and unresolved limits.

## Failure And Recovery Contract

Specify source/access, environment/runtime, graph/verification, and deployment
failures. For each, define the observable signal, safe recovery, artifact to
update, rerun boundary, and stop state. Never turn a required verification block
into an ordinary skip or claim acceptance without the required evidence.

## Review Template

```markdown
# Reusable-Bundle Specification

- contract kind: reusable-bundle
- routing decision revision:
- anchor kind:
- distillation form:
- anchor `z` or future anchor class:
- current task `tau`, when applicable: `tau = (q, D, E, g)`
- scoped capabilities `Q`:
- uncovered recurring construction gap:
- recurrence evidence:

## Grounded evidence `X`
- sources, revisions, provenance, access/trust boundary:
- selection, exclusions, conflicts, inaccessible items, assumptions:

## Candidate graph `G_tilde`
- root/router, nodes, links, progressive disclosure:

## Verification
| Check | Expected observation | Gate | Result |
|---|---|---|---|

## Construction record `R`
- construction environment and constraints:
- failures, repairs, recovery, and stop conditions:
- accepted graph `G` or unverified blocker:

## Later deployment
- reusability evidence:
- selected scope and exact targets:
- importer and overwrite policy:

## User decision
- status: proposed | approved | revise
- approved revision identifier:
```

Approval applies to this exact specification revision. It does not approve the
generated artifact, managed import, or any later operating graph.
