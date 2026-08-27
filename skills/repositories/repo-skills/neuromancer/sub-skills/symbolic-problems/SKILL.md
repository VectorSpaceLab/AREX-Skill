---
name: symbolic-problems
description: "Formulate and diagnose NeuroMANCER symbolic variables, objectives,
  constraints, aggregate losses, Node graphs, and constrained parametric
  Problems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Symbolic problems

Use this route when the task is about NeuroMANCER 1.5.6 symbolic programming:
`Variable` expressions, comparison constraints, `.minimize()` objectives,
`PenaltyLoss`/`BarrierLoss`/`AugmentedLagrangeLoss`, dictionary-wired `Node`
components, `Problem` computation graphs, or differentiable constrained
parametric optimization.

## Route quickly

1. Prefer module-qualified imports so the code does not depend on incidental
   top-level re-exports:
   `neuromancer.constraint`, `neuromancer.loss`, `neuromancer.system`, and
   `neuromancer.problem`.
2. Define input/output keys first. Use `variable("key")` for values supplied by
   a batch and use a `Node` to produce decision-variable tensors such as `x`.
3. Build expressions, call `.minimize(...)`, and write inequalities in the
   mathematical direction intended by the model. Check the residual sign and
   tensor shapes before selecting a loss.
4. Give every node, objective, and constraint an explicit unique `name`. Keep
   symbolic input keys and output keys unique; set `check_overwrite=True` while
   diagnosing a new graph.
5. Construct `Problem(nodes, loss, grad_inference=False,
   check_overwrite=False)`. Supply a batch dictionary containing every required
   key and a string `name`; `Problem.forward` prefixes every returned key with
   that name.
6. Run the bundled CPU-only check when a minimal executable confirmation is
   useful: [`scripts/core_smoke.py`](scripts/core_smoke.py).

Detailed contracts and examples are in:

- [`references/api-reference.md`](references/api-reference.md) — factories,
  operators, exact class signatures, output keys, graph and gradient behavior.
- [`references/workflows.md`](references/workflows.md) — formulation,
  validation, loss selection, and a small end-to-end CPU recipe.
- [`references/troubleshooting.md`](references/troubleshooting.md) — key,
  naming, tensor, comparator, graph rendering, and autograd failures.

## Boundaries and sibling routes

- Route static/sequence/graph data schemas, splitting, collators, and Trainer or
  Lightning details to [`../data-training/SKILL.md`](../data-training/SKILL.md).
- Route ODE/PINN/DAE/SDE models, integrators, and physics residual construction
  to [`../dynamics-modeling/SKILL.md`](../dynamics-modeling/SKILL.md).
- Route rollout loops, preview horizons, PSL simulators, and control signals to
  [`../control-simulation/SKILL.md`](../control-simulation/SKILL.md).
- Route SLiM maps, structured layers, and differentiable operator solvers to
  [`../structured-operators/SKILL.md`](../structured-operators/SKILL.md).

This route can still own the symbolic objective or constraint attached to a
model from a sibling route; hand off the model/data/rollout portion rather than
repeating it here.

## Verification stance

The contracts here are distilled from the package implementation, public
constraint/loss/problem/component/gradient documentation, the symbolic
 tutorials, the parametric-programming formulations, and the variable,
constraint, loss, problem, and system tests for the versioned 1.5.6 package.
The bundled smoke is deterministic, CPU-only, uses no network or training
loop, and checks that a tiny `Node`-to-`Problem` loss remains differentiable.
