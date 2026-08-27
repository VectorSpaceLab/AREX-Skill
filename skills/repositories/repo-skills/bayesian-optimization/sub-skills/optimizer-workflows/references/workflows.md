# Optimizer Workflow Recipes

These recipes are distilled for future agents using the installed
`bayesian-optimization` package. They are safe patterns for ordinary black-box
optimization and tiny ML hyperparameter optimization.

## Recipe 1: Basic Black-Box Maximization

```python
from bayes_opt import BayesianOptimization


def objective(x, y):
    # The optimizer maximizes this scalar value.
    return -x**2 - (y - 1.0) ** 2 + 1.0

pbounds = {"x": (-2.0, 2.0), "y": (-3.0, 3.0)}

optimizer = BayesianOptimization(
    f=objective,
    pbounds=pbounds,
    random_state=1,
    verbose=2,
)
optimizer.maximize(init_points=2, n_iter=5)

best = optimizer.max
history = optimizer.res
```

Validation checklist:

```python
assert best is not None
assert set(best["params"]) == set(pbounds)
assert len(history) >= 1
for row in history:
    assert isinstance(row["target"], float) or hasattr(row["target"], "item")
    assert set(row["params"]) == set(pbounds)
```

Practical guidance:

- Start with `verbose=0` in scripts/tests and `verbose=2` for interactive demos.
- Use `random_state` during debugging so repeated runs are comparable.
- Keep initial budgets tiny until you prove the objective sign, exception
  handling, and runtime.
- If a parameter spans orders of magnitude, optimize its log and transform
  inside the objective.

## Recipe 2: Metric Sign Handling For Losses

The package maximizes. If the real metric is a loss that should be minimized,
convert it to a larger-is-better target.

```python
def objective(log10_lr, depth_float):
    lr = 10 ** log10_lr
    depth = int(round(depth_float))
    validation_loss = train_and_score_model(lr=lr, max_depth=depth)
    return -float(validation_loss)
```

For scikit-learn cross-validation:

- `scoring="accuracy"`, `"roc_auc"`, or estimator `.score()` are already
  larger-is-better.
- `scoring="neg_log_loss"` and other `neg_*` scorers already return negative
  losses where larger is better.
- If you compute `log_loss(...)` yourself, return `-log_loss(...)`.

Report both values when communicating results:

```python
best_target = optimizer.max["target"]
best_loss = -best_target
```

Common mistake: returning a positive loss directly. The optimizer will then seek
larger losses and `optimizer.max` will describe the worst model.

## Recipe 3: Manual Ask-Tell Loop For External Evaluations

Use this when evaluations happen in another process, on another machine, in a
lab, or in a slow training harness that should not be called by `maximize()`.

```python
from bayes_opt import BayesianOptimization

optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 2.0), "y": (-3.0, 3.0)},
    random_state=7,
    verbose=0,
)

for step in range(8):
    params = optimizer.suggest()  # random before any observations exist
    target = external_evaluate(**params)  # your code, service, or lab result
    optimizer.register(params=params, target=float(target))

print(optimizer.max)
```

Rules:

- Never call `maximize()` when `f=None`; it will eventually try to evaluate via
  `probe(..., lazy=False)` and fail.
- Never call eager `probe(..., lazy=False)` when `f=None`; it raises
  `ValueError: No target function has been provided.`
- `probe(..., lazy=True)` only queues points for later `maximize()` and is not a
  substitute for external evaluation.
- Register every result with the exact params that were evaluated.
- If two workers might evaluate the same point, either coordinate suggestions
  outside this core route or use the acquisition-control sibling for batch/
  ConstantLiar strategies.

Manual validation:

```python
assert len(optimizer.res) == number_of_completed_evaluations
assert optimizer.max is None or set(optimizer.max["params"]) == set(pbounds)
```

## Recipe 4: Seed With Known Or Required Points

If you have points that should be evaluated before Bayesian suggestions, use
lazy `probe()` with a real target function:

```python
optimizer = BayesianOptimization(f=objective, pbounds=pbounds, random_state=1)
optimizer.probe({"x": 0.0, "y": 1.0}, lazy=True)
optimizer.probe({"x": -1.0, "y": 0.5}, lazy=True)
optimizer.maximize(init_points=0, n_iter=5)
```

For already-known targets, use `register()` instead of reevaluating:

```python
optimizer.register({"x": 0.0, "y": 1.0}, target=1.0)
optimizer.maximize(init_points=2, n_iter=5)
```

If duplicate points are not allowed, registering the same coordinate twice
raises `NotUniqueError`. Treat that as useful feedback unless noise estimation
requires repeats.

## Recipe 5: Safe Tiny scikit-learn HPO Pattern

This pattern adapts the repository's scikit-learn examples while keeping runtime
small and deterministic.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from bayes_opt import BayesianOptimization

X, y = make_classification(
    n_samples=160,
    n_features=12,
    n_informative=6,
    random_state=11,
)
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=11)


def rf_score(n_estimators_float, min_samples_split_float, max_features):
    n_estimators = int(round(n_estimators_float))
    min_samples_split = int(round(min_samples_split_float))
    max_features = float(np.clip(max_features, 0.2, 1.0))
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        min_samples_split=min_samples_split,
        max_features=max_features,
        random_state=11,
        n_jobs=1,
    )
    scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy", n_jobs=1)
    return float(scores.mean())

