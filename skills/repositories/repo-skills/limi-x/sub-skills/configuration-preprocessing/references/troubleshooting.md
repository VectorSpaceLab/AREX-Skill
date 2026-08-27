# Configuration and preprocessing troubleshooting

Use `scripts/inspect_config.py` first when a user supplies a JSON config. It catches malformed config lists without importing LimiX or loading a checkpoint.

## Malformed config list

Symptoms:

- JSON parse errors.
- Root JSON value is not a list.
- Root list is empty.
- A pipeline entry is not an object.
- A transform block that is unpacked with `**...` is not an object.

Fix:

1. Make the root value a non-empty JSON list.
2. Make each list item a JSON object with a `retrieval_config` object.
3. Keep transform blocks as JSON objects, except `FingerprintFeatureEncoder`, which is usually a boolean flag.
4. Validate with:

```bash
python sub-skills/configuration-preprocessing/scripts/inspect_config.py path/to/config.json
```

## Missing or invalid retrieval_config

Symptoms:

- Pipeline construction fails while indexing `inference_config_item["retrieval_config"]`.
- `inspect_config.py` reports `missing retrieval_config`.

Fix:

For a CPU-safe no-retrieval config, every pipeline item should include at least:

```json
"retrieval_config": {
  "use_retrieval": false,
  "retrieval_before_preprocessing": false,
  "calculate_feature_attention": false,
  "calculate_sample_attention": false,
  "subsample_ratio": 0.7,
  "subsample_type": "sample",
  "use_type": "mixed"
}
```

If retrieval is enabled, also include retrieval-specific keys such as `retrieval_len`, `subsample_type`, `use_type`, and the required attention flags. Route tuning and search semantics to `../retrieval-optimization/SKILL.md`.

## Invalid config path

Symptoms:

- The predictor receives a string path and raises that `inference_config is not a config file path`.
- A command references a catalog file name that is not present in the current runtime environment.

Fix:

- Pass either an already-loaded Python list or a path to an existing local JSON file.
- Do not assume the original repository's config directory exists in the user's environment.
- Generate a standalone no-retrieval file when needed:

```bash
python sub-skills/configuration-preprocessing/scripts/generate_noretrieval_config.py \
  --task classification \
  --output limix_cls_noretrieval.json
```

Then inspect the file before using it.

## Empty pipeline assertion

Symptom:

- Predictor assertion: invalid configuration file because the number of pipelines is 0.

Fix:

- Add at least one pipeline object to the root list.
- Prefer the observed default counts: 4 pipelines for classification, 8 for regression or MVI.
- If experimenting, reduce the pipeline count deliberately but never use an empty list.

## Retrieval config used on CPU

Symptoms:

- Predictor construction on CPU raises that retrieval is not supported for CPU inference.
- Mixed precision is automatically disabled on CPU.

Fix:

- Use a no-retrieval config (`use_retrieval=false` in every pipeline).
- Run `inspect_config.py`; `CPU compatible: yes` means no pipeline uses retrieval.
- Full checkpoint inference still needs a local LimiX checkpoint; practical retrieval inference may require CUDA/GPU and substantial memory.

## Constant or all-NaN features

Symptoms:

- `FilterValidFeatures` raises `All features are constant! Please check your data.`
- All columns disappear after filtering.
- MVI reconstruction has missing or restored columns that look unchanged.

Cause:

- Constant columns are dropped.
- If labels are supplied, columns that are all-NaN in the train slice or all-NaN in the test slice are also dropped.

Fix:

- Remove constant features before LimiX.
- Impute or drop columns that are all-NaN in train or test.
- Ensure train and test have the same feature columns before concatenation.
- For MVI, remember that invalid columns are restored from stored invalid-feature values during postprocessing where possible; they were not modeled as valid features.

## MVI power-method warning

Symptoms:

- Warning: missing value imputation does not currently support the preprocessing method `power`; default worker tags are used instead.
- MVI postprocessing raises about `power` not being supported.

Cause:

