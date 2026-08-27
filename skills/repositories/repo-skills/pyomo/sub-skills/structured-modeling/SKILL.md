---
name: structured-modeling
description: "Guides Pyomo users through GDP, DAE, network, MPEC, and
  units-based structured modeling workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Structured Modeling

Use this sub-skill when the task uses one of Pyomo's structured modeling
families instead of a plain algebraic model.

## What this sub-skill covers

- GDP with `Disjunct`, `Disjunction`, and GDP transformations.
- DAE with `ContinuousSet`, `DerivativeVar`, `Integral`, and discretization.
- Network models with `Port`, `Arc`, and `SequentialDecomposition`.
- MPEC and complementarity modeling.
- Units of measure and consistency checks.

## What to route elsewhere

- Core component syntax and basic model inspection go to `modeling-basics`.
- Data-file loading for structured models goes to `data-and-io`.
- Solver, CLI, and smoke-check issues go to `solve-and-cli`.
- APPSI, PyNumero, FBBT, simplification, community detection, or viewer issues
  go to `solver-extensions`.

## Read these references

- `../../references/structured-modeling.md` for the verified workflow patterns
  and common gotchas.
- `../../references/core-modeling.md` when a structured model still needs the
  base component syntax.
- `../../references/troubleshooting.md` when a transformation or unit check
  fails.

## Typical workflow

1. Build the underlying Pyomo model with the normal component types.
2. Add the structured feature: disjunction, continuous set, port/arc, or
   complementarity relation.
3. Apply the required transformation or discretization.
4. Inspect the transformed model before solving.
5. Only then hand the model to a solver or analysis tool.

## Common request patterns

- "How do I model an either-or choice with GDP?"
- "How do I discretize a DAE model?"
- "How do I expand arcs in a network model?"
- "How do I represent a complementarity condition?"
- "How do I check units on a Pyomo expression?"

## Common failure modes

- Forgetting the transformation step before solving.
- Using a `ContinuousSet` without discretization.
- Misspelling a transformation name such as `dae.collocation` or
  `network.expand_arcs`.
- Building a GDP model but never choosing a GDP reformulation.
- Unit inconsistency, especially around offset temperature units.

## Practical guidance

- Keep the structured example tiny until the transformation path is verified.
- Use the explicit transformation name in the example so the routing is clear.
- For DAE, always show the discretization call next to the model.
- For network models, show arc expansion before any sequential decomposition.
- For units, show the unit check alongside the expression being validated.

## Examples of what belongs here

- A GDP model with two disjuncts and a single disjunction.
- A DAE model discretized with finite difference or collocation.
- A flow network with ports, arcs, and an arc-expansion transform.
- A complementarity relation or units-consistency check.

## Examples of what does not belong here

- General solver configuration or CLI usage.
- Plain set/var/constraint syntax.
- Optional extension troubleshooting that is not tied to the structured model
  family itself.

## Related routes

- Move to `modeling-basics` when you only need the base components.
- Move to `solver-extensions` when the structured model depends on optional
  backends or advanced solver helpers.
