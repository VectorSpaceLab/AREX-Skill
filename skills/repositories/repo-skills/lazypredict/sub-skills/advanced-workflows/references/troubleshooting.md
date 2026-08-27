# Advanced Workflow Troubleshooting

## `No models fitted` during explainability

**Symptoms:** `ValueError: No models fitted. Call fit() first.`

**Recovery:** run `fit()` successfully before calling `.explain()`. If the
scores table is empty, inspect `.errors` and fix the base supervised workflow
first.

## SHAP import or compatibility errors

**Symptoms:** `ModuleNotFoundError: shap`, model-specific SHAP explainer errors,
or very slow SHAP computation.

**Recovery:**

1. Use `method='permutation'` for the dependency-light explanation.
2. Install the explain extra only when SHAP is required.
3. Reduce `max_samples` for large test sets.
4. Explain one important fitted model instead of every model when the full table
   is too slow.

## Invalid tuning backend or metric

- Supervised `tune_backend` must be `optuna`, `sklearn`, or `flaml`.
- Time-series `tune_metric` must be a supported forecast metric such as `RMSE`,
  `MAE`, `MAPE`, `SMAPE`, or `MASE`.
- `horizon_strategy` must be `recursive`, `direct`, or `multi_output`.

These are constructor validation errors. Correct the argument before running a
fit loop.

## Optional tuner is missing

**Symptoms:** import errors for `optuna` or `flaml` during tuning.

**Recovery:** switch to a backend that is installed, or install the relevant
extra. For a minimal environment, `tune_backend='sklearn'` is often the fastest
way to prove the flow before adding optional tuner dependencies.

## Tuning is too slow

**Likely causes:** too many initial models, too many trials, cross-validation,
large input data, expensive optional estimators, or no timeout.

**Recovery:**

- benchmark an explicit small model list first;
- use `tune_top_k=1` or `2`;
- lower `tune_trials`;
- set `tune_timeout`;
- sample data for the first pass;
- avoid GPU/foundation/deep models unless they are the user requirement.

## Search space returns `None`

This means Lazy Predict has no built-in search space for that model name. It is
normal for dummy/baseline models. Choose a different model, supply a manual
search outside Lazy Predict, or skip tuning for that row.

## Permutation importance is noisy

Permutation importance can vary with small test sets and stochastic models. Use
consistent `random_state`, increase `n_repeats` when budget allows, and compare
relative patterns rather than over-interpreting tiny differences.
