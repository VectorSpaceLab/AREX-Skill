# Troubleshooting: plotting and utilities

Use this reference when a plotting/data/file/text/math utility call fails or produces an unexpected return object.

## Display and backend issues

### Symptom: `ImportError`, `TclError`, blank windows, or hangs in headless jobs

Cause: Matplotlib is trying to use an interactive backend without a display.

Fix:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
```

Set this before importing `matplotlib.pyplot`. Save figures with `fig.savefig(...)` and close them with `plt.close(fig)` instead of relying on `plt.show()`.

### Symptom: too many open figures or memory growth

Close every created figure after saving:

```python
fig.savefig("out.png")
plt.close(fig)
```

For helpers that return an `Axes` or artist, recover the figure first:

```python
fig = ax.figure
fig = artist.axes.figure
```

## Figure and axes return pitfalls

| Helper | Common mistake | Correct handling |
|---|---|---|
| `plot_decision_regions` | Assigning result to `fig`. | It returns `Axes`: `ax = plot_decision_regions(...); ax.figure.savefig(...)`. |
| `plot_confusion_matrix` / `heatmap` | Ignoring the tuple. | Capture `fig, ax = ...`. |
| `plot_sequential_feature_selection` | Expecting a bare `Figure` because docs say `fig`. | Current implementation returns `plt.subplots()`, so capture `fig, ax = ...`. |
| `plot_linear_regression` | Expecting a figure. | It returns `(intercept, slope, corr_coeff)` and draws on current pyplot state; use `plt.gcf()` to save. |
| `scatter_hist` | Expecting a figure. | It returns the scatter artist; use `artist.axes.figure`. |
| `remove_borders` | Passing one axes object directly. | Pass an iterable, e.g. `remove_borders([ax])`. |

## Decision-region errors

### `ValueError: X must be a 2D array`

`plot_decision_regions` calls `check_Xy`. Use a 2D array even for one feature:

```python
X_one = X[:, [0]]      # ok
# not X[:, 0]          # 1D, fails
```

### `ValueError: y must be a NumPy array` or integer array

Convert labels before plotting:

```python
y = np.asarray(y).astype(np.int_)
```

Labels should be 1D and integer. Non-consecutive or large integer labels can make color/level behavior surprising; prefer compact labels such as `0..n_classes-1` or supply enough `colors` and `markers`.

### `Filler values must be provided when X has more than 2 training features`

For high-dimensional `X`, choose exactly two plotted features and fill all other columns:

```python
plot_decision_regions(
    X=X,
    y=y,
    clf=clf,
    feature_index=(0, 2),
    filler_feature_values={1: 0.0, 3: 1.0},
)
```

If some columns are missing from both `feature_index` and `filler_feature_values`, the helper raises a missing-column error.

### `filler_feature_values and filler_feature_ranges must have the same keys`

Use identical keys in both dictionaries:

```python
filler_feature_values = {1: 0.0, 3: 1.0}
filler_feature_ranges = {1: 0.5, 3: 0.5}
```

### Training points disappear on high-dimensional decision plots

When `X.shape[1] > 2` and no `filler_feature_ranges` is supplied, decision regions can draw while training samples are skipped. Supply ranges to select samples close to the filler values.

### `feature_index` errors

- `feature_index` must unpack to exactly two entries for multidimensional data.
- Each index must be within `0 <= index < X.shape[1]`.
- Do not set `feature_index` for a one-feature `X`; the helper rejects it.

### `Number of defined CPU cores is more than the available resources`

Set `n_jobs=None`, `n_jobs=1`, or `n_jobs=-1`. A positive `n_jobs` larger than the host CPU count raises.

## Confusion matrix and heatmap issues

### `Both show_absolute and show_normed are False`

At least one text display mode must be active:

```python
plot_confusion_matrix(conf_mat, show_absolute=True, show_normed=False)
```

### `class_names` length assertion

`len(class_names)` must equal the number of classes/rows in `conf_mat`.

### Heatmap row/column assertion

`row_names` must match `matrix.shape[0]`; `column_names` must match `matrix.shape[1]`.

### All-zero heatmap displays bad text colors or warnings

`heatmap` normalizes cell text colors by `matrix.max()`. For all-zero matrices, either skip cell text (`cell_values=False`), provide `text_color_threshold`, or plot a matrix with a nonzero scale.

## PCA correlation graph issues

- If `X_pca` is provided, `explained_variance` must also be provided.
- If `explained_variance` is provided, `X_pca` must also be provided.
- `X_pca.shape[1]` must equal `len(explained_variance)`.
- `max(dimensions)` must be available in both `X_pca` and `explained_variance`.
- `dimensions` are 1-based, so `(1, 2)` means first and second PCA dimensions.

## Dataset shape and path issues

### Packaged loader returns unexpected shape

Use the verified shapes in [data-formats.md](data-formats.md#dataset-return-shapes). Common checks:

```python
X, y = iris_data()
assert X.shape == (150, 4)
assert y.shape == (150,)
```

### `iris_data(version=...)` raises `ValueError`

Only `version='uci'` and `version='corrected'` are valid.

### `autompg_data()` contains `nan`

This version parses the car-name string field through a float loader, so one returned feature column is `nan`. Drop or impute that column before numeric modeling.

### `mnist_data()` is slower or memory-heavy

`mnist_data()` loads a packaged `(5000, 784)` array. Use `iris_data()` or `three_blobs_data()` for fast smoke tests unless MNIST shape behavior is specifically needed.

### `loadlocal_mnist` fails with `FileNotFoundError` or reshape errors

`loadlocal_mnist` needs existing local IDX/ubyte files. It assumes 28x28 images and reshapes to 784 pixels per label:

```python
images, labels = loadlocal_mnist("train-images-idx3-ubyte", "train-labels-idx1-ubyte")
```

Check that files are uncompressed, paths are correct, and label count matches image byte count.

## File glob and grouping issues

### `find_files` misses files

- `substring` must appear in the file name.
- `check_ext` is exact and should include the dot, e.g. `'.txt'`.
- In non-recursive mode, hidden files starting with `.` are skipped by default; set `ignore_invisible=False` if you need them.
- In recursive mode, current source may include hidden files even when `ignore_invisible=True`; filter after the call if this matters.

### `find_filegroups` raises `AssertionError`

- `paths` must contain at least two directories.
- If `extensions` is supplied, `len(extensions)` must equal `len(paths)`.

### `find_filegroups` raises `ValueError` about unequal values

With `validity_check=True`, every key from the first directory must have the same number of grouped files. Fix missing partner files or set `validity_check=False` when partial groups are acceptable.

### `find_filegroups` raises `TypeError: 'module' object is not callable`

Inspected 0.25.0 behavior can bind the internal `find_files` helper as a module. Use a compatibility wrapper:

```python
import importlib
from mlxtend.file_io import find_filegroups, find_files


