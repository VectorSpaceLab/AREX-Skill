# Fairness troubleshooting

Use this page for fairness-specific failures. For general fitting, result-path, and dependency issues, route to `../../training-core/`, `../../artifacts-reports/`, or the root troubleshooting reference.

## Wrong metric name

Symptom:

- `ValueError` says a metric is not allowed.
- A typo such as `demographic_parity`, `equal_odds_ratio`, or `group_loss` was passed.

Fix:

- For classification, use exactly one of `demographic_parity_difference`, `demographic_parity_ratio`, `equalized_odds_difference`, or `equalized_odds_ratio`.
- For regression, use exactly `group_loss_difference` or `group_loss_ratio`.
- `fairness_metric="auto"` is valid and chooses a task-specific default.

## Metric/task mismatch

Symptom:

- A classification metric is used with a regression target, or a group-loss metric is used with classification.
- AutoML fails after task inference or after `ml_task` is fixed manually.

Fix:

- Set `ml_task` explicitly when the target is ambiguous.
- Use classification fairness metrics for `binary_classification` and `multiclass_classification`.
- Use group-loss metrics for `regression`.
- Remember that `eval_metric` and `fairness_metric` are separate; changing one does not make the other task-compatible.

## `group_loss_difference` without a manual threshold

Symptom:

- AutoML raises an exception saying it cannot set a default fairness threshold.

Cause:

- Absolute group-loss differences depend on the scale of the regression target and the chosen regression `eval_metric`.

Fix:

- Provide `fairness_threshold=<float>` explicitly.
- Choose the threshold in the units of the metric, such as RMSE dollars, MAE minutes, or MAPE fraction.
- If no domain-specific threshold is available, use `group_loss_ratio` first.

## `sensitive_features` shape, index, or name issues

Symptoms:

- Training fails during input validation.
- Fairness fields are absent from reports.
- Privileged/underprivileged group dictionaries do not appear to affect results.

Fix:

- Pass `sensitive_features` to `fit()`, not only fairness constructor arguments.
- Split `X`, `y`, and `sensitive_features` together so their rows remain aligned.
- Ensure the number of rows in `sensitive_features` matches `X` and `y` after dropping or filtering rows.
- Prefer a pandas `DataFrame` with stable column names. Group declarations use those column names, for example `[{"gender": "male"}]`.
- If passing a NumPy array, expect generated names; do not use human-readable group dictionaries unless you convert to a DataFrame first.
- After rows with missing targets are removed, AutoML resets indices. That is fine as long as the input row order was aligned before `fit()`.

## Multiple sensitive features

Symptoms:

- More fairness columns appear than expected.
- The model is marked unfair because one sensitive feature or one intersection is poor.
- A group declaration seems to apply to only one column.

Fix:

- Expect one fairness value per sensitive feature in binary/regression tasks, and one per sensitive feature per target class in multiclass tasks.
- Bias mitigation considers intersections of sensitive feature values when computing sample weights, so sparse intersections can be unstable.
- Provide group dictionaries for each column that needs manual treatment, for example `[{"gender": "male"}, {"region": "urban"}]`.
- If an additional sensitive column is only exploratory, run a separate fit or lower-stakes analysis instead of mixing it into the fairness optimization.

## Privileged and underprivileged group definitions

Symptoms:

- Reported privileged/underprivileged values differ from the user's policy.
- Auto-selected groups are surprising.
- Group declarations are silently ignored for a column.

Fix:

- Use exact sensitive-feature column names and exact group values after preprocessing/binning.
- Set both `privileged_groups` and `underprivileged_groups` when policy requires fixed groups.
- Leave groups as `"auto"` only when metric-driven inference is acceptable.
- For numeric sensitive features, pre-bin manually before `fit()` if the auto two-bin split would create unclear group labels.
- Check detailed structured-report fairness metrics to confirm which values were used.

## Fairness-performance tradeoffs

Symptoms:

- The selected model is less accurate than a leaderboard competitor.
- Stacking is skipped.
- No model is marked fair, but a best model is still selected.

Cause:

- With fairness active, AutoML prioritizes fair models first. If no model meets the threshold, it selects the most fair valid model.
- Tight thresholds or sparse sensitive groups can make a high-performing model fail fairness.
- Stacking can use only fair base models and may be skipped when no fair base model exists.

Fix:

- Compare `metric_value`, fairness columns, and `is_fair` together.
- Use a threshold backed by policy or domain requirements; do not lower it just to improve performance without recording the tradeoff.
- Increase data volume or rebalance group representation when fairness estimates are unstable.
- Try more algorithms or a larger time budget through `../../training-core/` only when the user accepts the runtime cost.

## Network or dataset-example failures

Symptoms:

- An Adult, ACS, Crime, Drug, Housing, or LawSchool fairness recipe tries to fetch data or read a local CSV.
- A tutorial-style snippet fails because the dataset is unavailable.

Fix:

- Treat those as reference-only patterns, not runtime checks.
- Ask the user for a local dataset path if they want to train on the real dataset.
- For package/API sanity checks, run `../scripts/fairness_smoke.py`, which uses synthetic data only.

## Fairness fields missing from `report_structured()`

Symptoms:

- `fairness_summary` is `None` or absent.
- Leaderboard has no `fairness_metric`, `fairness_<feature>`, or `is_fair` columns.

Fix:

- Confirm `fit(..., sensitive_features=S)` was called.
- Confirm at least one model finished successfully.
- Use `report_structured(format="dict", model_name=<leaderboard model name>)` to inspect selected-model details.
- Route generic structured-report format and model-name errors to `../../artifacts-reports/`.

## Fairness certificate missing

Symptoms:

- Fairness metrics exist, but certificate fields are `None`.

Fix:

- A certificate is added only when fairness details are available and the model is fair.
- If `is_fair` is false, inspect `worst_fairness`, `fairness_threshold`, and per-feature fairness details instead of treating certificate absence as a report failure.
