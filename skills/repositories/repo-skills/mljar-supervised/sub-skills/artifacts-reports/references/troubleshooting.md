# Troubleshooting artifacts and reports

Use this guide when a saved run will not load, prediction after load fails, reports are missing or too sparse, or explainability artifacts do not match expectations.

## Result directory conflict

**Symptom**: creating or fitting `AutoML(results_path="...")` fails with a message like the directory is not empty.

**Cause**: `results_path` exists, has files, but is not recognized as a trained AutoML directory because `params.json` is absent.

**Fix**:

1. If this is a new run, choose a fresh directory or empty the intended directory deliberately.
2. If this is an existing run, verify `params.json` is present at the top level.
3. Do not point `results_path` at a parent folder that merely contains an AutoML run as a child.
4. For bundled smoke scripts, use a temporary directory or pass an explicit overwrite flag only for directories you are willing to replace.

Route training-output naming and fresh-run settings to `training-core`.

## Stale or inconsistent `params.json`

**Symptom**: the run loads partially, leaderboard/report information is inconsistent, or prediction fails after files were moved or edited.

**Facts**:

- The loader treats the directory you pass to `AutoML(results_path=...)` or `load(path)` as the actual loaded path, even if the serialized `results_path` value inside `params.json` is stale.
- `params.json` still must contain coherent model metadata such as `saved`, `best_model`, `load_on_predict`, `stacked`, and `fit_level` when those are needed.
- Top-level `data_info.json` and model folders must stay consistent with `params.json`.

**Fix**:

1. Restore the complete saved directory from backup if files were edited or only partially copied.
2. Prefer retraining or rerunning the interrupted AutoML process over hand-editing `params.json`.
3. If only the serialized `results_path` value differs after moving a complete directory, try loading with the new directory path and running a small `predict_all` check.
4. If `saved` or `best_model` references directories that no longer exist, recover those directories or retrain.

## Loading learner files instead of the AutoML object

**Symptom**: a user tries to open a learner file as JSON, load a CatBoost/XGBoost/LightGBM file directly, or instantiate a backend estimator and gets wrong predictions or missing preprocessing.

**Fix**:

Use the public AutoML run directory:

```python
from supervised import AutoML

automl = AutoML(results_path="AutoML_run")
y_pred = automl.predict(X_new)
```

Only inspect backend learner files for advanced backend-specific analysis. They are not a replacement for the AutoML object's preprocessing, target encoders, thresholds, ensemble/stacked-model logic, or class-label handling.

## Missing model files needed for prediction

**Symptom**: `AutoML(results_path=...)` loads but `predict`, `predict_proba`, or `predict_all` fails; an ensemble or stacked model reports missing dependencies.

**Likely causes**:

- The best model folder was copied without its component model folders.
- `Ensemble/ensemble.json` or `Stacked_Ensemble/ensemble.json` is missing.
- A model directory is present but missing `framework.json` or learner files.
- `data_info.json` is missing from the top level.
- Files were renamed manually.

**Fix**:

1. Inspect the best model from `params.json` or `get_leaderboard()`.
2. Use `automl.models_needed_on_predict(model_name)` to list required dependencies.
3. Confirm each required model folder exists under `results_path`.
4. For each non-ensemble model, keep its framework metadata, preprocessing metadata, learner files, and model report files together.
5. For ensembles, keep the ensemble folder and every selected component model folder.
6. Re-copy the entire original `results_path` directory if any dependency is uncertain.

## `predict_proba` fails

**Symptom**: `predict_proba()` raises an exception on a regression run.

**Cause**: probabilities are only available for classification tasks.

**Fix**: use `predict()` or `predict_all()` for regression. Route task selection and prediction API choice to `training-core` if the run's task type is unclear.

## Missing or sparse `report()` output

**Symptom**: `automl.report()` does not show an expected HTML report, or `README.html` is absent.

**Fix**:

