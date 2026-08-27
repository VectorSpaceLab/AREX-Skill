# Troubleshooting — model workflows

## Pipeline surprises

- If a user thinks `fit_transform` and `fit` + `transform` should match, remind
  them that imbalanced-learn pipelines resample during `fit_transform`.
- If a fitted pipeline appears to behave differently after caching, check the
  `memory` setting and the fitted step order.

## Ensemble compatibility

- Some ensemble parameters are easy to confuse with the base scikit-learn
  classes. Check whether the user wants a `sampler`, `sampling_strategy`, or
  `replacement` change.
- `BalancedRandomForestClassifier` has its own balancing defaults; do not assume
  it behaves exactly like `RandomForestClassifier`.
- `RUSBoostClassifier` can raise a "worse than random" error on difficult or
  poorly separated toy data. Try a more separable dataset, a different base
  estimator, or a larger `n_estimators` value if the smoke check fails.
- `sample_weight` support varies by estimator.

## Instance hardness issues

- `InstanceHardnessCV` is binary-only.
- The estimator passed to it must implement `predict_proba`.
- If the splitter raises a label error, check the positive label and class
  encoding.

## Recovery steps

1. Confirm the task is really about a model workflow rather than raw sampler
   choice.
2. Reduce the model to a tiny toy example.
3. Use `scripts/pipeline_leakage_check.py` or `scripts/model_selection_smoke.py`
   to isolate whether the issue is in pipeline semantics or splitter behavior.
