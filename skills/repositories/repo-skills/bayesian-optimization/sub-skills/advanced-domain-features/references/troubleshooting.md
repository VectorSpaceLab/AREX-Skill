# Troubleshooting Advanced Domain Features

## Constraint function `TypeError` or name mismatch

Symptoms:

```text
Encountered TypeError when evaluating constraint function.
This could be because your constraint function doesn't use the same keyword arguments as the target function.
```

Likely cause: the constraint function arguments do not match the objective and
`pbounds` keys. `TargetSpace` calls both target and constraint with the same
parameter dictionary.

Recovery:

1. Compare `optimizer.space.keys` with `inspect.signature(objective)` and
   `inspect.signature(constraint.fun)`.
2. Rename the constraint arguments to match the `pbounds` keys, or wrap it:
   `lambda x, y: original_constraint(a=x, b=y)`.
3. For typed parameters, remember the constraint receives canonical values
   such as integers and category labels, not raw one-hot arrays.
4. Rebuild the `NonlinearConstraint` and optimizer.

## `NoValidPointRegisteredError` in a constrained optimizer

Symptoms:

```text
Cannot suggest a point without an allowed point. Use target_space.random_sample() ... until at least one point that satisfies the constraints is found.
```

Likely cause: Expected Improvement or Probability of Improvement needs a best
allowed target, but every registered point violates the constraints.

Recovery:

1. Inspect `optimizer.res` for `allowed` flags and raw `constraint` values.
2. Verify the lower/upper bounds are not inverted or too narrow.
3. Seed at least one feasible observation with `optimizer.register(params=..., target=..., constraint_value=...)`.
4. If feasibility is rare, add more random initial points or design a feasible
   warm-start point before calling `suggest()`.

## Unsupported acquisition with constraints

Symptoms:

```text
ConstraintNotSupportedError: Received constraints, but acquisition function ... does not support constrained optimization.
```

Likely cause: `UpperConfidenceBound` or `ConstantLiar` was used on a constrained
`TargetSpace`. The constrained default is Expected Improvement.

Recovery:

1. Omit `acquisition_function` and let the optimizer choose constrained EI, or
   use a constraint-compatible EI/PI acquisition.
2. Route acquisition strategy questions to
   [`../../acquisition-control/SKILL.md`](../../acquisition-control/SKILL.md).
3. Do not solve this by deleting the constraint unless the user explicitly wants
   an unconstrained search.

## Invalid constraint lower/upper bounds

Symptoms:

```text
ValueError: Lower bounds must be less than upper bounds.
```

Likely cause: at least one `lb >= ub` after scalar/array conversion.

Recovery:

1. Print or inspect `constraint.lb` and `constraint.ub`.
2. Ensure every paired lower bound is strictly below the upper bound.
3. Use `-np.inf` or `np.inf` for one-sided constraints.
4. For multiple constraints, ensure the return vector order matches the bound
   arrays.

## Missing `constraint_value` on manual register

Symptoms:

```text
When registering a point to a constrained TargetSpace a constraint value needs to be present.
```

Likely cause: `optimizer.register(...)` or `space.register(...)` was called on a
constrained optimizer without the raw constraint value.

Recovery:

```python
params = {"x": 1.0, "y": 0.5}
optimizer.register(
    params=params,
    target=objective(**params),
    constraint_value=constraint.fun(**params),
)
```

For multiple constraints, pass the returned array.

## Duplicate or invalid categorical categories

Symptoms:

```text
ValueError: Categories must be unique.
ValueError: At least two categories are required.
```

Likely cause: a categorical `pbounds` sequence contains duplicates or only one
category.

Recovery:

1. Deduplicate categories while preserving their intended meaning.
2. If only one category is valid, remove that parameter from the search space
   and hard-code the value in the objective.
3. Use meaningful category labels rather than ordinal integers unless order is
   mathematically meaningful.

## Experimental non-float warning

Symptoms:

```text
Non-float parameters are experimental and may not work as expected.
```

Likely cause: at least one `IntParameter`, `CategoricalParameter`, or custom
non-float parameter is present.

Recovery:

- The warning is expected for typed domains; do not suppress it in generated
  guidance unless a local script deliberately filters warnings for cleaner
  output.
