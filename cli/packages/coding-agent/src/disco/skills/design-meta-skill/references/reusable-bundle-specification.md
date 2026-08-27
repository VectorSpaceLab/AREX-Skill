# Reusable-Bundle Specification

Use this reference only after `distill-ml-knowledge` has selected
`design-reusable` and supplied an exact routing handoff. Read
`../../distill-ml-knowledge/references/task-and-construction-contract.md` for the
canonical definitions of `tau`, the five construction fields, `G = (S, L)`, and
`R`. Do not redefine them here or use this specification to select a path.

## Contents

- [Validate The Routing Handoff](#validate-the-routing-handoff)
- [Separate The Two Contract Levels](#separate-the-two-contract-levels)
- [Review Template](#review-template)
- [Approval Boundaries](#approval-boundaries)

## Validate The Routing Handoff

Confirm that the handoff records:

- `selected path: design-reusable` and its decision revision.
- Normalized task, source requirements, required operating capabilities,
  verification/recovery needs, and construction constraints.
- Creator-visible capability matrix, selected inventory snapshot, and the exact
  uncovered construction contract.
- Why extension or bounded composition of existing workflows is inadequate.
- Recurrence evidence across future source anchors.
- Unknowns, assumptions, and approval state.

Return the exact missing fields or blocking unknowns to `distill-ml-knowledge`
when the handoff is incomplete, or return the changed evidence when a material
inventory/requirement change invalidates the decision. Stop this branch until a
revised handoff resolves them; do not rebuild a second adequacy matrix here.

## Separate The Two Contract Levels

The incoming routing record describes the current downstream task and why a new
construction capability is needed. The reusable-bundle specification describes
a parameterized Creator workflow that future callers will invoke with different
anchors. Do not hardcode the current task or copy the routing record into the
runtime bundle.

Specialize the canonical five fields at the reusable-bundle level:

- Source contract (`s`): supported future anchor kinds, identifiers, versions,
  access methods, trust boundaries, and evidence selection/exclusion behavior.
- Operating use (`u`): operating capabilities and graph contract the bundle must
  construct for a caller, including triggers and non-goals.
- Skill verification (`v`): checks that prove the meta workflow can resolve
  representative anchors, construct and validate graphs, and recover from
  expected failures.
- Construction environment (`e`): resources, permissions, tools, hardware,
  software, concurrency, budgets, and prohibited actions needed by future
  Creator runs.
- Graph structure (`sigma`): parameterized output boundaries, root/router
  behavior, links, progressive disclosure, bundled resources, and handoff
  ownership.

## Review Template

```markdown
# Reusable-Bundle Specification

- contract kind: reusable-bundle
- routing decision revision:
- uncovered recurring contract:
- recurrence evidence:

## Parameterized source contract (`s`)
- accepted future anchors and versions:
- access and trust boundaries:
- evidence selection, exclusion, and conflict rules:

## Generated operating use (`u`)
- required output capabilities and triggers:
- expected observations:
- non-goals:

## Bundle verification (`v`)
| Capability | Representative anchor/check | Expected observation | Gate |
|---|---|---|---|

## Future construction environment (`e`)
- verified and requested resources:
- permissions and prohibited actions:
- budget, recovery, and stop conditions:

## Generated graph structure (`sigma`)
- root/router and skill boundaries:
- links and progressive disclosure:
- required references/scripts and ownership:

## Failure and recovery contract
- source/access failures:
- environment/runtime failures:
- graph/verification failures:
- resumability and construction records:

## Later operating-graph deployment
- reusability evidence to collect after graph verification:
- project-scope conditions and trust requirement:
- managed-scope evidence threshold:
- default when uncertain: project
- specialized importer, if any:
- exact-path review, auto-import, and overwrite policy:

## Unknowns and assumptions
| Item | Status | Owner | Resolution |
|---|---|---|---|

## User decision
- status: proposed | approved | revise
- approved revision identifier:
```

## Approval Boundaries

Approval applies to the exact reusable-bundle specification revision. Return to
review if source access, permission, cost, bundle scope, parameterization,
recovery, or verification changes materially.

Specification approval does not approve the generated meta-skill artifact, its
managed import, or any operating graph produced by a later invocation. The
artifact receives a separate final review; every later operating graph receives
its own post-verification scope and destination decision. Overwrite always
requires separate approval.
