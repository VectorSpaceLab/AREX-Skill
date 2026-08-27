# API Overview — imbalanced-learn

This is the compact map for the public `imblearn` surface. Read the
sub-skill references for deeper parameter notes and examples.

## Package-level exports

`imblearn` exports the main subpackages plus `FunctionSampler` and
`show_versions`.

- `combine`
- `ensemble`
- `exceptions`
- `keras` (lazy import)
- `metrics`
- `model_selection`
- `over_sampling`
- `tensorflow`
- `under_sampling`
- `utils`
- `pipeline`
- `FunctionSampler`
- `__version__`

## Core modules and main entry points

| Module | Main public entry points | When to use |
|---|---|---|
| `imblearn.base` | `SamplerMixin`, `BaseSampler`, `FunctionSampler`, `is_sampler` | Build or introspect custom samplers. |
| `imblearn.over_sampling` | `RandomOverSampler`, `ADASYN`, `SMOTE`, `SMOTENC`, `SMOTEN`, `BorderlineSMOTE`, `KMeansSMOTE`, `SVMSMOTE` | Increase minority-class support. |
| `imblearn.under_sampling` | `RandomUnderSampler`, `TomekLinks`, `EditedNearestNeighbours`, `RepeatedEditedNearestNeighbours`, `AllKNN`, `OneSidedSelection`, `CondensedNearestNeighbour`, `NeighbourhoodCleaningRule`, `NearMiss`, `ClusterCentroids`, `InstanceHardnessThreshold` | Reduce majority-class support or clean borderline samples. |
| `imblearn.combine` | `SMOTEENN`, `SMOTETomek` | Compose over-sampling and cleaning. |
| `imblearn.pipeline` | `Pipeline`, `make_pipeline` | Chain samplers with transformers and estimators safely. |
| `imblearn.ensemble` | `BalancedBaggingClassifier`, `BalancedRandomForestClassifier`, `EasyEnsembleClassifier`, `RUSBoostClassifier` | Use imbalance-aware ensemble estimators. |
| `imblearn.datasets` | `make_imbalance`, `fetch_datasets` | Create imbalanced toy data or load benchmark datasets. |
| `imblearn.metrics` | `sensitivity_specificity_support`, `sensitivity_score`, `specificity_score`, `geometric_mean_score`, `make_index_balanced_accuracy`, `classification_report_imbalanced`, `macro_averaged_mean_absolute_error` | Evaluate imbalanced classification results. |
| `imblearn.metrics.pairwise` | `ValueDifferenceMetric` | Use categorical pairwise distance. |
| `imblearn.model_selection` | `InstanceHardnessCV` | Cross-validation that spreads hard samples evenly. |
| `imblearn.tensorflow` | `balanced_batch_generator` | Balanced mini-batches for TensorFlow-style loops. |
| `imblearn.keras` | `BalancedBatchGenerator`, `balanced_batch_generator` | Balanced mini-batches for Keras training loops. |
| `imblearn.utils` | `check_neighbors_object`, `check_sampling_strategy`, `check_target_type`, `Substitution` | Validation and docstring helpers. |

## Signature anchors from the inspected environment

These were confirmed from the private inspection environment and are useful
when writing task-specific instructions.

- `FunctionSampler(func=None, accept_sparse=True, kw_args=None, validate=True)`
- `RandomOverSampler(sampling_strategy='auto', random_state=None, shrinkage=None)`
- `RandomUnderSampler(sampling_strategy='auto', random_state=None, replacement=False)`
- `SMOTE(sampling_strategy='auto', random_state=None, k_neighbors=5)`
- `SMOTENC(categorical_features, *, categorical_encoder=None, sampling_strategy='auto', random_state=None, k_neighbors=5)`
- `SMOTEN(categorical_encoder=None, *, sampling_strategy='auto', random_state=None, k_neighbors=5)`
- `SMOTEENN(sampling_strategy='auto', random_state=None, smote=None, enn=None, n_jobs=None)`
- `SMOTETomek(sampling_strategy='auto', random_state=None, smote=None, tomek=None, n_jobs=None)`
- `BalancedBaggingClassifier(..., sampler=None)`
- `BalancedRandomForestClassifier(sampling_strategy='all', replacement=True, bootstrap=False, ...)`
- `EasyEnsembleClassifier(n_estimators=10, estimator=None, ...)`
- `RUSBoostClassifier(estimator=None, n_estimators=50, learning_rate=1.0, ...)`
- `Pipeline(steps, *, transform_input=None, memory=None, verbose=False)`
- `make_pipeline(*steps, memory=None, transform_input=None, verbose=False)`
- `make_imbalance(X, y, *, sampling_strategy=None, random_state=None, verbose=False, **kwargs)`
- `fetch_datasets(*, data_home=None, filter_data=None, download_if_missing=True, random_state=None, shuffle=False, verbose=False)`
- `geometric_mean_score(y_true, y_pred, *, labels=None, pos_label=1, average='multiclass', sample_weight=None, correction=0.0)`
- `classification_report_imbalanced(y_true, y_pred, *, labels=None, target_names=None, sample_weight=None, digits=2, alpha=0.1, output_dict=False, zero_division='warn')`
- `balanced_batch_generator(X, y, *, sample_weight=None, sampler=None, batch_size=32, keep_sparse=False, random_state=None)`

## What to remember

- Most sampling classes follow the scikit-learn estimator pattern and expose
  `fit_resample`.
- `Pipeline` applies samplers during fitting; the fit/transform split is not a
  no-op resampling split.
- `BalancedBatchGenerator` requires Keras/TensorFlow to be importable; the
  generator functions themselves can still be used as CPU data iterators.
- `fetch_datasets` is a network/cache helper, not a pure offline primitive.
