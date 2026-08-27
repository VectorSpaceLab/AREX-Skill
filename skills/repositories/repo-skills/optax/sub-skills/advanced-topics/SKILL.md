---
name: advanced-topics
description: "Use Optax projections, tree utilities, assignment, second-order
  helpers, and contrib algorithms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Advanced Topics

Use this sub-skill when the user is asking about **constraint handling, tree manipulation, assignment, second-order utilities, or contrib/experimental algorithms**. This is the route for the more specialized Optax modules.

## Include here

- Projection helpers in `optax.projections`, especially simplex, box, ball, orthant, hyperplane, and halfspace projections.
- Assignment helpers such as `optax.assignment.hungarian_algorithm`.
- Tree utilities in `optax.tree_utils`.
- Numerical and linear-algebra helpers such as `safe_norm`, `matrix_inverse_pth_root`, `power_iteration`, and `nnls`.
- Second-order helpers such as `hvp`, `fisher_diag`, and `hessian_diag`.
- Contrib and experimental algorithms such as `sam`, `schedule_free`, `dpsgd`, `muon`, `galore`, `prodigy`, `mechanic`, `momo`, `adopt`, `acprop`, `sophia`, `reduce_on_plateau`, and `optax.experimental.aggregating`.

## Exclude or route elsewhere

- Ordinary optimizer composition, wrapper selection, and `apply_updates`: use `core-optimization`.
- Plain loss or schedule selection: use `losses-and-schedules`.

## Good questions for this route

- “How do I project parameters onto the simplex or non-negative orthant?”
- “How do I solve a Hungarian assignment problem in Optax?”
- “How do I manipulate parameter trees safely?”
- “How do I use a contrib algorithm like SAM, Muon, or Schedule-Free?”
- “How do I get a Hessian-vector product or another second-order diagnostic?”

## Read first

- `../../references/advanced-topics.md` for the distilled reference on projections, assignment, trees, second order, and contrib/experimental features.
- `../../references/examples-index.md` for example notebooks such as `linear_assignment_problem.ipynb`, `freezing_parameters.ipynb`, and the contrib notebooks.
- `../../references/troubleshooting.md` for tree-shape, projection-feasibility, numerical-stability, and API-drift notes.

## Core workflow

1. Decide whether the request is primarily about constraints, trees, assignment, curvature, or a contrib algorithm.
2. Check tensor/tree shapes and the intended feasible set before calling a projection helper.
3. For tree utilities, confirm which tree is the parameter tree and which tree is auxiliary data.
4. For second-order and linear-algebra helpers, verify the dtype and conditioning assumptions.
5. For contrib algorithms, check whether the feature is stable enough for the user’s intended workflow or whether the request should stay in the exploratory/experimental lane.

## Signals that this route is correct

- The user mentions projections, simplex constraints, assignment, tree arithmetic, or Hessian-like helpers.
- The user names a contrib algorithm or asks for a feature that is clearly outside the main optimizer surface.
- The user wants to study or adapt a specialized notebook rather than a plain training loop.

## Common mistakes

- Applying a projection helper to the wrong tree shape or the wrong feasible set.
- Using tree utilities interchangeably on mismatched trees.
- Assuming a contrib example is interchangeable with the stable main-package API.
- Ignoring the numerical sensitivity of curvature or linear-algebra helpers.

## Useful examples

- `../../references/examples-index.md` points to `linear_assignment_problem.ipynb`, `freezing_parameters.ipynb`, `lookahead_mnist.ipynb`, and several contrib notebooks that belong here.
