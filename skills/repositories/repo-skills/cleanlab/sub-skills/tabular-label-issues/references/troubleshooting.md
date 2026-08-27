# Troubleshooting

## Route mistakes

- If the data is standard binary or multiclass classification, route to `classification` instead of this sub-skill.
- If you want a single dataset audit across multiple issue families, route to `datalab`.
- If the task is token classification, object detection, or segmentation, route to `structured-label-issues`.
- If the task is multiannotator consensus or standalone outlier scoring, route to `multiannotator` or `outlier`.

## Multilabel troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `labels` validation fails | You passed a multi-hot matrix, strings, or scalar labels. | Convert labels to a list of lists of zero-based class IDs. |
| Scores look wrong or the wrong class is flagged | `pred_probs` columns are out of order, missing a class, or came from a multiclass softmax. | Keep `pred_probs` shape `(N, K)` and align columns with class IDs `0..K-1`. |
| Examples with no labels fail | You used `None` instead of an empty list. | Represent no labels as `[]`. |
| `pred_probs` rows sum to 1 | You may have used multiclass probabilities instead of multilabel probabilities. | Use independent one-vs-rest probabilities; rows do not need to sum to 1. |
| Direct multilabel output and Datalab output disagree | You may be mixing class-order conventions or reading the wrong result field. | Check the class order before aligning `pred_probs`, and remember Datalab uses `label_score`. |
| `return_indices_ranked_by` did not give a mask | That is expected. | Use the mask form only when `return_indices_ranked_by=None`. |

## Regression troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `get_label_quality_scores` raises a validation error | `labels` or `predictions` are not numeric 1D arrays of the same length. | Convert both to numeric 1D arrays and keep them aligned. |
| `CleanLearning.fit` complains about `sample_weight` | The wrapped model does not accept `sample_weight`, or the vector length is wrong. | Pass `sample_weight` directly to `fit(...)` and use a compatible estimator. |
| `CleanLearning` cannot clone the model | The estimator is not sklearn-clonable. | Implement `get_params()` or use `rank.get_label_quality_scores` with precomputed predictions. |
| `find_label_issues` fails on a tiny dataset | There are too few examples for the chosen cross-validation settings. | Lower `cv_n_folds` or use more data. |
| `uncertainty` shape error | The uncertainty vector length does not match `y`. | Pass a scalar or a length-N vector. |
| `label_quality` and `label_score` do not match | You are comparing direct regression output to Datalab output. | Direct `CleanLearning` uses `label_quality`; Datalab uses `label_score`. |

## Workflow reminders

- If you already have out-of-sample predictions and no useful regression model, use `rank.get_label_quality_scores` instead of `CleanLearning`.
- If you want a broader dataset audit, switch to `Datalab(task="regression")` or `Datalab(task="multilabel")`.
- If you need standard noisy-label cleanup for multiclass classification, switch to `classification`.
