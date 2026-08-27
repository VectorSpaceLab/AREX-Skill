---
name: modeling-basics
description: "Guides Pyomo users through core model construction, component
  inspection, and tiny concrete-model smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modeling Basics

Use this sub-skill when the task is about building or reading a Pyomo model from
scratch with the core modeling objects rather than a data file, a CLI command,
or a structured extension.

## What this sub-skill covers

- `ConcreteModel` and the basic declaration pattern.
- `Set`, `RangeSet`, `Param`, `Var`, `Constraint`, `Objective`, `Block`,
  `Expression`, and `Suffix`.
- `value()`, `pprint()`, `display()`, and component traversal.
- Tiny self-contained model checks that prove the base package is usable.

## What to route elsewhere

- File-backed loading or `AbstractModel` workflows go to `data-and-io`.
- `pyomo solve`, `pyomo convert`, and solver selection go to `solve-and-cli`.
- GDP, DAE, network, MPEC, and units go to `structured-modeling`.
- APPSI, PyNumero, FBBT, simplification, community detection, or the model
  viewer go to `solver-extensions`.

## Read these references

- `../../references/core-modeling.md` for the verified core component patterns.
- `../../references/troubleshooting.md` for install/import or basic modeling
  failures.

## Use these helpers

- `../../scripts/check_import.py` for a fast import and metadata sanity check.
- `../../scripts/solve_tiny_milp.py` when you want a safe solver-backed smoke
  check for a tiny binary model.

## Typical workflow

1. Import `pyomo.environ`.
2. Create a `ConcreteModel`.
3. Declare sets, parameters, variables, constraints, and objectives.
4. Assign values or bounds where needed.
5. Inspect the model with `pprint()` or `display()`.
6. If the task asks for an execution check, run the tiny solver smoke.

## Common request patterns

- "How do I define a binary decision variable?"
- "Why is my constraint body or objective expression not evaluating?"
- "How do I traverse all active variables or constraints?"
- "How do I attach a suffix to a model?"
- "Can you show a tiny Pyomo model that solves?"

## Common failure modes

- Domain or bound mismatches during value assignment.
- Expressions that use values before the model is fully constructed.
- Misunderstanding `ConcreteModel` versus `AbstractModel`.
- Solver checks that fail because the solver is not installed yet.

## Practical guidance

- Keep examples tiny and self-contained.
- Prefer the simplest component that expresses the intent.
- Use `ConcreteModel` for immediate construction and inspection.
- Use `AbstractModel` only when the task depends on external data loading.
- When a user only needs to understand a component pattern, prefer references
  over a long worked example in the skill file itself.

## Examples of what belongs here

- A one-off model with a couple of variables and constraints.
- A script that inspects model components or prints values.
- A tiny binary model used to confirm the package and solver path.

## Examples of what does not belong here

- Solver templates, config files, or CLI subcommands.
- DAE discretization, GDP transformations, or network expansion.
- Optional backend installation or GUI troubleshooting.

## Related routes

- Move to `data-and-io` when the model starts from external input.
- Move to `solve-and-cli` when the question is about execution or solver flags.
- Move to `structured-modeling` when the model uses transformations or special
  model families.
- Move to `solver-extensions` when the workflow depends on optional packages or
  advanced solver interfaces.
