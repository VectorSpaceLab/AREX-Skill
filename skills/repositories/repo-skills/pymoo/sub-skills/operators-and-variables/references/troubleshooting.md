# Operators and Variables Troubleshooting

## Integer variables become floats

Likely causes:
- Real-coded SBX/PM variation is used without rounding repair.
- The problem only set `vtype=int`, which is a hint but not a full mixed-variable
  search configuration.

Recovery:
- Use explicit `Integer(bounds=(lo, hi))` variables with `MixedVariableGA` for
  heterogeneous spaces.
- Or pass `RoundingRepair()` to SBX/PM and validate bounds after rounding.
- Assert result values are integer-valued before reporting a solution.

## Categorical values disappear or become invalid

Likely causes:
- Choice variables encoded as integers without a decoder/repair.
- Ordinary float mutation applied to a category column.

Recovery:
- Use `Choice(options=[...])` and mixed-variable mating, or implement a stable
  encode/decode layer plus repair.
- Check every final value belongs to the original option set.

## Custom crossover shape mismatch

pymoo passes crossover input as:

```text
(n_parents, n_matings, n_var)
```

and expects output:

```text
(n_offsprings, n_matings, n_var)
```

Recovery:
- Set `super().__init__(n_parents, n_offsprings)` correctly.
- Allocate `Y` with the right first dimension.
- For object values, use `dtype=object` and avoid NumPy coercion to strings or
  floats.

## Mutation changed shape or dtype

Symptoms:
- Errors during population construction.
- Object strings/lists become arrays of characters or `nan` values.

Recovery:
- Return the same row count and variable count as input.
- Mutate in place only when safe; otherwise copy and preserve dtype.
- For object arrays, allocate `np.empty_like(X, dtype=object)` if needed.

## Duplicate elimination does not work

Likely causes:
- Object identity is compared instead of semantic equality.
- Floating arrays need tolerance-aware comparison.
- Dictionary/mixed-variable rows have inconsistent keys.

Recovery:
- Subclass `ElementwiseDuplicateElimination` and implement `is_equal(a, b)` for
  your encoding.
- For mixed dictionaries, ensure every row has the same variable keys.
- For continuous variables, set a tolerance compatible with the task instead of
  exact equality when appropriate.

## Initial population fails at setup

Checklist:
- Candidate row count and `n_var` match the problem.
- Bounds are respected or a repair operator is provided.
- For mixed variables, rows are dictionaries with variable names and valid
  values, not numeric arrays.
- Pre-evaluated populations have `F`/`G` shapes matching problem metadata.
- Any precomputed values use the same objective sign and constraint convention
  as the problem.

## Repair hides a modeling mistake

A repair operator can transform infeasible candidates, but it should not silently
change the optimization problem. If repair makes every candidate identical or
moves points to a narrow boundary, inspect the encoding, bounds, and constraint
formulation. Report repair effects in final results when they are material.

## Optional `optuna` or `comocma` import fails

These integrations are optional extras. Base pymoo does not install them.

Recovery:
- If the task explicitly needs Optuna-backed hyperparameter optimization or
  COMO-CMA-ES, install the relevant optional dependency in an isolated
  environment.
- Otherwise, use base pymoo alternatives such as `MixedVariableGA` for small
  hyperparameter smoke tests or route to another algorithm.

## Mixed-variable multi-objective surprise

`MixedVariableGA` is a convenient mixed-variable genetic algorithm with a
single-objective default survival/output configuration. If a task needs true
multi-objective mixed-variable optimization, verify the selected algorithm,
mating, survival, and output combination explicitly rather than assuming a base
`MixedVariableGA` constructor is enough for all MOO tasks.

## Permutation validity breaks

Symptoms:
- Duplicate items or missing items in a route/permutation.
- Objective crashes on invalid order.

Recovery:
- Use permutation-aware sampling, crossover, and mutation.
- Add a repair or assertion that `sorted(route) == list(range(n_items))`.
- Do not use independent integer mutation for permutations unless a decoder
  converts rows back to valid permutations.