def find_filegroups_compatible(*args, **kwargs):
    try:
        return find_filegroups(*args, **kwargs)
    except TypeError as exc:
        if "'module' object is not callable" not in str(exc):
            raise
        module = importlib.import_module("mlxtend.file_io.find_filegroups")
        module.find_files = find_files
        return module.find_filegroups(*args, **kwargs)
```

This preserves the intended public behavior without reading any source checkout files.

## Tokenizer and name-generalization edge cases

- `tokenizer_words_and_emoticons` lowercases words, strips HTML-like tags, removes most punctuation from word tokens, and appends recognized emoticons.
- `tokenizer_emoticons` only returns recognized emoticons; it does not return words.
- `generalize_names` removes accents and punctuation, lowercases, handles comma-separated order, and joins particles such as `van der` into the last name.
- Single-token names return the normalized token unchanged.
- `generalize_names_duplcheck` drops exact duplicate source names before resolving generalized-name duplicates by using more first-name letters. If other DataFrame columns matter, remember that dropped duplicate rows disappear from the returned DataFrame.

## Math/counting/linalg issues

- `factorial`, `num_combinations`, and `num_permutations` do not robustly validate inputs. Pass non-negative integers and keep `k <= n` when `with_replacement=False`.
- Very large `n`/`k` values can be slow because `factorial` is recursive.
- `vectorspace_orthonormalization` treats columns as vectors; if your vectors are rows, transpose first.
- Linearly dependent columns become zero columns after orthonormalization.
- Use numeric NumPy arrays; object/string arrays will fail in NumPy operations.

## Utility helper issues

### `check_Xy` rejects valid-looking arrays

Review the exact schema:

```python
X = np.asarray(X)
y = np.asarray(y)
assert X.ndim == 2
assert y.ndim == 1
assert X.shape[0] == y.shape[0]
```

If labels are floats but intended as classes, cast to integer. If regression-style float targets are intentional for a direct `check_Xy` call, pass `y_int=False`; `plot_decision_regions` always requires integer labels through its internal call.

### `format_kwarg_dictionaries` drops keys

Protected keys are removed after merging defaults and user values. This is intentional for wrappers that reserve Matplotlib keys such as `colors`, `levels`, `c`, `marker`, or `label`.

### `Counter` prints during tests

Redirect stdout/stderr or construct with `stderr=True` and capture stderr. `Counter.update()` has the side effect of writing progress text on every call.
