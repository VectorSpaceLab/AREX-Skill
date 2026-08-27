# Core API Reference

## Constructors

`TabPFNClassifier` and `TabPFNRegressor` are sklearn-style estimators. Both
constructors share these important parameters:

- `n_estimators="auto"` — ensemble size; integer values explicitly control the number of forward passes.
- `auto_scale_n_estimators=True` — raises estimator count on wide datasets so features are covered.
- `categorical_features_indices=None` — optional positional indices for categorical features.
- `model_path="auto"` — use the default checkpoint; can also be a local path, list of paths, or model-spec object.
- `device="auto"` — infer CUDA, MPS, or CPU devices.
- `ignore_pretraining_limits=False` — bypass model size guardrails when explicitly accepted.
- `inference_precision="auto"` — automatic/autocast or a torch dtype.
- `fit_mode="fit_preprocessors"` — ordinary default; performance modes are routed to batched-performance.
- `n_preprocessing_jobs=1` — parallel preprocessing worker count.
- `inference_config=None` — dict or `InferenceConfig` for advanced behavior.
- `show_progress_bar=False` — enables progress display.

Classifier-only constructor parameters include `balance_probabilities`,
`average_before_softmax`, `eval_metric`, and `tuning_config`.

## Version-pinned defaults

```python
from tabpfn import TabPFNClassifier, TabPFNRegressor
from tabpfn.constants import ModelVersion

clf = TabPFNClassifier.create_default_for_version(ModelVersion.V2_6, n_estimators=4)
reg = TabPFNRegressor.create_default_for_version(ModelVersion.V3, n_estimators=4)
```

Known `ModelVersion` values are `v2`, `v2.5`, `v2.6`, and `v3`.

## Classifier outputs

| Method | Return shape | Notes |
| --- | --- | --- |
| `fit(X, y)` | `self` | Sets fitted sklearn attributes such as `classes_`, `n_features_in_`, and `executor_`. |
| `predict(X)` | `(n_samples,)` | Returns decoded labels. |
| `predict_proba(X)` | `(n_samples, n_classes)` | Probabilities sum to 1 per row. |
| `predict_logits(X)` | `(n_samples, n_classes)` | Aggregated logits. With multiple estimators and `average_before_softmax=False`, `softmax(predict_logits(...))` need not equal `predict_proba(...)`. |
| `predict_raw_logits(X)` | `(n_estimators, n_samples, n_classes)` | Per-estimator logits before averaging and temperature/probability postprocessing. |
| `logits_to_probabilities(raw_logits, ...)` | `(n_samples, n_classes)` | Applies the estimator's softmax temperature, averaging order, and balancing options. |
| `get_embeddings(X, data_source="test")` | `(n_estimators, n_samples, embedding_dim)` when ensembled | Requires a fitted estimator; `data_source` is `"train"` or `"test"`. |

## Regressor outputs

`TabPFNRegressor.predict(X, output_type="mean", quantiles=None)` supports:

| `output_type` | Return |
| --- | --- |
| `"mean"` | NumPy array of mean predictions. |
| `"median"` | NumPy array of median predictions. |
| `"mode"` | NumPy array of modal predictions. |
| `"quantiles"` | List of arrays, one per quantile. Defaults to 0.1 through 0.9. |
| `"main"` | Dict with `mean`, `median`, `mode`, and `quantiles`. |
| `"full"` | Same as `main`, plus the raw-space bar-distribution `criterion` and `logits`. |

Quantiles must be floats between 0 and 1. Constant-target regression datasets
are answered analytically and return constant arrays for all point/quantile
outputs.

## Persistence methods

Both estimators expose light wrappers:

- `save_fit_state(path)` — stores fitted estimator state; path must end in `.tabpfn_fit`.
- `load_from_fit_state(path, device="cpu")` — reconstructs the estimator and fitted state.

For model-weight and checkpoint details, use the model-management sub-skill.
