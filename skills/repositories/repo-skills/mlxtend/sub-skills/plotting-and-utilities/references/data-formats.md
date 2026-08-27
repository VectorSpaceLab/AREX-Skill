# Plotting and Utility Data Formats

Use this reference to check input and output shapes before calling plotting/data/file/text/math utility APIs.

## Plotting inputs

| Helper | Expected input | Notes |
|---|---|---|
| `plot_decision_regions` | `X`: numeric 2D array; `y`: 1D label array; `clf`: fitted object with `.predict` | For more than two features, select plotted columns with `feature_index` and provide filler values for every other feature. Labels should be discrete and preferably integer-coded. |
| `plot_confusion_matrix` | `conf_mat`: 2D square-like count matrix | Use `class_names` with length matching matrix dimension. `show_normed=True` annotates normalized values. |
| `heatmap`, `checkerboard_plot` | 2D numeric matrix/array | Optional row/column names should match matrix axes. |
| `category_scatter` | pandas DataFrame or mapping with x, y, and label columns | Number of markers/colors should cover categories, or categories will cycle. |
| `plot_sequential_feature_selection` | `metric_dict` from `SequentialFeatureSelector.get_metric_dict()` | Do not hand-build unless you match keys such as selected feature indices and average scores. |
| `plot_pca_correlation_graph` | `X`: samples x features; `variables_names`: one name per feature | `dimensions` are 1-based principal-component numbers such as `(1, 2)`. |
| `scatterplotmatrix` | 2D array/dataframe; optional `names` per feature | Use small feature counts for readability. |

## Dataset returns

Typical loaders return NumPy arrays:

| Loader | Expected return |
|---|---|
| `iris_data()` | `(X, y)` with 150 rows, 4 features, and labels. |
| `wine_data()` | `(X, y)` wine features and labels. |
| `three_blobs_data()` | `(X, y)` 2D cluster data. |
| `make_multiplexer_dataset(...)` | `(X, y)` binary multiplexer features and labels. |
| `mnist_data()` | `(X, y)` with 5000 rows and 784 pixel features. |
| `loadlocal_mnist(images_path, labels_path)` | Images/labels read from local IDX/ubyte files. |

Prefer `iris_data()` or `three_blobs_data()` for smoke checks; `mnist_data()` is still packaged but heavier.

## File grouping schemas

`find_files` returns a list of matching paths. Useful filters:

- `substring="sample"` means the basename/path must contain the substring.
- `recursive=True` descends into subdirectories.
- `check_ext=".csv"` restricts file extension.
- `ignore_invisible=True` skips dotfiles by default.

`find_filegroups(paths=[dir1, dir2, ...])` returns a dictionary:

```python
{
    "sample_a": ["dir1/sample_a.txt", "dir2/sample_a.csv"],
    "sample_b": ["dir1/sample_b.txt", "dir2/sample_b.csv"],
}
```

The first directory establishes group keys. Later directories add matching basenames. If `validity_check=True`, every key must have the same number of files.

## Text/name outputs

- `tokenizer_words_and_emoticons(text)` returns lowercase word tokens plus emoticons.
- `tokenizer_emoticons(text)` returns only emoticons.
- `generalize_names(name, output_sep=' ', firstname_output_letters=1)` emits a generalized name string; adjust `firstname_output_letters` for collision control.
- `generalize_names_duplcheck(df, col_name)` returns a dataframe-like result after name generalization and duplicate handling.

## Math/vector inputs

- `num_combinations(n, k, with_replacement=False)` and `num_permutations(n, k, with_replacement=False)` expect nonnegative integer counts.
- `vectorspace_orthonormalization(ary, eps=1e-13)` expects vectors as array columns.
- `vectorspace_dimensionality(ary)` measures span/hyper-volume of vector columns; ensure numeric finite input.

## Utility array contracts

- `check_Xy(X, y, y_int=True)` is for supervised-learning arrays. If `y_int=True`, labels should be integer-like.
- `format_kwarg_dictionaries(default_kwargs, user_kwargs, protected_keys)` returns a merged kwargs dictionary and should not silently override protected keys.
- `Counter` is a progress helper, not a data structure replacement.
