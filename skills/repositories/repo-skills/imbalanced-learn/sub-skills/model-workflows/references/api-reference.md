# API Reference — model workflows

## Core signatures confirmed in the private inspection environment

| Symbol | Signature / key arguments | Notes |
|---|---|---|
| `Pipeline` | `Pipeline(steps, *, transform_input=None, memory=None, verbose=False)` | Chained transforms, samplers, and final estimator. |
| `make_pipeline` | `make_pipeline(*steps, memory=None, transform_input=None, verbose=False)` | Convenience constructor. |
| `BalancedBaggingClassifier` | `BalancedBaggingClassifier(..., sampler=None, sampling_strategy='auto', replacement=False, random_state=None, ...)` | Bagging with internal resampling. |
| `BalancedRandomForestClassifier` | `BalancedRandomForestClassifier(..., sampling_strategy='all', replacement=True, bootstrap=False, ...)` | Random-forest-style balanced bootstraps. |
| `EasyEnsembleClassifier` | `EasyEnsembleClassifier(n_estimators=10, estimator=None, ..., sampling_strategy='auto', replacement=False, random_state=None, ...)` | AdaBoost-based ensemble on balanced subsets. |
| `RUSBoostClassifier` | `RUSBoostClassifier(estimator=None, n_estimators=50, learning_rate=1.0, ..., sampling_strategy='auto', replacement=False, random_state=None)` | Boosting with repeated under-sampling. |
| `InstanceHardnessCV` | `InstanceHardnessCV(estimator, *, n_splits=5, pos_label=None)` | Binary-only hardness-aware splitter. |

## Routing notes

- `Pipeline` and `make_pipeline` are the safest way to keep resampling inside the
  training branch.
- `BalancedBaggingClassifier` is the most flexible ensemble when the user wants
  to swap the internal sampler.
- `BalancedRandomForestClassifier` is the most obvious forest-like balanced
  ensemble.
- `InstanceHardnessCV` is not a general splitter; it is specialized for binary
  classification and model-selection robustness.

## Related package behavior

- The pipeline warns if you treat `fit_transform` as equivalent to `fit` plus
  `transform`.
- Ensemble constructors expose internal balancing parameters that can change the
  class distribution of bootstrap samples.
- `InstanceHardnessCV` uses a classifier that must implement `predict_proba`.
