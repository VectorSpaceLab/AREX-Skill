# Reporting and explainability

MLJAR AutoML creates human-readable and machine-readable documentation for each run. Reports are generated from the saved `results_path` state, so load the whole AutoML directory before report extraction.

## Human report: `report()`

```python
automl = AutoML(results_path="AutoML_run")
automl.report()
```

`report()` builds `README.html` from the top-level `README.md` and model-level `README.md` files when the HTML report is missing, then returns an IPython display object. It is most useful in notebooks or environments that can render HTML. The Markdown reports remain available in `results_path` for text review.

Use the top-level `README.md` for:

- AutoML leaderboard and best-model marker.
- Metric type and metric values.
- Training time per model.
- Fairness certificate section when fairness-aware training was used.
- Links to model-specific report directories.

Use a model directory's `README.md` for:

- Model-specific metrics and threshold details.
- Learning curves.
- Coefficients, tree visualization, permutation importance, and SHAP sections when generated.
- Fairness details for that model when fairness-aware training was used.

## Machine-readable report: `report_structured(...)`

```python
markdown = automl.report_structured()
compact = automl.report_structured(format="dict")
json_text = automl.report_structured(format="json")
model_md = automl.report_structured(model_name="1_Baseline")
model_dict = automl.report_structured(format="dict", model_name="1_Baseline")
```

Allowed `format` values are exactly `"markdown"`, `"dict"`, and `"json"`. Any other format raises an error. If `model_name` is provided, it must exactly match a saved model name from the leaderboard; otherwise an AutoML exception reports the available names.

Every call builds the full structured payload and writes `report_structured.json` under `results_path`. The returned object is intentionally compact:

| Call | Return type | Typical returned fields |
| --- | --- | --- |
| `report_structured()` | Markdown string | Leaderboard, global feature importance when available, fairness summary when available, automation disclosure. |
| `report_structured(format="dict")` | Python dict | `created_at_utc`, `mljar_supervised_version`, `results_path`, `leaderboard`, `global_feature_importance`, `fairness_summary`. |
| `report_structured(format="json")` | JSON string | JSON serialization of the compact dict view. |
| `report_structured(..., model_name=name)` | Markdown/dict/json for one selected model | Selected model summary, hyperparameters, metric details, feature importance, and fairness details when available. |

The saved `report_structured.json` contains the full payload, including run summary, best model, all model records, and artifact paths. That file is useful for offline audit, reproducibility notes, or summarization by a downstream tool.

## Structured report field guide

Common compact fields:

- `leaderboard`: list of rows matching `get_leaderboard(original_metric_values=True)`.
- `global_feature_importance`: averaged feature-importance ranking across models when permutation-importance files are available; otherwise an unavailable reason.
- `fairness_summary`: present only for fairness-aware runs. It includes metric name, threshold, best-model fairness status, sensitive-feature values, and certificate information when generated. Interpret fairness semantics with `fairness-workflows`.
- `results_path`: path string embedded in the report. Treat this as runtime metadata; it may be local to the machine that generated the report.

Common model-specific fields:

- `selected_model.name`, `model_type`, `metric_type`, `metric_value`, `train_time`, `is_valid`, `is_stacked`.
- `hyperparameters`: learner/model parameters when extractable; ensembles may only expose a model-type fallback.
- `metrics`: additional classification/regression details such as confusion matrix, threshold, max metrics, and fairness metric details when available.
- `feature_importance`: top and worst features by permutation importance when `*_importance.csv` files exist.
- `artifacts`: model report paths for `README.md` and `README.html` plus the model directory.

## Choosing `model_name`

Start from the leaderboard instead of guessing:

```python
payload = automl.report_structured(format="dict")
model_names = [row["name"] for row in payload["leaderboard"]]
name = model_names[0]
details = automl.report_structured(format="dict", model_name=name)
```

Model names often include run order and algorithm name, for example `1_Baseline`, `1_DecisionTree`, `1_Default_Xgboost`, `Ensemble`, or `Stacked_Ensemble`. Names are case-sensitive and must match the saved artifacts.

## Explain levels and artifact expectations

`explain_level` controls which extra files and report sections are created:

| `explain_level` | Expected explanations | Typical artifacts |
| --- | --- | --- |
| `0` | No importance, SHAP, tree, or coefficient explanations. Learning curves are still produced. | `learning_curves.png`; basic reports and model files. |
| `1` | Learning curves plus permutation importance; decision-tree visualizations for decision trees; coefficients for linear models. | `*_importance.csv`, `permutation_importance.png`, `*_tree.svg`, `*_coefs.csv` when supported. |
| `2` | Everything from level 1 plus SHAP outputs where supported. | `*_shap_importance.csv`, `shap_importance.png`, `*_shap_dependence*.png`, `*_shap_*decisions.png`. |

Important caveats:

- SHAP is not generated for every algorithm; Baseline, Neural Network, and CatBoost are excluded by package behavior.
- SHAP can be skipped for data-size or dependency limitations.
- Decision-tree SVG rendering needs optional visualization support. If the system Graphviz `dot` executable is absent, tree files may be missing even when the Python packages import.
- `explain_level=0` is the safest setting for smoke tests and production checks where report structure matters but explanations are not required.
- `Compete` and `Optuna` modes usually prioritize performance and may produce fewer explanations by default than `Explain` mode.

## Fairness sections in reports

When fairness-aware training is used, report surfaces can include:

- Fairness columns in `get_leaderboard()` and `leaderboard.csv`.
- A top-level Fairness Certificate section in `README.md`.
- `fairness_summary` in `report_structured(format="dict")`.
- Model-specific fairness fields and certificate details in `report_structured(..., model_name=...)`.

This sub-skill can locate those fields and explain how to extract them. Route metric choice, group definitions, threshold interpretation, and mitigation behavior to `fairness-workflows`.

## Minimal extraction recipe

```python
from supervised import AutoML

run = AutoML(results_path="AutoML_run")
leaderboard = run.get_leaderboard(original_metric_values=True)
compact = run.report_structured(format="dict")

first_model = compact["leaderboard"][0]["name"] if compact["leaderboard"] else None
if first_model:
    model_details = run.report_structured(format="dict", model_name=first_model)

print(leaderboard[["name", "model_type", "metric_type", "metric_value"]])
```
