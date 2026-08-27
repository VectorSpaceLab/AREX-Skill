# Task And Construction Contract

Read this reference before path selection. It owns the vocabulary shared by
`direct`, `reuse-existing`, and `design-reusable`; branch-specific references
must extend this contract rather than redefine it.

## Contents

- [Canonical Task](#canonical-task)
- [Construction Fields](#construction-fields)
- [Clarification Gate](#clarification-gate)
- [Artifact Model](#artifact-model)
- [Routing Before Specification](#routing-before-specification)
- [Preference Mapping And Change Control](#preference-mapping-and-change-control)

## Canonical Task

Record the downstream ML research task as `tau = (x, E, B, J)`:

- `x` (`task`): research problem and expected deliverable.
- `E` (`downstream environment`): resources and runtime in which Researcher
  will later execute the task.
- `B` (`constraints`): time, token, compute, cost, data, safety, permission, and
  stop conditions.
- `J` (`task evaluation`): evaluator, acceptance observations, metrics, or
  review procedure for the downstream result.

Unknown fields remain `unknown`. Record assumptions separately with an owner
and a validation plan.

## Construction Fields

Use the five construction fields only as shorthand after their plain-language
names are established:

- `s` (`source contract`): source kinds, identifiers, versions, access methods,
  trust boundaries, and evidence-selection constraints.
- `u` (`operating use`): capabilities the resulting operating graph must
  support, trigger conditions, expected observations, and non-goals.
- `v` (`skill verification`): checks, fixtures or trials, expected results, and
  strict or soft gates used before the graph is accepted.
- `e` (`construction environment`): Creator workspace, tools, source access,
  network, credentials, permissions, hardware, software environments,
  concurrency, storage, and construction budget.
- `sigma` (`graph structure`): skill boundaries, root/router behavior, links,
  canonical ids, references/scripts, ownership, and progressive disclosure.

Keep these distinctions explicit:

| Downstream task field | Construction field | Difference |
| --- | --- | --- |
| `x` task/deliverable | `u` operating use | What the user ultimately needs versus what the graph must teach Researcher to do. |
| `E` downstream environment | `e` construction environment | Where Researcher will execute versus where Creator builds and verifies. |
| `J` task evaluation | `v` skill verification | How the final research result is judged versus how the generated graph is validated before import. |

## Clarification Gate

First resolve facts through permitted read-only inspection when reasonable. An
unknown is blocking when assuming it could change the selected path or exact
branch specification, task/deliverable/acceptance, source identity/access/trust,
required permissions/credentials/hardware/budget, a strict verification gate,
recurrence evidence for `design-reusable`, or a live destination/overwrite
decision.

Before the affected decision or action, stop, list only the blocking information
or decisions, and ask for them together. Do not treat approval of a record that
still contains a blocking unknown as resolution. Other unknowns may remain as
`assumption-safe` only when they are safe and reversible, do not materially
affect those decisions, and have an owner and validation plan.

## Artifact Model

Represent an operating graph as `G = (S, L)`:

- `S`: root and sub-skill nodes.
- `L`: explicit routing, dependency, composition, and relative-reference links.

Use `R` for the construction record containing the task/specification revision,
evidence plan, candidate graph, verification and repair evidence, deployment
review, and stop reason. `R` and other review artifacts stay outside live skill
roots.

## Routing Before Specification

Create a lightweight routing record before writing a branch-specific exact
specification:

```markdown
# Routing Record

- task `tau`:
- source requirements:
- required operating capabilities:
- required verification and recovery:
- construction constraints:
- path preference: auto | direct | reusable
- selected path: direct | reuse-existing | design-reusable
- reuse mode: single | compose | not-applicable
- selected visible contracts:
- uncovered contract:
- recurrence evidence:
- rationale:
- unknowns and assumptions:
- decision revision:
```

Then specialize the contract exactly once:

- `direct`: approve an `operating-run` specification for the current anchor and
  task before material construction.
- `reuse-existing`: pass the routing record to the selected existing workflow;
  that workflow owns its exact branch specification and normal importer.
- `design-reusable`: pass the routing record and verified recurring gap to
  `design-meta-skill`, which owns a separate `reusable-bundle` specification for
  a parameterized future construction workflow.

## Preference Mapping And Change Control

- `auto`: select the smallest adequate existing workflow or composition; use
  `direct` for a task-conditioned need; use `design-reusable` for a verified
  recurring construction gap.
- `direct`: select `direct` only when the source, verification, permissions, and
  construction environment allow it; otherwise report the conflict.
- `reusable`: select `reuse-existing` when possible, otherwise
  `design-reusable` only for a verified recurring gap. Do not silently fall back
  to `direct`.

Approval applies to an exact revision. Revisit the affected routing or branch
specification when source access, permissions, budget, evidence requirements,
graph scope, or verification changes materially. Import destination approval
and overwrite approval remain separate decisions.
