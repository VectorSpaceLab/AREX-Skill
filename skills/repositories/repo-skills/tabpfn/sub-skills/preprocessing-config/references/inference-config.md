# Inference and Preprocessing Configuration

## `InferenceConfig`

`InferenceConfig` collects advanced inference-time and preprocessing-time
controls. The important groups are:

### Feature and preprocessing transforms

- `PREPROCESS_TRANSFORMS`
- `REGRESSION_Y_PREPROCESS_TRANSFORMS`
- `FEATURE_SHIFT_METHOD`
- `CLASS_SHIFT_METHOD`
- `FINGERPRINT_FEATURE`
- `POLYNOMIAL_FEATURES`
- `SUBSAMPLE_SAMPLES`
- `ENABLE_GPU_PREPROCESSING`
- `FEATURE_SUBSAMPLING_METHOD`
- `FEATURE_SUBSAMPLING_CONSTANT_FEATURE_COUNT`
- `FEATURE_SUBSAMPLING_IMPORTANCE_TOP_K_COUNT`

### Heuristics and model-size limits

- `MAX_UNIQUE_FOR_CATEGORICAL_FEATURES`
- `MIN_UNIQUE_FOR_NUMERICAL_FEATURES`
- `MIN_NUMBER_SAMPLES_FOR_CATEGORICAL_INFERENCE`
- `OUTLIER_REMOVAL_STD`
- `MAX_NUMBER_OF_CLASSES`
- `MAX_NUMBER_OF_FEATURES`
- `MAX_NUMBER_OF_SAMPLES`
- `MAX_CPU_SAMPLES`

### Precision and numerical behavior

- `USE_SKLEARN_16_DECIMAL_PRECISION`
- `FIX_NAN_BORDERS_AFTER_TARGET_TRANSFORM`
- `PASSTHROUGH_INF`

## Default values worth remembering

- `OUTLIER_REMOVAL_STD` resolves to a task-specific default when set to `"auto"`.
- `MAX_CPU_SAMPLES` is version dependent: `5000` for `v3`, `1000` otherwise.
- `ENABLE_GPU_PREPROCESSING` is off by default.
- `PASSTHROUGH_INF` is off by default.
- Static defaults are only reconstructed for `v2` and `v2.5`; `v3` checkpoints carry the inference config inside the checkpoint, so the bundled inspection helper reports that instead of fabricating a static `v3` default.

## `PreprocessorConfig`

Important fields:

- `name` — the transformation to apply.
- `categorical_name` — how categorical columns are encoded.
- `append_original` — whether to append transformed features to the original features.
- `max_features_per_estimator` — feature budget per estimator.
- `global_transformer_name` — optional global reduction transform.
- `max_onehot_cardinality` — maximum category cardinality for one-hot encoding.
- `differentiable` — whether the preprocessor must remain differentiable.

## How to think about it

- `InferenceConfig` sets the high-level policy.
- `PreprocessorConfig` describes the concrete transform used by each ensemble member.
- The public estimators expose the common knobs directly and leave the rest here
  for advanced users.
