# Dataset and metric API reference

These signatures and behaviors are for AIX360 0.3.0. Import the class from
`aix360.datasets` only when the release exports it; otherwise import its
specific `aix360.datasets.<module>` module. Do not infer availability from the
Sphinx dataset list: the package initializer uses broad `try/except` imports,
so missing optional dependencies can make a class silently absent.

## Constructors and methods

| API | Signature | Important result or side effect |
|---|---|---|
| `HELOCDataset` | `(custom_preprocessing=default_preprocessing, dirpath=None)` | Reads `<dirpath>/heloc_dataset.csv`; `dataframe()` returns raw frame with target last; `data()` returns callback output; `split(random_state=0)` returns processed data, feature splits, and one-hot labels. |
| `COMPASDataset` | `(custom_preprocessing=default_preprocessing, dirpath=None)` | Reads `<dirpath>/compas.csv`; `dataframe()` and `data()` expose the processed frame. Missing data prints a message and exits the process in the current implementation, so validate first. |
| `MEPSDataset` | `(custom_preprocessing=default_preprocessing, dirpath=None)` | Reads `<dirpath>/h181.csv`; `data()` returns the processed frame. Source error text incorrectly mentions a HELOC filename; trust the expected `h181.csv` contract instead. |
| `AdultDataset` | `(custom_preprocessing=default_preprocessing, dirpath=None)` | Direct-module class; reads `<dirpath>/adult.csv` headerless with whitespace parsing and returns callback output through `data()`/`dataframe()`. |
| `TEDDataset` | `(dirpath=None)` | `load_file(fileName='Retention.csv') -> (X,Y,E)`; no download. |
| `MNISTDataset` | `(custom_preprocessing=None, dirpath=None)` | Reads/downloads four gzip files; public attributes are `train_data`, `train_labels`, `validation_data`, `validation_labels`, `test_data`, and `test_labels`. `custom_preprocessing` is accepted but unused. |
| `FMnistDataset` | `(batch_size=256, subset_size=50000, test_batch_size=256, dirpath=None)` | Requires torch/torchvision; creates `train_loader`/`test_loader` with download enabled. `next_batch()` and `next_test_batch()` are generators. |
| `CIFARDataset` | `(dirpath=None)` | Reads/writes processed JSON and may download/process a tar archive; `load_file(filename)` returns a NumPy array from a JSON file. |
| `CelebADataset` | `(dirpath=None)` | `get_img(img_id)` loads `<id>_img.npy`; `get_latent(img_id)` loads `<id>_latent.npy` and casts `float32`. |
| `eSNLIDataset` | `()` | `get_example(example_id: str) -> Dict`; fixed `docs.jsonl` location, no `dirpath`. |
| `CDCDataset` | `(custom_preprocessing=default_preprocessing, dirpath=None)` | Downloads/converts a fixed NHANES questionnaire set when missing; `get_csv_file(filename) -> DataFrame`; `get_csv_file_names() -> list[str]`. `custom_preprocessing` is currently not applied. |
| `FordDataset` | `(url: str=None, category_a: bool=True)` | Downloads missing Ford files from an allow-listed HTTPS host; `load_data() -> (x_train,x_test,y_train,y_test)` with `(n,500,1)` inputs. No `dirpath` parameter. |
| `SunspotDataset` | `(url: str=None)` | Downloads a cache if missing; `load_data() -> (DataFrame, schema_dict)`. No `dirpath` parameter. |
| `ClimateDataset` | `(url: str=None)` | Requires TensorFlow at module import, downloads a fixed ZIP if missing; `load_data(return_train=False, test_start=None) -> dict`. No `dirpath` parameter. |
| `DiabetesDataset` | `(url: str=None)` | Downloads a tab-delimited source if missing; `load_data(return_only_numerical=True, test_size=0.3, random_state=None)` returns `(x_train,x_test,y_train,y_test,feature_names,target_names)`. No `dirpath` parameter. |

The package initializer exports `CDCDataset`, `CIFARDataset`, `CelebADataset`,
`DiabetesDataset`, `FordDataset`, `HELOCDataset`, `MEPSDataset`,
`MNISTDataset`, `SunspotDataset`, `TEDDataset`, and `eSNLIDataset` when their
imports succeed in this release. `AdultDataset`, `ClimateDataset`, and
`FMnistDataset` are not exported there; direct module imports can still fail if
TensorFlow, torch, or torchvision is absent.

## Metric signatures and exact semantics

```python
from aix360.metrics import faithfulness_metric, monotonicity_metric

score = faithfulness_metric(model, x, coefs, base)
ok = monotonicity_metric(model, x, coefs, base)
```

Required model behavior:

- `model.predict_proba(one_row)` returns a 2-D array whose second dimension is
  the class-probability axis.
- `x` is a one-dimensional numeric row. The implementation calls
  `x.reshape(1, -1)` and creates one probability query per feature.
- `coefs` and `base` must each have exactly `x.shape[0]` entries and use the
  same feature order as `x`. `base[j]` is the replacement/absence value for
  feature `j`, not necessarily a statistical mean.

`faithfulness_metric` first selects `pred_class = argmax(model.predict_proba(x
.reshape(1,-1)), axis=1)[0]`. It sorts coefficient indices in descending signed
coefficient order, replaces each feature in a copy of `x` with its base value,
and stores the predicted-class probability at that feature index. It returns
`-np.corrcoef(coefs, pred_probs)[0, 1]`. The sorting affects query order but not
the final correlation because `pred_probs` is restored to feature positions.

`monotonicity_metric` selects the same predicted class, starts from a copy of
`base`, sorts indices in ascending signed coefficient order, inserts the real
feature value one feature at a time, and returns
`np.all(np.diff(pred_probs[sorted_indices]) >= 0)`. A `True` result means only
that this finite sequence was non-decreasing for this row and base; it is not a
proof that the model is globally monotone.

## Alignment and sanity checks

Before calling either metric:

```python
import numpy as np

x = np.asarray(x, dtype=float).reshape(-1)
coefs = np.asarray(coefs, dtype=float).reshape(-1)
base = np.asarray(base, dtype=float).reshape(-1)
assert x.size == coefs.size == base.size
assert np.isfinite(x).all() and np.isfinite(coefs).all() and np.isfinite(base).all()
proba = np.asarray(model.predict_proba(x.reshape(1, -1)))
assert proba.ndim == 2 and proba.shape[0] == 1 and proba.shape[1] >= 2
```

Use `np.isfinite(score)` as a postcondition for faithfulness when the
coefficient and probability vectors are non-constant. A constant `coefs` or
constant `pred_probs` makes Pearson correlation undefined and can yield `nan`.
For monotonicity, inspect the ordered probability sequence if the boolean is
unexpected; do not reverse the order merely because a domain explanation uses
absolute magnitudes.