optimizer = BayesianOptimization(
    f=rf_score,
    pbounds={
        "n_estimators_float": (5, 20),
        "min_samples_split_float": (2, 8),
        "max_features": (0.25, 1.0),
    },
    random_state=11,
    verbose=0,
)
optimizer.maximize(init_points=2, n_iter=3)
print(optimizer.max)
```

HPO safety rules:

- Keep datasets synthetic or user-supplied; do not download data inside a smoke
  or diagnostic script.
- Bound runtime with small `n_samples`, small CV folds, low estimator counts,
  and `n_jobs=1` unless the user explicitly wants parallelism.
- Cast integer-valued model hyperparameters inside the objective wrapper. For
  native typed parameter syntax such as `(low, high, int)`, route deeper typed
  semantics to `../../advanced-domain-features/SKILL.md`.
- Use log-transformed bounds for scale-sensitive parameters such as `C`,
  `gamma`, regularization, or learning rate.
- Return score metrics directly and return negative losses for loss metrics.

## Recipe 6: Save, Load, And Resume

```python
from pathlib import Path
from bayes_opt import BayesianOptimization

state_path = Path("optimizer_state.json")

optimizer = BayesianOptimization(f=objective, pbounds=pbounds, random_state=1, verbose=0)
optimizer.maximize(init_points=2, n_iter=3)
optimizer.save_state(state_path)

resumed = BayesianOptimization(f=objective, pbounds=pbounds, random_state=1, verbose=0)
resumed.load_state(state_path)
assert len(resumed.res) == len(optimizer.res)
assert resumed.max == optimizer.max

resumed.maximize(init_points=0, n_iter=2)
```

Compatibility checklist before loading:

- Same parameter names and compatible order.
- Bounds compatible with saved observations and intended continuation.
- Same objective signature and target sign.
- Same advanced objects if used: acquisition function, constraints, duplicate
  policy, and bounds transformer.
- Fresh optimizer instance unless intentionally composing observations.

Useful validation after loading:

```python
assert resumed.max is not None or len(resumed.res) == 0
assert all(set(row["params"]) == set(pbounds) for row in resumed.res)
next_point = resumed.suggest()  # should be inside bounds
for name, value in next_point.items():
    lo, hi = pbounds[name][:2]
    assert lo <= value <= hi
```

State files are JSON and safe to inspect with ordinary JSON tools. They are not
a replacement for saving the user objective code, data version, or model config;
record those separately in the user's experiment tracking system.

## Recipe 7: Predict Means And Uncertainty

After at least one observation:

```python
point = {"x": 0.0, "y": 1.0}
mean, std = optimizer.predict(point, return_std=True, fit_gp=True)
```

For multiple candidate points:

```python
points = [{"x": 0.0, "y": 1.0}, {"x": 0.5, "y": 0.5}]
means, stds = optimizer.predict(points, return_std=True, fit_gp=True)
assert len(means) == len(points)
assert len(stds) == len(points)
```

Use `return_cov=True` only when a full covariance matrix is needed:

```python
means, cov = optimizer.predict(points, return_cov=True)
assert cov.shape == (len(points), len(points))
```

Do not set both `return_std=True` and `return_cov=True`. With no observations,
`fit_gp=True` raises a runtime error; `fit_gp=False` returns prior predictions
and is mostly useful for parser/smoke diagnostics rather than decision-making.

## Recipe 8: Noisy Objectives And Duplicate Points

Default duplicate rejection catches accidental repeated evaluations:

```python
from bayes_opt.exception import NotUniqueError

try:
    optimizer.register({"x": 0.1}, target=0.2)
    optimizer.register({"x": 0.1}, target=0.21)
except NotUniqueError:
    print("duplicate coordinate; decide whether this is accidental or noisy")
```

For intentionally noisy objectives:

```python
optimizer = BayesianOptimization(
    f=noisy_objective,
    pbounds={"x": (-2.0, 2.0)},
    random_state=1,
    allow_duplicate_points=True,
    verbose=0,
)
optimizer.set_gp_params(alpha=1e-2)  # often helpful for noisy observations
```

Guidance:

- Use duplicates to estimate noise only when repeated coordinates are meaningful.
- Increase `alpha` for numeric stability with noisy targets.
- Preserve every noisy observation in `res`; aggregate only outside the optimizer
  if the user needs custom reporting.
- If duplicate suggestions are frequent without noise, inspect bounds and
  acquisition settings; route acquisition-specific changes to the sibling route.

## Recipe 9: Bounds Updates During A Run

Manual bounds update:

```python
optimizer.set_bounds({"x": (-1.0, 1.0)})
optimizer.maximize(init_points=0, n_iter=5)
```

Notes:

- Only existing parameter names are updated; unknown keys are ignored.
- `res` keeps all historical observations.
- `max` is selected among points valid under current bounds, so shrinking bounds
  can change `optimizer.max` even though no observation was deleted.
- Do not change a parameter from float to int/categorical or change its
  dimensionality here. Route typed/custom/domain-reduction changes to the
  advanced sibling.

## Recipe 10: Result Reporting Template

When returning optimizer results to a user, include enough context to avoid
metric-sign and state confusion:

```text
Best target: <optimizer.max['target']>
Best params: <optimizer.max['params']>
Observations: <len(optimizer.res)>
Metric sign: target = score | target = -loss, so best loss = <...>
Bounds: <pbounds used>
Random seed: <seed if set>
State saved: <path if the user requested persistence>
```

If the target is a negated loss, never call the negative value a loss without
flipping the sign back.
