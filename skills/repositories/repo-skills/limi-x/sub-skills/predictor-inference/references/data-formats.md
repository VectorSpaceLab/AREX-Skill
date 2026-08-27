# Data Formats for Predictor Inference

`LimiXPredictor.predict()` is designed for supervised tabular context plus test rows. It concatenates `x_train` and `x_test` before preprocessing so feature transforms are consistent across train/test rows.

## Required shapes

| Argument | Shape | Requirements |
| --- | --- | --- |
| `x_train` | `(n_train, n_features)` | Two-dimensional array-like. Rows are training samples; columns are aligned tabular features. |
| `y_train` | `(n_train,)` | One target per training row. Use classification labels for `task_type="Classification"`; numeric targets for `task_type="Regression"`. |
| `x_test` | `(n_test, n_features)` | Two-dimensional array-like with exactly the same feature columns and order as `x_train`. |

If the feature counts differ, concatenating train and test features will fail before model inference.

## Accepted containers

- NumPy arrays are the safest default for numeric data.
- Pandas dataframes/series are accepted when scikit-learn validation can convert them.
- Scikit-learn dataset outputs work directly after train/test split.
- Avoid pure NumPy arrays with fixed-width string dtype (`"U"`/`"S"`). Use pandas/object columns or pre-encode strings.

## Feature dtypes and categorical/object columns

The predictor converts numeric features through pandas and then to floating tensors. Object/string/bool columns are encoded internally with ordinal-style encoding before model inference; missing string/object values are temporarily filled with a placeholder and restored to missing values after encoding.

Caveats:

- `categorical_features_indices` is accepted by the constructor, but current preprocessing does not actively consume it.
- Low-cardinality categorical inference is heuristic. With fewer than 100 combined train+test rows, no numeric column is inferred as categorical by that heuristic. With enough rows, columns with fewer than 4 unique values are treated as categorical candidates.
- For precise category encodings, one-hot choices, or transform authoring, route to the configuration/preprocessing sub-skill.

## Target labels

### Classification

- `y_train` may contain numeric or string-like class labels as long as it is one-dimensional.
- Labels are encoded internally with a label encoder.
- After prediction, probability columns correspond to `predictor.classes`.
- Native batch-style classification loops skip unsupported class counts, but the direct API itself leaves class-count validation mostly to runtime failures and metrics. For stable use, keep classification labels to a small, meaningful set.

### Regression

- `y_train` must be numeric and one-dimensional.
- The predictor does not normalize the target. Normalize externally when needed, then denormalize the returned tensor for user-facing predictions.
- Guard against constant regression targets before z-normalizing; `std == 0` makes normalization invalid.

## NaN and missing-value handling

- Feature validation allows NaNs.
- For ordinary prediction, NaNs can be present, but they still affect preprocessing and model quality.
- For MVI, deliberately set missing entries in `x_test` to `np.nan` and keep the original unmasked matrix separately for validation.
- The reconstructed MVI output covers the combined train+test feature matrix. Use the final `n_test` rows for the test reconstruction.
- Columns that are all constant or all-NaN across the relevant train/test split are removed by preprocessing. If every feature is removed, prediction raises an all-features-constant error.

## Size guidance

LimiX is intended for tabular datasets below roughly 50,000 samples and below roughly 10,000 features. Larger tables increase memory and hardware requirements and may provide less advantage over classical supervised models. Retrieval configs are especially memory-intensive and are intended for CUDA/GPU environments; use non-retrieval configs for CPU or constrained smoke checks.
