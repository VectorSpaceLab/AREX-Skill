# Problem Modeling Troubleshooting

## Constraints are backwards

Symptoms:
- Points that should be feasible have positive `G` values.
- Optimizer returns no feasible solution for an obviously feasible problem.

pymoo convention:

```text
Inequality constraints are feasible when G <= 0.
Equality constraints are feasible when H ~= 0.
```

Recovery:
- Convert `a(x) <= b` to `a(x) - b <= 0`.
- Convert `a(x) >= b` to `b - a(x) <= 0`.
- Normalize constraints when one violation scale dominates ranking.
- Use `n_eq_constr` and `out["H"]` for equalities instead of forcing them into
  inequalities unless an explicit tolerance formulation is acceptable.

## Maximization objective behaves poorly

pymoo minimizes. Convert `maximize f(x)` to `minimize -f(x)`. When reporting final
results back to a user, convert the sign again so the original objective meaning
is clear.

## Shape errors from `_evaluate`

Common messages include mismatched dimensions, assertion errors in `evaluate`, or
unexpected one-dimensional output.

Recovery:
- For vectorized `Problem`, `X` has shape `(n_candidates, n_var)`.
- For multi-objective vectorized output, use `np.column_stack([f1, f2, ...])`.
- For multiple constraints, use `np.column_stack([g1, g2, ...])`.
- For one objective, prefer `f[:, None]` or `np.sum(..., keepdims=True)` while
  debugging.
- For elementwise output, return a scalar/list for one candidate; pymoo stacks it
  across candidates.

## Bounds warnings

Symptoms:
- Warning that `xl`/`xu` have wrong length.
- Warning that `xl > xu` at one or more indices.

Recovery:
- If using scalars, pass scalar `xl`/`xu` intentionally for all variables.
- If using arrays, ensure both have length `n_var` and matching order.
- Check unit conversions and sign mistakes before assuming an algorithm problem.

## `n_constr` deprecation warning

This version accepts `n_constr` as a deprecated alias mapped to inequality
constraints. New code should use:

```python
super().__init__(n_ieq_constr=number_of_G_constraints,
                 n_eq_constr=number_of_H_constraints, ...)
```

If old code used `n_constr` for equalities, split the constraints and write
`out["H"]` for equality residuals.

## `Problem not found`

Likely causes:
- Built-in problem name misspelled or wrong punctuation.
- Mixed family naming such as `zdt1`, `dtlz2`, `wfg1`, `mw1`, `dascmop1`, `df1`.

Recovery:
- Lowercase the name and check family prefixes.
- For custom problems, instantiate the class directly rather than using
  `get_problem`.

## NaNs or infinite objective values

Symptoms:
- Optimizer stalls, returns empty results, or warnings appear during survival.
- Analysis metrics fail because `F` has non-finite rows.

Recovery:
- Clip or repair invalid design variables before domain-sensitive math.
- Add explicit checks around log/sqrt/division operations.
- Return a large finite penalty only when that behavior is mathematically
  justified and documented.
- Use `replace_nan_values_by` as a last-resort guard, not as a substitute for
  debugging.

## Elementwise problem runs too slowly

Elementwise style is convenient but loops over candidates. If objective math is
NumPy/SciPy vectorizable, convert to vectorized `Problem`. If each candidate is a
black-box simulation, use `elementwise_runner` with the performance sub-skill and
keep pool cleanup explicit.

## FunctionalProblem cannot be parallelized or pickled

Lambdas or closures can capture non-serializable state. Convert to a module-level
`Problem`/`ElementwiseProblem` class when using process pools, distributed
workers, checkpointing, or reusable scripts.

## Mixed variable dictionary errors

If `X` rows are dictionaries or object arrays, route to
`operators-and-variables`. The ordinary numeric `Problem` shape rules no longer
fully describe how variables are sampled and mated; explicit `vars={...}` and
mixed-variable operators are usually needed.

## Pareto front is unavailable

Do not invent `pf` for GD/IGD just because a metric requires it. Options:
- Use a built-in problem's `pareto_front()` only when available.
- Use non-dominated filtering on observed `F` for qualitative inspection.
- Use hypervolume with an explicit reference point.
- Use history or anytime indicators to compare runs under the same budget.
