# Optimizer API Reference

This reference covers the core public `bayes_opt.BayesianOptimization` workflow
for package version 3.3.0. It intentionally omits deep acquisition-function,
constraint, typed-parameter, custom-parameter, and domain-reduction guidance;
route those to the sibling sub-skills named in `../SKILL.md`.

## Import And Constructor

```python
from bayes_opt import BayesianOptimization

optimizer = BayesianOptimization(
    f=objective_or_none,
    pbounds={"x": (-2.0, 2.0), "y": (-3.0, 3.0)},
    acquisition_function=None,
    constraint=None,
    random_state=1,
    verbose=2,
    bounds_transformer=None,
    allow_duplicate_points=False,
)
```

Current verified signature:

```text
BayesianOptimization(
    f,
    pbounds,
    acquisition_function=None,
    constraint=None,
    random_state=None,
    verbose=2,
    bounds_transformer=None,
    allow_duplicate_points=False,
)
```

Parameter rules:

- `f` is a callable to maximize, or `None` for manual ask-tell loops.
- `pbounds` is a dictionary from parameter name to bounds. For ordinary float
  optimization, values are `(min, max)` tuples.
- Every `pbounds` key must match an objective keyword argument. Example:
  `pbounds={"x": ..., "y": ...}` requires `def objective(x, y): ...`.
- Dict order matters for array/list conversions. If you pass arrays to
  `register()` or `probe()`, element order follows the insertion order of
  `pbounds`. Prefer dicts in user-facing workflows.
- `random_state` accepts an integer seed, a `numpy.random.RandomState`, or
  `None`. Use a seed for reproducible suggestions.
- `verbose=0` is silent, `verbose=1` prints only new maxima, and `verbose=2`
  prints each logged step.
- `allow_duplicate_points=False` rejects duplicate coordinates with
  `NotUniqueError`; set it to `True` only when repeated noisy evaluations at the
  same point are intentional.

Default acquisition behavior: when `acquisition_function=None`, the optimizer
uses an unconstrained default for ordinary problems and a constrained default
when `constraint` is supplied. Detailed acquisition selection belongs in
`../../acquisition-control/SKILL.md`.

## Objective Function Contract

The optimizer maximizes `target = f(**params)`. A valid objective should:

- Accept exactly the `pbounds` keys as keyword arguments.
- Return a finite scalar numeric value. Convert arrays, tuples, metrics, or
  framework tensors to a Python float before returning.
- Treat losses as negative scores: return `-loss` or a scorer such as
  scikit-learn's `neg_log_loss`, because larger target values are always better.
- Catch or prevent invalid model configurations inside the wrapper. If a model
  fails for a legal point, either return a very low finite score or narrow the
  bounds after diagnosing the failure.

For slow objectives, first run a tiny budget (`init_points=1 or 2`,
`n_iter=1 or 2`) to validate the signature, sign, and result structure before a
long run.

## Core Method Signatures

```text
maximize(init_points=5, n_iter=25) -> None
predict(params, return_std=False, return_cov=False, fit_gp=True)
register(params, target, constraint_value=None) -> None
probe(params, lazy=True) -> None
random_sample(n=1) -> list[dict]
suggest() -> dict
set_bounds(new_bounds) -> None
set_gp_params(**params) -> None
save_state(path) -> None
load_state(path) -> None
```

## Lifecycle Semantics

### `maximize(init_points=5, n_iter=25)`

`maximize()` drives the standard loop:

1. It logs a header when `verbose` is nonzero.
2. It primes a queue with random samples. If the optimizer has no observations
   and no queued points, `maximize(init_points=0, n_iter=0)` still evaluates one
   random point.
3. It consumes queued `probe(..., lazy=True)` points and random initial points.
4. It performs `n_iter` acquisition-driven suggestions.
5. It evaluates each point by calling `probe(..., lazy=False)`.

Important warning: during `maximize()`, the internal Gaussian Process is fitted
when an acquisition-driven suggestion is needed. The final registered point may
not be included in the fitted GP when the method returns. If you need posterior
predictions or uncertainty after the run, call `predict(..., fit_gp=True)`.

### `max` and `res`

`optimizer.max` returns either `None` or a dictionary describing the best valid
observed point:

```python
{"target": 0.95, "params": {"x": 1.2, "y": -0.3}}
```

For constrained optimizers, the result can also include a `constraint` entry and
is filtered to valid points. Constraint workflows are owned by the advanced
sibling sub-skill.

`optimizer.res` returns a list of all observations in registration order:

```python
[
    {"target": 0.3, "params": {"x": -0.5, "y": 0.1}},
    {"target": 0.95, "params": {"x": 1.2, "y": -0.3}},
]
```

Validation pattern:

```python
assert optimizer.max is not None
assert "target" in optimizer.max and "params" in optimizer.max
assert len(optimizer.res) == len(optimizer.space)
for row in optimizer.res:
    assert set(row["params"]) == set(pbounds)
```

### `probe(params, lazy=True)`

`probe()` asks the optimizer to evaluate a point using its `f` callable.

- `lazy=True` appends the point to an internal queue and does not evaluate until
  the next `maximize()` call.
- `lazy=False` evaluates immediately by calling the target function and
  registering the result.
- With `f=None`, eager probing raises `ValueError: No target function has been
  provided.` Use `register()` instead after evaluating externally.
