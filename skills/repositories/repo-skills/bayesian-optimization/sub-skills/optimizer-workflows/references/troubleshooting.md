# Optimizer Troubleshooting

Use this file when a core `BayesianOptimization` workflow fails or produces
surprising results. Each entry lists the likely cause and concrete fixes.

## `ValueError: Parameters' keys ... do not match the expected set of keys`

Symptoms:

- `register()`, `probe()`, `predict()`, or internal conversion fails with a key
  mismatch error.
- The objective receives missing or unexpected keyword arguments.

Likely causes:

- `pbounds` names differ from the objective function parameter names.
- A dict passed to `register()`/`probe()`/`predict()` has an extra key or is
  missing a required key.
- An HPO wrapper renamed a hyperparameter but `pbounds` was not updated.

Fix:

```python
import inspect

expected = set(pbounds)
actual = set(inspect.signature(objective).parameters)
assert expected == actual
assert set(params) == expected
```

Prefer dict inputs over arrays so names are explicit. If arrays are required,
remember that array order follows `pbounds` insertion order.

## Duplicate Point Raises `NotUniqueError`

Symptoms:

- `bayes_opt.exception.NotUniqueError: Data point ... is not unique` during
  `register()` or repeated manual evaluations.

Likely causes:

- The same coordinates were registered twice.
- A manual ask-tell worker returned a stale suggestion.
- Bounds are too narrow or acquisition behavior revisits a point.
- The objective is noisy but duplicates were not enabled.

Fix:

- If the duplicate is accidental, skip it, request a fresh `suggest()`, or widen
  bounds.
- If repeated noisy evaluations are intentional, construct the optimizer with
  `allow_duplicate_points=True` from the start and consider
  `optimizer.set_gp_params(alpha=1e-2)`.
- Do not toggle duplicate policy by editing state files; recreate a compatible
  optimizer and rerun or reload intentionally.

## `predict(..., fit_gp=True)` Fails With Zero Observations

Symptoms:

- `RuntimeError: The Gaussian Process model cannot be fitted with zero observations...`

Likely causes:

- `predict()` was called before any `register()`, eager `probe()`, or
  `maximize()` observation.
- A manual ask-tell loop called `suggest()` but never registered the result.

Fix:

```python
if len(optimizer.res) == 0:
    # Either run/evaluate at least one point...
    params = optimizer.suggest()
    target = external_evaluate(**params)
    optimizer.register(params, target)

mean, std = optimizer.predict(params, return_std=True, fit_gp=True)
```

For a parser or prior-only smoke check, call `predict(..., fit_gp=False)`, but
do not interpret prior predictions as learned objective behavior.

## Prediction Shape Is Not What The User Expected

Symptoms:

- A single-point prediction returns a scalar-like object but code expects a
  length-1 array.
- `return_cov=True` returns a 2D covariance matrix.
- `ValueError: return_std and return_cov cannot both be True`.

Likely causes:

- Passing a dict versus a list of dicts changes return shape.
- Both uncertainty modes were requested.

Fix:

- Use a dict for scalar-like output: `optimizer.predict({"x": 0.1})`.
- Use a list for array output: `optimizer.predict([{"x": 0.1}])`.
- Choose exactly one uncertainty mode: `return_std=True` for per-point standard
  deviations or `return_cov=True` for full covariance.

## Objective Appears To Optimize The Wrong Direction

Symptoms:

- `optimizer.max` reports a high loss or a poor model.
- HPO results get worse as the target improves.

Likely causes:

- The objective returned a loss directly even though the optimizer maximizes.
- A scikit-learn metric was misunderstood (`neg_log_loss` is already negated).
- Reporting code forgot to flip `-loss` back to positive loss.

Fix:

```python
def objective(...):
    loss = compute_loss(...)
    return -float(loss)

best_target = optimizer.max["target"]
best_loss = -best_target
```

For scorer strings, check whether larger is better. `accuracy`, `roc_auc`, and
estimator `.score()` can be returned directly. Positive losses must be negated.

## `f=None` Misuse

Symptoms:

- `ValueError: No target function has been provided.`
- `maximize()` fails in a manual/distributed workflow.
- `probe(..., lazy=False)` fails.

Likely causes:

- The optimizer was constructed with `f=None` for ask-tell, but code called a
  method that tries to evaluate the objective internally.

Fix:

Use only this loop:

```python
optimizer = BayesianOptimization(f=None, pbounds=pbounds, random_state=1)
params = optimizer.suggest()
target = external_evaluate(**params)
optimizer.register(params=params, target=float(target))
```

