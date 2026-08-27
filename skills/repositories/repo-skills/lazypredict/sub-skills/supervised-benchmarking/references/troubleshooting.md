# Supervised Troubleshooting

## Model table is empty or missing important estimators

**Symptoms:** `scores` is empty, a named model is absent, or only very simple
models appear.

**Likely causes:** all selected models failed, `timeout` was too strict, an
optional dependency is missing, or `ignore_warnings=True` suppressed errors.

**Recovery:**

1. Inspect `estimator.errors` after `fit()`.
2. Re-run with an explicit small model list and `ignore_warnings=False`.
3. Install only the optional dependency needed by the missing model family.
4. Increase `timeout` or use smaller data for the first benchmark.

## Constructor validation errors

- `cv=1` is invalid; use `None` or an integer `>= 2`.
- `timeout <= 0` is invalid; use `None` or a positive number.
- `categorical_encoder` must be one of `onehot`, `ordinal`, `target`, `binary`.
- `n_jobs` must be an integer or `None`.
- `max_models` must be a positive integer.
- `tune_backend` must be `optuna`, `sklearn`, or `flaml`.

Fix the constructor before debugging model behavior.

## Data shape errors

**Symptoms:** messages like `X_train has ... samples but y_train has ...`,
`X_test has ... samples but y_test has ...`, or train/test feature counts differ.

**Recovery:** print the four shapes immediately before `fit()`. Recreate the
split so train/test matrices have the same feature columns and target vectors
match row counts. For pandas DataFrames, align column order between train and
test before passing them to Lazy Predict.

## Target or binary categorical encoders fail

**Symptoms:** import errors involving `category_encoders` or encoder construction
failures.

**Likely cause:** `target` and `binary` encoders require the optional
`category_encoders` package, while `onehot` and `ordinal` work with base
dependencies.

**Recovery:** install `category_encoders` in the active Python environment, or
switch to `categorical_encoder="onehot"` for the first pass.

## ROC-AUC seems lower than expected

Lazy Predict computes classifier ROC-AUC using probabilities when available and
falls back through decision scores or class labels when needed. Some estimators
do not expose calibrated probabilities. Compare a single fitted pipeline's
`predict_proba` or `decision_function` behavior before treating ROC-AUC as a
package error.

## GPU requested but not used

`use_gpu=True` only adds GPU parameters for supported optional model families
when CUDA appears available. Base sklearn estimators remain CPU-bound. For a
hard GPU requirement, verify the relevant optional package and framework first:
XGBoost, LightGBM, CatBoost, cuML, or PyTorch CUDA depending on the requested
model.

## Save/load problems

- `save_models()` raises `ValueError` before `fit()` because there are no fitted
  pipelines.
- `load_models()` raises `FileNotFoundError` for a missing directory.
- Loaded joblib pipelines depend on compatible versions of scikit-learn, pandas,
  numpy, Lazy Predict, and any optional estimator packages.

When portability matters, save the package versions next to model artifacts and
reload in a matching environment.

## Slow runs

Running `"all"` trains many estimators and may cross-validate them. Use these
controls in order:

1. explicit `classifiers=[...]` or `regressors=[...]`;
2. `max_models` for smoke tests;
3. `timeout` for per-model guardrails;
4. smaller input samples for the first leaderboard;
5. `cv=None` until the quick train/test pass looks sane.
