# LimiX preprocessing reference

Use this reference to explain what a LimiX inference config item does before a predictor call. Actual prediction workflows belong to `../predictor-inference/SKILL.md`; retrieval search/tuning belongs to `../retrieval-optimization/SKILL.md`.

## Pipeline construction order

For every config-list item, the predictor builds one pipeline in this order:

1. If retrieval is enabled and `retrieval_before_preprocessing=true`: attention map, then `SubSampleData`.
2. Optional `PolynomialInteractionGenerator` if the key is present.
3. Always `FilterValidFeatures`.
4. Optional `RebalanceFeatureDistribution` if the key is present.
5. Optional `CategoricalFeatureEncoder` if the key is present.
6. Optional `FingerprintFeatureEncoder` if the key is present and truthy.
7. Optional `FeatureShuffler` if the key is present.
8. If retrieval is enabled and `retrieval_before_preprocessing=false`: attention map, then `SubSampleData`.

The predictor concatenates train and test features before preprocessing so that the same fitted pipeline shape is used across train/test. Rebalance fitting is special: it fits on the train slice (`x[:len(y)]`) and then transforms train and test slices separately before concatenation.

## Data conversion before configured transforms

Before the configured transforms run, predictor code:

- validates arrays while allowing NaNs;
- concatenates train and test feature rows;
- converts numeric arrays to a pandas frame with float dtype;
- converts object/string/bool/category columns through an ordinal encoder, preserving missing string placeholders as NaN;
- infers categorical feature indices only when the concatenated feature matrix has at least 100 rows, then marks columns with fewer than 4 unique values as categorical.

The predictor stores `max_unique_num_for_category_infer=30`, but its implemented category-inference method uses only the 100-row minimum and the fewer-than-4-unique-values rule.

## Transform classes

| Class/block | Key options | Behavior | Data implications and failure modes |
|---|---|---|---|
| `FilterValidFeatures` | No config block; always inserted. | Drops columns that are constant across all rows. When `y` is supplied, it also drops columns that are all-NaN in either the train slice or test slice. Categorical indices are remapped to the retained columns. | Raises `ValueError("All features are constant! Please check your data.")` if no feature survives. For MVI postprocessing, deleted columns are restored from stored invalid-feature values where possible. |
| `RebalanceFeatureDistribution` | `worker_tags`, `discrete_flag`, `original_flag`, `svd_tag`, `joined_svd_feature`, `joined_log_normal`. | Builds a `ColumnTransformer` over categorical/discrete and continuous columns. `original_flag=true` preserves original features; `discrete_flag=true` treats categorical+continuous columns together as transformed discrete-like features; `svd_tag="svd"` appends SVD features when at least 2 input features exist. | Worker tags seen in default configs include `quantile_uniform_10`, `quantile_uniform_all_data`, `power`, and `null`. Sampled configs can mention log-normal, quantile-normal/uniform variants, robust scaling, KDI variants, or combinations. Unknown string tags fall back to identity behavior. `power` is not safe for MVI; use the MVI config or no-power worker tags for mask prediction. KDI-related tags require `kditransform` to be importable. |
| `CategoricalFeatureEncoder` | `encoding_strategy`: `ordinal`, `ordinal_strict_feature_shuffled`, `ordinal_shuffled`, `onehot`, `numeric`, `none`. | `ordinal*` encodes selected categorical columns first and can shuffle category codes. `onehot` uses dense one-hot encoding with binary drop and unknown-category ignore. `numeric`/`none` does not create a transformer. | Strict feature-shuffled ordinal encoding only keeps categorical columns with least-common-category count ≥ 10 and unique category count < `len(column)//10`; non-strict ordinal shuffling requires least-common-category count ≥ 10. One-hot falls back to the original matrix if the dense encoded result size is at least 1,000,000 values. Invalid strategy raises an unsupported/unknown transform error. |
| `FeatureShuffler` | `mode`: `shuffle`, `rotate`, or `null`; `offset` (predictor overwrites offsets per estimator). | Reorders feature columns and returns remapped categorical indices. `shuffle` uses the per-step seed; `rotate` rolls indices by offset; `null` preserves order. | Raises for unsupported mode, transform before fit, or mismatched feature count at transform time. Because feature order changes per estimator, postprocessing uses inverse indices for MVI reconstruction. |
| `FingerprintFeatureEncoder` | Config value is normally boolean; constructor accepts an optional seed but predictor ignores config args and instantiates with defaults. | Appends one fingerprint column derived from a salted hash of each row. Training mode resolves collisions by rehashing; test mode uses the first hash. | Adds one numeric feature and keeps categorical indices unchanged. Requires fit before transform. Hashing numeric arrays with NaNs or object remnants can produce surprising fingerprints; rely on predictor dtype conversion first. |
| `PolynomialInteractionGenerator` | `max_interaction_features`: positive integer or `null`; constructor defaults falsy/null to 100. | Standardizes features with `StandardScaler(with_mean=false)`, samples randomized feature pairs, and appends pairwise product interaction features. | Increases feature width and memory. Input must be two-dimensional. Empty matrices pass through. Non-positive `max_interaction_features` fails an assertion. |
| `SubSampleData` | Constructed from `retrieval_config.subsample_type` (`sample` or `feature`) and `retrieval_config.use_type` (`mixed` or `only_sample`). | For sample retrieval, stores train data and attention scores for retrieval inference. For feature retrieval, selects feature indices using feature attention. | Only meaningful when retrieval attention maps are present. Mixed sample retrieval multiplies sample and feature attention and may OOM when moved to CUDA; the code falls back to CPU for that calculation if a CUDA OOM is caught. CPU predictor use should avoid retrieval configs entirely. |