1. Confirm the run is fitted or loadable from a complete `results_path`.
2. Call `automl.report()`; it creates `README.html` when it is missing.
3. If running outside a notebook, inspect `README.md` and model-level `README.md` directly or open `README.html` in a browser.
4. If model directories lack `README.md`, the run may be incomplete or corrupted.

## Wrong `report_structured` format

**Symptom**: `report_structured(format="html")`, `format="md"`, or another spelling fails.

**Fix**: use exactly one of:

```python
automl.report_structured(format="markdown")
automl.report_structured(format="dict")
automl.report_structured(format="json")
```

The default is `"markdown"`.

## Wrong `model_name`

**Symptom**: `report_structured(model_name="...")` raises an exception listing available models.

**Fix**:

```python
payload = automl.report_structured(format="dict")
print([row["name"] for row in payload["leaderboard"]])
```

Use an exact name from the leaderboard. Model names are case-sensitive and include run-order prefixes such as `1_` when created by AutoML.

## `report_structured` says the model is not fitted

**Symptom**: report extraction raises a not-fitted error.

**Fix**:

1. Confirm `results_path` points to the AutoML run directory, not to a model subfolder.
2. Confirm `params.json`, `data_info.json`, and at least one saved model are present.
3. Load with `AutoML(results_path="AutoML_run")` and run `get_leaderboard()` before report extraction.
4. If the directory is an interrupted run with no finished model, resume/retrain rather than forcing a report.

## Absent SHAP, permutation importance, tree, or coefficient files

**Symptom**: expected explanation files are missing from model folders or structured reports say feature importance is unavailable.

**Common explanations**:

- `explain_level=0`: no permutation importance, SHAP, tree, or coefficient outputs are expected.
- `explain_level=1`: permutation importance is expected when supported, but SHAP is not.
- `explain_level=2`: SHAP is attempted when supported, but not all algorithms support it.
- Baseline, Neural Network, and CatBoost do not produce SHAP outputs in this package's SHAP path.
- Decision-tree SVG files need optional visualization support; missing Graphviz `dot` can prevent tree rendering.
- Very small, very wide, failed, or interrupted model runs can skip some explanations.

**Fix**:

1. Check the run's `explain_level` in `params.json` or the AutoML constructor used for training.
2. Check the algorithm/model type before expecting SHAP or coefficients.
3. Use `report_structured(format="dict")` and inspect `global_feature_importance.available` and unavailable reasons.
4. For tree visualization, install system Graphviz and retry training/report generation when tree SVGs are required.
5. For fast verification, deliberately use `explain_level=0` and assert report structure rather than explanation files.

## Fairness report fields appear but are hard to interpret

**Symptom**: leaderboard/report includes `fairness_metric`, `fairness_<feature>`, `is_fair`, `fairness_summary`, or Fairness Certificate fields, but the group semantics or threshold interpretation is unclear.

**Fix**: this sub-skill can extract and locate those fields. Route metric meaning, threshold choice, privileged/underprivileged group handling, and sensitive-feature setup to `fairness-workflows`.

## Moving directories breaks links or paths in reports

**Symptom**: after moving a run, Markdown links or structured-report path strings point to the old location, or some model links are broken.

**Fix**:

1. Keep the relative structure of the run directory unchanged.
2. Load using the new top-level directory path; the loader uses that path for runtime model loading.
3. Regenerate HTML with `automl.report()` if `README.html` contains stale rendered links.
4. Regenerate `report_structured.json` with `automl.report_structured(format="dict")` if a machine-readable report should contain fresh path strings.
5. Avoid moving only selected model folders; move the complete `results_path` directory.

## Joblib or backend version mismatch on load

**Symptom**: loading a model folder fails with a message about joblib or backend-library versions.

**Cause**: saved model metadata records dependency versions, and binary learner files can be sensitive to package versions.

**Fix**:

1. Load with a compatible `mljar-supervised` runtime when possible.
2. Keep dependency versions close to the environment that trained the model, especially for joblib-backed scikit-learn models and native boosting libraries.
3. If compatibility cannot be restored, retrain the AutoML run in the current environment.
