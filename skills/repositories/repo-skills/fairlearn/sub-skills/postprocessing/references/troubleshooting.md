# Postprocessing troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: The base estimator cannot be None` | `ThresholdOptimizer` was constructed without `estimator`. | Pass a sklearn-compatible estimator. If already fitted, set `prefit=True`; otherwise leave `prefit=False`. |
| Warning about `prefit=True` and not-fitted estimator | Base estimator is not recognized as fitted or was cloned. | Use `prefit=False` unless you deliberately fitted the estimator and are not using cross-validation cloning. |
| Invalid constraint/objective error | Objective is not supported for the chosen constraint. | Use `accuracy_score` or `balanced_accuracy_score` for `equalized_odds`; check the workflow reference table. |
| Error says relaxed constraints are not supported for equalized odds | `tol` was set with `constraints="equalized_odds"`. | Remove `tol` or choose a simple constraint that supports relaxation. |
| Predictions are not reproducible | `ThresholdOptimizer.predict` may randomize according to interpolation probabilities. | Pass `random_state` to `predict` when producing a report. |
| `predict_method="predict_proba"` fails | Base estimator lacks `predict_proba` or its output is not binary-class probability shaped. | Use `decision_function`, `predict`, or a different base estimator. |
| `plot_threshold_optimizer` raises matplotlib install error | Matplotlib is missing. | Install `matplotlib` and rerun the smoke script with `--plot`. |
| Multi-column sensitive features fail or produce surprising groups | Postprocessor data reformatting can be stricter than assessment. | Start with one named sensitive feature; verify shape and group counts before using multiple columns. |
| User wants fair retraining rather than threshold adjustment | Wrong mitigation family. | Route to `../reductions/` or `../adversarial/` depending on the estimator type. |

## Minimal diagnostic

```python
print(hasattr(estimator, "predict_proba"), hasattr(estimator, "decision_function"), hasattr(estimator, "predict"))
print(len(X_train), len(y_train), len(A_train))
optimizer = ThresholdOptimizer(estimator=estimator, constraints="demographic_parity", predict_method="auto")
optimizer.fit(X_train, y_train, sensitive_features=A_train)
print(optimizer.predict(X_train[:5], sensitive_features=A_train[:5], random_state=0))
```

If fitting succeeds but held-out metrics are poor, switch to assessment rather than tuning postprocessing blindly.