When `mask_prediction=true`, the predictor scans each pipeline's `RebalanceFeatureDistribution.worker_tags`. If it finds `power`, it replaces that tag with `null` and sets `discrete_flag=true`. Postprocessing also treats `power` as unsupported for MVI.

Fix:

- Use an MVI-style no-retrieval config where the second template uses `worker_tags=[null]`, `discrete_flag=true`, and one-hot encoding.
- Do not start from `reg_default_noretrieval` for MVI unless you remove or replace `power` worker tags.
- Route the actual MVI predictor workflow to `../predictor-inference/SKILL.md` after config selection.

## Category inference thresholds

Symptoms:

- Expected categorical columns are treated as numeric.
- Strict ordinal feature-shuffled encoding ignores a categorical column.

Relevant thresholds:

- Automatic category inference returns no categorical columns when the concatenated train+test feature matrix has fewer than 100 rows.
- Otherwise, a column is inferred categorical only if it has fewer than 4 unique values.
- `max_unique_num_for_category_infer=30` exists as a predictor attribute but is not used by the implemented inference method.
- Strict feature-shuffled ordinal encoding keeps a categorical column only when the least common category appears at least 10 times and the unique count is less than `len(column)//10`.

Fix:

- For small datasets, encode categorical features explicitly before calling LimiX or choose numeric/ordinal behavior deliberately.
- For rare categories, prefer `numeric`, `none`, or non-strict ordinal strategies if strict filtering drops the column.
- Validate class balance and category counts before blaming retrieval or checkpoint behavior.

## Large one-hot fallback

Symptoms:

- One-hot encoding appears to have no effect.
- Categorical indices after one-hot do not match expectations.

Cause:

The one-hot encoder builds a dense matrix. If the encoded result contains at least 1,000,000 values, the encoder falls back to the original input matrix by clearing the transformer.

Fix:

- Use ordinal or numeric encoding for high-cardinality categorical data.
- Reduce categorical cardinality before inference.
- If MVI requires one-hot for a small categorical dataset, confirm the dense encoded size is below the fallback threshold.

## KDI and Hyperopt dependency issues

Symptoms:

- Importing preprocessing code fails because `kditransform` is missing.
- Calling `sample_inferece_params` fails because `hyperopt` is missing.
- Sampled worker tags with KDI-like names behave unexpectedly.

Fix:

- Install `kditransform` when importing preprocessing code or using KDI worker tags. The preprocessing module imports it at module import time.
- Install `hyperopt` only if using `sample_inferece_params`; existing JSON parsing and the bundled inspector do not need it.
- Be careful with custom KDI tag names. The implementation recognizes `kdi_uni`, `kdi_norm`, and alpha-prefixed `kdi_uni_alpha_*` / `kdi_norm_alpha_*`; unknown strings fall back to identity behavior.

## Retrieval assertion failures

Symptoms:

- Assertion says sample-level retrieval must calculate sample attention.
- Assertion says mixed retrieval must calculate sample and feature attention.
- Assertion says feature-level retrieval must calculate feature attention.

Fix:

- For `subsample_type="sample"`, set `calculate_sample_attention=true`.
- For `subsample_type="sample"` and `use_type="mixed"`, set both sample and feature attention flags true.
- For `subsample_type="feature"`, set `calculate_feature_attention=true`.
- Prefer observed defaults (`sample` + `only_sample` + sample attention) unless you are deliberately tuning retrieval; route tuning to `../retrieval-optimization/SKILL.md`.

## Optional transform shape or mode errors

Symptoms and fixes:

- `FeatureShuffler` unsupported mode: use `shuffle`, `rotate`, or `null`.
- Feature count mismatch after shuffling: ensure train/test have identical columns and do not change feature count between fit and transform.
- `PolynomialInteractionGenerator` assertion: input must be two-dimensional and `max_interaction_features` must be positive when provided.
- `FingerprintFeatureEncoder` transform-before-fit error: let the predictor build and fit the pipeline; do not call the transform directly first.