- Duplicate eager probes return a cached target when duplicates are disallowed
  at the `TargetSpace` level, but `BayesianOptimization.register()` rejects
  direct duplicate registrations unless duplicates are allowed. Avoid relying on
  duplicates unless you deliberately enabled noisy duplicate behavior.

### `register(params, target, constraint_value=None)`

`register()` records an already-known observation. It does not call `f`.

Use it for manual ask-tell loops, distributed evaluations, expensive lab runs,
or results coming from another process:

```python
params = optimizer.suggest()
target = external_evaluate(params)
optimizer.register(params=params, target=float(target))
```

Duplicate points raise `bayes_opt.exception.NotUniqueError` unless the optimizer
was constructed with `allow_duplicate_points=True`. In constrained use,
`constraint_value` is required; route detailed constraint handling to the
advanced-domain sibling.

### `suggest()` and `random_sample(n=1)`

`suggest()` returns one parameter dictionary. If there are no observations, it
returns a random sample from the target space. After observations exist, it fits
or refits the GP as needed and asks the acquisition function for the next point.

`random_sample(n=1)` returns a list of `n` parameter dictionaries drawn uniformly
inside the current bounds. It is useful for diagnostics, custom initialization,
or sanity-checking bounds before running an expensive objective.

### `set_bounds(new_bounds)`

`set_bounds()` updates bounds for existing parameters. Unknown keys are ignored.
It does not rename parameters or add new parameters. For ordinary float bounds:

```python
optimizer.set_bounds({"x": (-1.0, 1.5)})
```

At the `TargetSpace` level, existing observations outside the new bounds can be
excluded from `max` selection because the validity mask checks current bounds.
`res` still reports all observations. Changing a parameter's type or dimension
raises `ValueError`; typed and custom parameter details belong in the advanced
sibling sub-skill.

### `set_gp_params(**params)`

`set_gp_params()` forwards keyword arguments to the internal scikit-learn
`GaussianProcessRegressor`. Common safe knobs are:

```python
optimizer.set_gp_params(alpha=1e-3, n_restarts_optimizer=3, normalize_y=True)
```

Use a larger `alpha` for noisy objectives to improve numerical stability.
Custom kernels are wrapped internally so they remain compatible with the
optimizer's parameter transform, but kernel design is an expert topic; keep
basic workflows conservative.

## `predict` Semantics

Signature:

```text
predict(params, return_std=False, return_cov=False, fit_gp=True)
```

Input forms:

- A single dict: `{"x": 0.1, "y": 0.2}`.
- An iterable of dicts: `[{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}]`.
- Strings and other invalid types raise `TypeError`.

Return-shape rules:

| Call | Mean return | Extra return |
| --- | --- | --- |
| `predict(dict)` | scalar-like value | none |
| `predict([dict])` | 1D array length 1 | none |
| `predict([dict, dict])` | 1D array length N | none |
| `predict(dict, return_std=True)` | scalar-like mean | scalar-like std |
| `predict([dicts], return_std=True)` | 1D array length N | 1D array length N |
| `predict(dict, return_cov=True)` | scalar-like mean | 2D covariance array |
| `predict([dicts], return_cov=True)` | 1D array length N | 2D covariance array `(N, N)` |

`return_std=True` and `return_cov=True` are mutually exclusive and raise
`ValueError` if both are set.

`fit_gp=True` refits the internal GP first. With zero observations, this raises
`RuntimeError` because the GP cannot be fitted. For prior-only diagnostics with
no observations, use `fit_gp=False`; the mean comes from the unfitted GP prior
and should not be interpreted as evidence about the objective.

Recommended pattern after optimization:

```python
mean, std = optimizer.predict({"x": 0.0, "y": 1.0}, return_std=True, fit_gp=True)
```

## State Persistence

`save_state(path)` writes JSON. The state includes observed params, targets,
current bounds, GP parameters, acquisition parameters, random-state information,
verbose setting, and duplicate-point policy. It can be saved even before any
samples are registered.

Resume pattern:

```python
old_optimizer.save_state("optimizer_state.json")

new_optimizer = BayesianOptimization(
    f=objective,
    pbounds=compatible_pbounds,
    random_state=1,
    verbose=0,
)
new_optimizer.load_state("optimizer_state.json")
new_optimizer.maximize(init_points=0, n_iter=5)
```

Compatibility requirements:

- Recreate the optimizer before loading; `load_state` mutates the existing
  instance.
- Use a compatible `f` signature and `pbounds` key set/order. If bounds were
  changed before saving, construct the new optimizer with bounds compatible
  with the saved state and intended continuation.
- Recreate any custom acquisition function, constraint, duplicate policy, and
  bounds transformer before loading. Loading restores acquisition parameters and
  GP parameters, but it does not invent missing custom objects.
- Do not append stale observations accidentally: load into a fresh optimizer
  unless you intentionally want to register existing points before load.
- Validate loaded state with `len(res)`, `max`, and a known subsequent
  `suggest()` when reproducibility matters.

## TargetSpace Facts Exposed Through The Optimizer

`optimizer.space` is the underlying `TargetSpace`. Most users should not need
it, but it explains public behavior:

- `space.keys` stores `pbounds` keys in insertion order.
- `space.params` is the observed design matrix.
- `space.target` is the observed target array.
- Dict-to-array conversion requires exactly the same key set.
- Array-to-dict conversion uses `pbounds` order.
- Duplicate coordinates are tracked by a hash of the numeric array
  representation.
- `space.set_bounds()` ignores unknown keys but rejects type/dimension changes.
- `space.max()` can return `None` if no valid observations exist.