If you want `maximize()` or eager `probe()`, recreate the optimizer with a real
callable `f`.

## State Load Gives Stale, Incompatible, Or Surprising Results

Symptoms:

- `load_state()` fails while registering saved points.
- Loaded optimizer has unexpected `max`, suggestions, or bounds.
- Continuing from a state file repeats work or uses wrong objective sign.

Likely causes:

- New optimizer was constructed with incompatible `pbounds`, objective signature,
  acquisition function, constraint, bounds transformer, or duplicate policy.
- State was loaded into an optimizer that already had observations.
- The objective code or metric sign changed after saving.
- Bounds were changed before saving but the resumed optimizer was created with
  stale bounds.

Fix:

1. Create a fresh optimizer before loading.
2. Recreate the same compatible constructor objects.
3. Validate immediately:

```python
loaded.load_state(state_path)
assert len(loaded.res) == expected_count
assert loaded.max is None or set(loaded.max["params"]) == set(pbounds)
```

4. If reproducibility matters, compare the next `suggest()` from the original
   and loaded optimizers in a controlled test.
5. Keep experiment metadata outside the state file: objective code version,
   data version, target sign, and model library versions.

## Bounds Update Did Not Work Or Changed `max`

Symptoms:

- `set_bounds({"unknown": (...)})` appears to do nothing.
- `optimizer.max` changes after shrinking bounds even though no observations
  were removed.
- A `ValueError` mentions parameter type or dimensions.

Likely causes:

- Unknown keys are ignored by `set_bounds()`.
- Historical observations outside new bounds remain in `res` but are invalid for
  `max` selection.
- The update attempted to change a float parameter into an int/categorical
  parameter or changed dimensionality.

Fix:

```python
assert set(new_bounds).issubset(set(pbounds))
optimizer.set_bounds(new_bounds)
for name, (lo, hi) in new_bounds.items():
    assert lo < hi
```

Do not use `set_bounds()` to rename parameters, add parameters, or change types.
Route typed/custom/domain-reduction changes to `../../advanced-domain-features/SKILL.md`.

## Slow Or Expensive Objective Burns Budget

Symptoms:

- Smoke run takes too long.
- HPO job launches too many cross-validation fits.
- User cannot tell whether the setup is correct before a long run.

Likely causes:

- Defaults `maximize(init_points=5, n_iter=25)` are too large for the objective.
- CV folds, dataset size, estimator count, or parallelism are excessive.
- Objective performs data loading or preprocessing every call.

Fix:

- First run `init_points=1` or `2` and `n_iter=1` or `2`.
- Cache data/preprocessing outside the objective wrapper.
- Use synthetic or small stratified samples for diagnostics.
- Set estimator budgets low and `n_jobs=1` in smoke scripts.
- Increase budget only after `optimizer.max`, `optimizer.res`, and metric sign
  pass validation.

## Non-Finite Targets Or Model Failures

Symptoms:

- GP fitting emits numerical warnings.
- `maximize()` fails after a model configuration throws an exception.
- Target history contains `nan` or infinities.

Likely causes:

- Objective returned `nan`, `inf`, a tensor, an array, or an exception escaped.
- HPO wrapper allowed invalid integer/categorical/model settings.
- Bounds include invalid regions such as zero for a log transform.

Fix:

```python
def objective(...):
    try:
        score = compute_score(...)
        score = float(score)
        if not math.isfinite(score):
            return -1e12
        return score
    except RecoverableModelError:
        return -1e12
```

Prefer narrowing bounds after diagnosing repeated invalid regions. Do not hide
systemic errors such as missing dependencies or bad data; fix those before BO.

## `random_sample` Or `suggest` Values Look Out Of Order

Symptoms:

- Array inputs map to the wrong parameter names.
- A user expected alphabetical order but got insertion order.

Likely causes:

- `TargetSpace.keys` is `list(pbounds.keys())`, preserving dict insertion order.

Fix:

- Use dicts for `probe`, `register`, and `predict`.
- If arrays are necessary, build `pbounds` in the intended order and document
  that order next to the array conversion.

## Logger Output Is Missing Or Too Verbose

Symptoms:

- No optimization table appears.
- Every row prints and clutters logs.
- Only some rows print.

Likely causes:

- `verbose` setting controls the screen logger.

Fix:

- `verbose=0`: silent, best for scripts and tests.
- `verbose=1`: print only rows that establish a new maximum.
- `verbose=2`: print all logged optimization steps.

Logger output is presentation only; use `optimizer.max` and `optimizer.res` for
programmatic validation.