## Rebalance worker notes

- `quantile_uniform_10`: uniform quantile transform with roughly `n_samples//10` quantiles, minimum 2.
- `quantile_uniform_all_data`: uniform quantile transform using all data as its subsample and roughly `n_samples//5` quantiles, minimum 2.
- `quantile_norm_10`, `quantile_norm_5`, `quantile_norm_all_data`: normal-output quantile variants.
- `power`: robust Yeo-Johnson-like power transform with NaN/Inf guards, mean imputation, and scaling; current MVI logic warns and replaces it.
- `logNormal`: shifts values non-negative, adds epsilon, logs, and imputes missing values around the transform.
- `robust`: robust scaling with unit variance.
- `norm_and_kdi`, `kdi_uni`, `kdi_norm`, and alpha-prefixed KDI variants require `kditransform` and are more dependency-sensitive.
- `null` worker tag is an identity transform. Unknown non-null strings also degrade to identity in the current implementation, so inspect custom tags carefully.

## Sampled preprocessing configs

`sample_inferece_params(rng, sample_num=2, repeat_num=2)` uses Hyperopt to sample preprocessing configs. It returns:

- `hyperopt_configs`: a list where each sampled pipeline config is repeated `repeat_num` times;
- `base_config`: a separate dict with `softmax_temperature` and `seed` values intended for `set_inference_config`.

Sampled configs may include optional `FingerprintFeatureEncoder` and `PolynomialInteractionGenerator`, sampled categorical encoders, sampled shuffler modes, and no-retrieval `retrieval_config`. Hyperopt is only needed for this sampling helper, not for parsing or inspecting an existing JSON config.

## Practical selection rules

- Classification defaults use 4 pipelines; regression and MVI defaults use 8 pipelines.
- Use non-retrieval configs for CPU and quick local validation.
- Use `reg_default_noretrieval_MVI`-style no-power configs for MVI (`mask_prediction=true`).
- Avoid one-hot configs when categorical cardinality is high enough to create very large dense matrices; use ordinal or numeric encoding instead.
- If every feature is constant or all-NaN in train/test, fix the dataset before changing model or retrieval parameters.
