---
name: problem-modeling
description: "Define, validate, and troubleshoot pymoo optimization problems,
  built-in test problems, constraints, bounds, and evaluation output shapes."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# problem-modeling

Use this sub-skill when a task asks how to represent an optimization problem in
pymoo: built-in benchmark problems, custom vectorized or elementwise objectives,
functional objectives, bounds, constraint signs, equality constraints, Pareto
front/set methods, evaluation shape validation, or confusing `Problem` warnings.

## Route first

- Algorithm choice, `minimize`, termination, ask-and-tell, callbacks, and result
  interpretation belong to `optimization-workflows`.
- Mixed variables, sampling/crossover/mutation/repair, duplicate elimination,
  initialization, and custom operators belong to `operators-and-variables`.
- Vectorization vs parallel runners and optional joblib/dask/ray backends belong
  to `performance-and-parallelization`.
- Indicators, reference directions, decomposition, MCDM, convergence, and plots
  belong to `analysis-and-visualization`.
- Stay here for problem metadata, `_evaluate` contracts, objective/constraint
  sign conventions, built-in `get_problem`, and validation of `F`/`G`/`H`.

## Fast operating checklist

1. **Convert the math to pymoo conventions**: every objective is minimized.
   Negate objectives that the source problem describes as maximized. Inequality
   constraints belong in `out["G"]` and are feasible when `G <= 0`; equality
   constraints belong in `out["H"]` and should be near zero.
2. **Pick the problem style**: use vectorized `Problem` for matrix-friendly
   NumPy/SciPy objectives; use `ElementwiseProblem` for one-candidate black-box
   calls; use `FunctionalProblem` for concise objective/constraint functions.
3. **Set metadata in `__init__`**: `n_var`, `n_obj`, `n_ieq_constr`,
   `n_eq_constr`, `xl`, `xu`, and optional `vtype`/`vars` must match the search
   space and outputs.
4. **Return stable shapes**: for vectorized multi-objective outputs, make
   `out["F"]` a 2-D matrix with one row per candidate and one column per
   objective. For constraints, align rows with `F`.
5. **Validate before optimizing**: call `problem.evaluate(...)` on tiny sample
   inputs, request `F`, `G`, and `H`, assert finite values, and inspect signs.
6. **Use built-in problems for smoke tests**: `get_problem("zdt1")`,
   `get_problem("dtlz2", n_obj=3)`, `Sphere(n_var=...)`, and constrained
   families are useful baselines before debugging custom code.
7. **Treat deprecated `n_constr` carefully**: this version maps it to
   `n_ieq_constr` with a warning; new problem code should use `n_ieq_constr`
   and `n_eq_constr` explicitly.

## Open the bundled references

- [API reference](references/api-reference.md): signatures and output contracts
  for `Problem`, `ElementwiseProblem`, `FunctionalProblem`, `get_problem`, and
  `evaluate`.
- [Problem definition workflows](references/problem-definition-workflows.md):
  built-in problems, vectorized/elementwise/functional definitions, constraints,
  Pareto fronts, bounds, and validation recipes.
- [Troubleshooting](references/troubleshooting.md): fixes for wrong constraint
  sign, objective maximization, shape errors, bounds warnings, NaNs, deprecated
  arguments, and missing Pareto fronts.

## Bundled script

- [scripts/validate_problem_shapes.py](scripts/validate_problem_shapes.py): safe
  CPU-only assertions for a vectorized constrained problem and an elementwise
  constrained problem.
