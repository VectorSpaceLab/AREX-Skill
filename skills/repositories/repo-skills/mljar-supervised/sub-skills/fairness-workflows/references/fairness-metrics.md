# Fairness metrics

`AutoML` separates performance scoring from fairness scoring:

- `eval_metric` chooses the performance loss/score used to compare models in the usual AutoML search. Route generic metric/performance setup to `../../training-core/`.
- `fairness_metric` chooses the fairness criterion used when `fit(..., sensitive_features=...)` is supplied.

A ratio metric is fair when its value is greater than the threshold. A difference metric is fair when its value is lower than the threshold. MLJAR's comparisons are strict (`>` for ratios, `<` for differences), so equality with the threshold should not be treated as a pass.

## Default choices

When `fairness_metric="auto"`:

| Task | Default fairness metric | Default threshold |
| --- | --- | --- |
| Binary classification | `demographic_parity_ratio` | `0.8` |
| Multiclass classification | `demographic_parity_ratio` | `0.8` |
| Regression | `group_loss_ratio` | `0.8` |

For `group_loss_difference`, there is no automatic threshold. Provide a manual `fairness_threshold` in the units of the regression evaluation metric.

## Classification metrics

Supported for binary and multiclass classification:

| Metric name | Meaning | Fair direction | Auto threshold |
| --- | --- | --- | --- |
| `demographic_parity_difference` | Difference between the highest and lowest group selection rates. | Lower is better; fair when `< threshold`. | `0.1` |
| `demographic_parity_ratio` | Ratio of lowest to highest group selection rate. | Higher is better; fair when `> threshold`. | `0.8` |
| `equalized_odds_difference` | Larger of the group true-positive-rate gap and false-positive-rate gap. | Lower is better; fair when `< threshold`. | `0.1` |
| `equalized_odds_ratio` | Minimum of group true-positive-rate ratio and false-positive-rate ratio. | Higher is better; fair when `> threshold`. | `0.8` |

Additional notes:

- Selection rate is the fraction of samples predicted as the positive class.
- For binary classification, fairness is reported once per sensitive feature.
- For multiclass classification, AutoML converts each class into a one-vs-rest check and reports fairness per sensitive feature and per class. A column named `gender` with a target class `approved` appears as `gender__approved` in detailed fairness fields.
- If `privileged_groups` and `underprivileged_groups` are not supplied, parity metrics infer them from highest/lowest selection rates; equalized-odds metrics infer them from the largest true-positive-rate or false-positive-rate separation.
- Very small groups can create unstable ratios or divide-by-zero style values. Use adequate group counts before relying on the metric.

## Regression metrics

Supported for regression:

| Metric name | Meaning | Fair direction | Auto threshold |
| --- | --- | --- | --- |
| `group_loss_ratio` | Ratio between privileged and underprivileged group performance for the model's regression metric. | Higher is better; fair when `> threshold`. | `0.8` |
| `group_loss_difference` | Difference between underprivileged and privileged group performance for the model's regression metric. | Lower is better; fair when `< threshold`. | None; manual threshold required. |

Regression fairness is computed against the trained model's regression metric. For example, with `eval_metric="rmse"`, detailed fairness output can describe `Group Loss Ratio @ RMSE` or `Group Loss Difference @ RMSE`.

Group inference for regression depends on whether the underlying metric is lower-better or higher-better:

- For lower-better metrics such as `MAE`, `MSE`, `RMSE`, and `MAPE`, the privileged group is the group with the lower loss and the underprivileged group is the group with the higher loss.
- For higher-better metrics such as `R2`, `SPEARMAN`, and `PEARSON`, the privileged group is the group with the higher score and the underprivileged group is the group with the lower score.

## How fairness affects model ranking

AutoML stores fairness scores per model and per sensitive feature. The model-level summary uses:

- worst fairness: lowest value across sensitive features for ratio metrics, highest value across sensitive features for difference metrics;
- best fairness: highest value across sensitive features for ratio metrics, lowest value across sensitive features for difference metrics.

When at least one model is fair, the best model is selected from fair valid models by normal model performance. When no model is fair, AutoML chooses the most fair valid model instead of silently ignoring fairness.

## Choosing a metric

Use these practical defaults unless the user supplies a domain policy:

- Need parity of positive decisions across groups: start with `demographic_parity_ratio` and `0.8`.
- Need similar error behavior conditional on true labels: use an equalized-odds metric.
- Need regression performance to be similar across groups: start with `group_loss_ratio` and `0.8`.
- Need an absolute regression gap: use `group_loss_difference` only after choosing an interpretable threshold for the target scale and `eval_metric`.

Do not swap classification and regression fairness metrics. Metric/task mismatches raise validation errors once AutoML knows the ML task.