- Validate with a small run or the bundled smoke script.
- Inspect `optimizer.res` to confirm objective arguments and result params are
  canonical values.
- If behavior is unstable, reduce categorical cardinality, scale continuous
  features, seed known good points, or use a staged search.

## `params_to_array` key mismatch

Symptoms:

```text
ValueError: Parameters' keys (...) do not match the expected set of keys (...).
```

Likely cause: a dictionary is missing a key, contains an extra key, or uses a
renamed parameter not present in `pbounds`.

Recovery:

1. Use `optimizer.space.keys` as the required key set.
2. Pass every key exactly once. Input dictionary order does not matter.
3. For derived hyperparameters, put only the optimizer-facing keys in
   `pbounds`; compute derived values inside the objective.

## `array_to_params` or raw-array dimension mismatch

Symptoms:

```text
ValueError: Size of array (...) is different than the expected number of parameters (...).
```

Likely cause: the raw array length does not match `space.dim`. This often
happens with categorical parameters because one category dimension is allocated
per category.

Recovery:

1. Prefer dictionary params for typed/custom domains.
2. Inspect `space.dim`, `space.keys`, and `space.masks`.
3. Remember that `{"kind": ["a", "b", "c"]}` contributes three internal
   dimensions, not one.
4. Convert with `space.params_to_array(...)` instead of hand-building arrays.

## Domain reduction with non-float parameters

Symptoms:

```text
ValueError: Domain reduction is only supported for all-FloatParameter optimization.
```

Likely cause: `SequentialDomainReductionTransformer.initialize(...)` found an
integer, categorical, or custom parameter that is not a `FloatParameter`.

Recovery:

1. Remove `bounds_transformer` for the mixed-domain run.
2. If domain reduction is essential, reparameterize the reduced variables as
   floats and handle casting/categories outside the optimizer, acknowledging the
   typed-kernel trade-off.
3. Consider a two-stage workflow: typed coarse search, then float-only domain
   reduction around selected choices.

## Invalid `minimum_window`

Symptoms:

```text
ValueError: Length of minimum_window must be the same as the number of parameters
ValueError: Global bounds are not compatible with the minimum window size.
```

Likely cause: `minimum_window` sequence length does not match the bounds rows,
or a requested minimum width is larger than the original global interval.

Recovery:

1. Use a scalar if the same width is acceptable for every float parameter.
2. Use a mapping keyed by `TargetSpace.keys` to avoid ordering mistakes.
3. Ensure each minimum width is no larger than `upper - lower` for that
   parameter.

## Domain reduction warnings during trimming

Symptoms include warning text about a parameter boundary being reset because a
proposed bound exceeded the global bounds.

Likely cause: the reduced window center and size proposed bounds outside the
original `pbounds`.

Recovery:

- Check that original bounds are broad enough and correctly ordered.
- Inspect `bounds_transformer.bounds` to see whether repeated reductions are
  over-focusing.
- Increase `minimum_window` or use less aggressive shrinkage if the optimizer is
  chasing noise.

## Custom parameter shape or transform failures

Symptoms: GP fitting errors, acquisition optimization errors, non-finite arrays,
or conversion errors after adding a custom `BayesParameter`.

Likely causes:

- `dim` does not match the number of columns returned by `random_sample` or
  `to_float`.
- `bounds` shape does not match `dim`.
- `to_param` fails for a one-dimensional slice from `TargetSpace`.
- `kernel_transform` is not vectorized or changes dimensionality.

Recovery:

1. Create a `TargetSpace(None, {"param": custom_param})` and test
   `random_sample`, `params_to_array`, `array_to_params`, and
   `kernel_transform` before running optimization.
2. Keep `kernel_transform` shape-preserving and finite.
3. For constrained custom parameters, ensure the constraint function accepts the
   canonical value returned by `to_param`.

## Smoke-test diagnostics

Use the bundled helper for a quick local sanity check:

```bash
python scripts/advanced_features_smoke.py --check all
```

If the helper cannot import `bayes_opt`, install the public package and its
normal runtime dependencies in the active Python environment. The helper does
not need network access and does not open original repository files.
