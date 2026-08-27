---
name: operators-and-variables
description: "Customize pymoo variables, sampling, crossover, mutation, repair,
  initialization, duplicate elimination, and mixed-variable search workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# operators-and-variables

Use this sub-skill when a task asks how to customize pymoo's search space or
evolutionary operators: real/integer/binary/choice variables, mixed-variable
problems, permutation or discrete encodings, sampling, crossover, mutation,
repair, selection/survival, duplicate elimination, initial populations, or
algorithm hyperparameter helper APIs.

## Route first

- Objective/constraint `_evaluate` shapes, `G <= 0`, bounds warnings, or built-in
  test problems belong to `problem-modeling`.
- Running `minimize`, choosing termination, callbacks, direct stepping, or
  interpreting `Result` belongs to `optimization-workflows`.
- Parallel evaluation, optional joblib/dask/ray, compiled-extension checks, and
  resource controls belong to `performance-and-parallelization`.
- Hypervolume, IGD/GD, MCDM, reference directions, decomposition, or plots belong
  to `analysis-and-visualization`.
- Stay here for how candidate values are represented and transformed during
  initialization and variation.

## Fast operating checklist

1. **Match the encoding to the variables**: ordinary real-valued algorithms use
   float arrays; mixed-variable workflows use `vars={...}` with `Real`,
   `Integer`, `Binary`, and `Choice` objects plus `MixedVariableGA` or compatible
   mixed-variable mating.
2. **Repair integer/discrete values after float variation**: SBX/PM can produce
   floats unless you use integer-aware variables, `RoundingRepair`, or custom
   repair.
3. **Respect operator shapes**: `Sampling._do` returns `(n_samples, n_var)` or an
   object-compatible list/matrix; `Crossover._do` receives
   `(n_parents, n_matings, n_var)` and returns `(n_offsprings, n_matings,
   n_var)`; `Mutation._do` returns mutated `X` rows.
4. **Keep object encodings explicit**: for strings, lists, routes, subsets, or
   dictionaries, use `dtype=object`, custom duplicate elimination, and
   problem-specific sampling/crossover/mutation.
5. **Initialize deliberately**: pass sampling operators, initial arrays, or
   evaluated populations when the starting design matters.
6. **Use repair for feasibility-preserving encodings**: bounds repair, rounding,
   or domain-specific repair can outperform penalty-only constraint handling.
7. **Treat optional helper integrations as optional**: `optuna` and `comocma`
   are optional extras; do not assume them in a base pymoo environment.

## Open the bundled references

- [Operator API reference](references/operator-api-reference.md): variable
  classes, operator base contracts, common import paths, and shape conventions.
- [Variable and operator workflows](references/variable-and-operator-workflows.md):
  mixed-variable GA, integer repair, custom object/string operators, initial
  populations, duplicate elimination, and hyperparameter helper recipes.
- [Troubleshooting](references/troubleshooting.md): fixes for float integers,
  object dtype mistakes, crossover/mutation shape errors, duplicate handling,
  invalid initial populations, and missing optional extras.

## Bundled script

- [scripts/mixed_variable_smoke.py](scripts/mixed_variable_smoke.py): safe
  CPU-only smoke that solves a tiny `Real`/`Integer`/`Binary`/`Choice` problem
  with `MixedVariableGA` and asserts valid result types.
