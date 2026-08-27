# Data Formats

Read this file before building a PyPOTS dataset, HDF5 file, CLI data command,
or assertion case. Most user mistakes are key-name or shape mistakes.

## Core Tensor Shape

PyPOTS time-series samples use a 3D array:

```text
[n_samples, n_steps, n_features]
```

Values may contain `NaN` where observations are missing. PyPOTS usually derives
missing masks internally from `NaN` positions.

## Shared Dataset Keys

| Key | Shape | Meaning | Required for |
| --- | --- | --- | --- |
| `X` | `[n_samples, n_steps, n_features]` | observed input with missing values encoded as `NaN` | all tasks |
| `X_ori` | same as `X` | original or intact values used for loss/evaluation at artificially masked points | many imputation validation/test flows |
| `X_pred` | `[n_samples, n_pred_steps, n_pred_features]` | future target segment for forecasting | forecasting train/val/test |
| `y` | `[n_samples]` or classifier-compatible labels | labels for classification, clustering validation, and some CLI evaluation paths | classification, clustering, representation validation, CLI evaluation |
| `anomaly_y` | task-specific binary labels in native tests | anomaly labels used by native detector tests | anomaly detection evaluation |

The `BaseDataset` class supports HDF5 and in-memory dict inputs with `X`,
optional `X_ori`, optional `X_pred`, and optional `y`. `anomaly_y` is used by
native test fixtures and metric calls but is not part of the base dataset's
standard optional-key list.

## Task-Specific Data Recipes

### Imputation

Minimum test set:

```python
test_set = {"X": X_with_nan}
results = model.predict(test_set)
imputed = results["imputation"]
```

For evaluation against artificially hidden values:

```python
test_set = {"X": X_with_nan, "X_ori": X_intact}
indicating_mask = np.isnan(test_set["X"]) & ~np.isnan(test_set["X_ori"])
```

Native tests often compute MSE only on the indicating mask.

### Forecasting

Training and validation use an observed prefix plus a future segment:

```python
train_set = {"X": train_X[:, :n_steps], "X_pred": train_X[:, n_steps:]}
val_set = {"X": val_X[:, :n_steps], "X_pred": val_X[:, n_steps:]}
```

The model returns `results["forecasting"]` with shape compatible with
`X_pred`.

### Classification

Training and validation need labels:

```python
train_set = {"X": train_X, "y": train_y}
val_set = {"X": val_X, "y": val_y}
test_set = {"X": test_X}
```

Use `predict_proba()` or read `results["classification_proba"]` for probability
metrics. Use `classify()` or `results["classification"]` for class labels.

### Anomaly Detection

Detectors usually take `X` plus a constructor-time `anomaly_rate`.
Native tests keep binary labels in `anomaly_y` for metric checks:

```python
model = TimesNet(n_steps=n_steps, n_features=n_features, anomaly_rate=0.05, ...)
results = model.predict({"X": test_X})
scores_or_labels = results["anomaly_detection"]
```

When using `pypots-cli evaluate` for anomaly detection, verify the ground-truth
HDF5 key expected by that command; its current binary-evaluation branch checks
for `y`.

### Clustering

Clustering training can use only `X`, while labels are useful for evaluation:

```python
train_set = {"X": train_X}
val_set = {"X": val_X, "y": val_y}
results = model.predict({"X": test_X}, return_latent_vars=True)
clusters = results["clustering"]
```

### Representation

Representation models return embeddings rather than task labels:

```python
model.fit({"X": train_X, "y": train_y}, {"X": val_X, "y": val_y})
results = model.predict({"X": test_X})
embeddings = results["representation"]
series_vectors = model.represent({"X": test_X}, encoding_window="full_series")
```

## HDF5 Lazy Loading

The only supported dataset file type in the base dataset config is `hdf5`.
Use the programmatic save/load helpers:

```python
from pypots.data.saving import save_dict_into_h5, load_dict_from_h5

save_dict_into_h5({"X": X, "X_ori": X_ori}, "dataset.h5")
loaded = load_dict_from_h5("dataset.h5")
```

The same logical keys are used whether the input is an in-memory dict or an HDF5
file path.

## `BaseDataset` Sample Order

Internally, `BaseDataset.__getitem__()` returns a list in this order:

```text
idx, X, missing_mask
+ X_ori, indicating_mask        when return_X_ori=True
+ X_pred, X_pred_missing_mask   when return_X_pred=True
+ y                             when return_y=True
```

This order matters when adding or debugging model wrappers that assemble input
dicts for `forward()`.

## CSV Protocol Used by `pypots-cli data`

The CLI data helpers detect these special column roles:

- `SAMPLE_ID`: groups rows into samples.
- `TIMESTAMP`: time coordinate metadata.
- `SAMPLE_LABEL` and `STEP_LABEL`: reserved names.
- Any column containing `CLAF_TARGET`: classification label column.
- Numeric, non-reserved columns: feature columns.

`pypots-cli data prepare` converts CSV rows to `X` shaped
`[n_samples, max_steps, n_features]`, pads shorter samples with `NaN`, writes
`X_ori`, and adds `y` if a label column exists. For `set_type=train`, `X` starts
as `X_ori`; for validation/test, artificial missingness may be injected according
to `--missing_rate`.

## Programmatic Data Utilities

The `pypots.data` public exports include:

- `BaseDataset`
- `SUPPORTED_DATASET_FILE_FORMATS`
- `save_dict_into_h5`, `load_dict_from_h5`
- `pickle_dump`, `pickle_load`
- `parse_delta`
- `sliding_window`, `inverse_sliding_window`

Use `sliding_window()` to turn a continuous `[total_length, n_features]` series
into fixed-length samples before feeding a model. Use `inverse_sliding_window()`
only when you understand that overlap averaging, stride gaps, and dropped tails
can prevent exact reconstruction.
