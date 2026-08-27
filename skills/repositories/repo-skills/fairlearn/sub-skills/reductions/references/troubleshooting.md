# Reductions troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Base estimator raises unexpected `sample_weight` error | Estimator does not accept `sample_weight` or a pipeline step needs a routed name. | Choose a sample-weight-aware estimator or set `sample_weight_name`, e.g. `classifier__sample_weight` for a named pipeline step. |
| `RuntimeError: Unsupported disparity metric` | Constraint is not a Fairlearn `Moment` instance. | Pass an instantiated Moment such as `DemographicParity()` or `EqualizedOdds()`, not a metric function. |
| `RuntimeError: Unsupported selection rule` | `GridSearch` received a non-supported `selection_rule`. | Use `selection_rule="tradeoff_optimization"` in this source. |
| `constraint_weight` error | Weight is outside `[0.0, 1.0]`. | Choose a value between 0 and 1. Higher values emphasize constraint violation over error. |
| Mitigator fit is slow | Repeated base-estimator training; grid/iteration count too high. | First run with smaller `max_iter`/`grid_size`, simpler estimator, and smaller fixture. |
| Results vary across runs | Random base estimator or stochastic data split. | Set `random_state` on the base estimator and train/test split. |
| Disparity did not improve | Constraint/metric mismatch, estimator cannot fit trade-off, or data issue. | Use assessment to compare the specific constrained metric; try another constraint or mitigation family only with documented rationale. |
| User supplies continuous targets | Some classification constraints are inappropriate. | Use regression/loss moments such as `BoundedGroupLoss` with a suitable loss. |
| Multiple sensitive features cause confusing labels | Intersections are represented by combinations of sensitive feature values. | Use pandas DataFrame with named sensitive columns and report group counts. |

## Minimal reducer diagnostic

```python
print(type(base_estimator))
print(hasattr(base_estimator, "fit"), hasattr(base_estimator, "predict"))
print(len(X_train), len(y_train), len(A_train))
mitigator = ExponentiatedGradient(base_estimator, DemographicParity(), max_iter=3)
mitigator.fit(X_train, y_train, sensitive_features=A_train)
print(mitigator.predict(X_train[:5]))
```

If this fails before optimization diagnostics are produced, fix estimator compatibility and data alignment first.
