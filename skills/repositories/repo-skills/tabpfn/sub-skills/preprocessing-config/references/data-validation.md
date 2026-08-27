# Data Validation and Cleaning

## Fit-time validation

The main fit-time entry point validates both `X` and `y` before the model is
built.

### `ensure_compatible_fit_inputs`

This helper:

- Preserves a pandas `Series` target name when one exists.
- Delegates to sklearn-style validation.
- Enforces dataset size limits.
- Returns validated `X`, validated `y`, feature names, feature count, and the original target name.

### `validate_dataset_size`

Checks:

- `X` and `y` must have the same number of rows.
- `X` must be two-dimensional.
- Sample and feature caps must not be exceeded unless the user explicitly overrides them.
- CPU inference has a separate large-dataset guard.

### `validate_num_classes`

Raises if the number of classes exceeds the model's supported class limit.

## Predict-time validation

### `ensure_compatible_predict_input_sklearn`

- Converts pandas DataFrames to NumPy-friendly form.
- Uses sklearn validation without resetting fitted state.
- Allows NaNs by default.
- Rejects infinities unless the estimator's inference config enables `PASSTHROUGH_INF`.

## Cleaning helpers

### `fix_dtypes`

- Converts numeric NumPy arrays to a DataFrame with numeric dtype.
- Leaves object arrays as DataFrames so pandas can inspect mixed dtypes.
- Refuses raw string NumPy dtypes.
- Applies user-supplied categorical indices as pandas categorical columns.

### `process_text_na_dataframe`

- Ordinal-encodes categorical and text-like columns.
- Handles missing values and preserves fitted ordinal encoding on predict.
- Emits a warning when a column looks like free text rather than a stable categorical feature.

### `coerce_nullable_dtypes_to_numpy`

Converts nullable numeric and boolean pandas columns to float64 before sklearn's
validation so mixed frames do not trip a whole-frame cast.

## Feature modality detection

### `detect_feature_modalities`

TabPFN infers per-column modality from:

- User-provided categorical indices.
- Unique-value counts.
- Whether the column is numeric, categorical, string-like, text-like, or constant.
- The number of rows available for inference.

### Common modality results

- `NUMERICAL` — stable numeric features.
- `CATEGORICAL` — low-cardinality or explicitly categorical features.
- `TEXT` — string columns with too many unique values for stable categorical use.
- `CONSTANT` — all-missing or single-value columns.

## Practical implications

- A DataFrame with mixed numeric, categorical, and text columns can be valid.
- A NumPy object array is much less predictable than a pandas DataFrame.
- Users should mark real categorical columns explicitly when the inference heuristics are ambiguous.
- Infinities are only allowed when the model config says to pass them through.
