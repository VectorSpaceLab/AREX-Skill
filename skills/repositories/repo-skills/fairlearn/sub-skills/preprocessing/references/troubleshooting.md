# Preprocessing troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `CorrelationRemover` says a sensitive column is missing | `sensitive_feature_ids` names/indices do not exist in `X`. | For DataFrames, pass exact column names. For arrays, pass valid integer indices. |
| `transform` says feature count differs from fit | The test matrix has different columns/order than the training matrix. | Apply the same preprocessing and column selection before `transform`; keep DataFrame column order stable. |
| Downstream estimator sees fewer columns than expected | `CorrelationRemover` drops sensitive columns from its output. | Refit the downstream estimator on the transformed matrix; do not expect original sensitive columns to remain. |
| Decorrelated data still has unfair outcomes | Linear correlation removal is not enough for the chosen harm/metric. | Use assessment to quantify remaining disparity; consider reductions, postprocessing, or adversarial methods. |
| `PrototypeRepresentationLearner` is slow or unstable | Non-convex optimization, too many prototypes, large `max_iter`, poorly scaled inputs. | Scale numeric inputs, lower `n_prototypes`, set `random_state`, tune `max_iter`/`tol`, and start with the smoke script. |
| `PrototypeRepresentationLearner` result ignores labels or groups | `y` or `sensitive_features` was omitted or misaligned. | Pass `y` and `sensitive_features` to `fit`/`fit_transform` and verify lengths. |
| Output quality varies across runs | Random initialization. | Set `random_state` and record parameter values in the report. |
| User wants a fairness-constrained estimator rather than a transformed feature matrix | Wrong mitigation family. | Route to `../reductions/` for constrained retraining or `../postprocessing/` for threshold adjustment. |

## Minimal shape diagnostic

```python
print(X_train.shape, X_test.shape)
print(getattr(X_train, "columns", None))
print(len(y_train), len(A_train))
Z = transformer.fit_transform(X_train, y_train, sensitive_features=A_train)
print(Z.shape)
```

For `CorrelationRemover`, omit `sensitive_features` from `fit_transform`; sensitive columns are identified inside `X` through `sensitive_feature_ids`.
