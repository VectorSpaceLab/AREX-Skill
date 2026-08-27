# Plotting and Utilities Workflows

Use these recipes when a task asks for mlxtend visualization, packaged datasets, local-file grouping, text/name helpers, math helpers, or small utility diagnostics.

## Headless plotting baseline

For scripts, CI, remote servers, and notebooks without a display:

```python
import matplotlib
matplotlib.use("Agg")  # before pyplot
import matplotlib.pyplot as plt
```

Or in a shell:

```bash
MPLBACKEND=Agg python your_script.py
```

Prefer saving and closing figures:

```python
fig.savefig("plot.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

## Confusion matrices and heatmaps

Use `mlxtend.plotting.plot_confusion_matrix` when you already have a confusion matrix from `mlxtend.evaluate.confusion_matrix`, sklearn, or another source:

```python
import numpy as np
from mlxtend.plotting import plot_confusion_matrix

conf_mat = np.array([[12, 2], [3, 9]])
fig, ax = plot_confusion_matrix(
    conf_mat=conf_mat,
    class_names=["negative", "positive"],
    show_absolute=True,
    show_normed=True,
    colorbar=True,
)
fig.savefig("confusion-matrix.png", dpi=150, bbox_inches="tight")
```

For a generic 2D numeric table:

```python
from mlxtend.plotting import heatmap
fig, ax = heatmap(matrix=conf_mat, row_names=["actual 0", "actual 1"], column_names=["pred 0", "pred 1"])
```

Route metric or confusion-matrix construction to `../evaluation-and-validation/SKILL.md`; this sub-skill owns visualization.

## Decision regions

Use `plot_decision_regions` with a fitted classifier and numeric data. The safest recipe is 2D features:

```python
from sklearn.linear_model import LogisticRegression
from mlxtend.data import iris_data
from mlxtend.plotting import plot_decision_regions

X, y = iris_data()
X2 = X[:, [0, 2]]
clf = LogisticRegression(max_iter=200).fit(X2, y)
ax = plot_decision_regions(X2, y, clf=clf, legend=2)
ax.figure.savefig("decision-regions.png", dpi=150, bbox_inches="tight")
```

For more than two features, select two with `feature_index=(i, j)` and provide constant filler values/ranges for every remaining feature. If the task is about fitting the estimator, route to `../estimators-and-ensembles/SKILL.md` first.

## Learning curves, SFS plots, and PCA correlation graphs

- `plot_learning_curves(X_train, y_train, X_test, y_test, clf, ...)` fits the classifier repeatedly across training sizes. Use small data and route estimator/scoring choices to sibling sub-skills.
- `plot_sequential_feature_selection(metric_dict, ...)` expects `metric_dict = sfs.get_metric_dict()` from `SequentialFeatureSelector`; build the selector in `../feature-workflows/SKILL.md`.
- `plot_pca_correlation_graph(X, variables_names, dimensions=(1, 2), ...)` computes or displays a PCA correlation graph. `variables_names` length must match the number of input columns.

## Scatter and distribution plots

Use these for lightweight data exploration:

```python
from mlxtend.plotting import category_scatter, ecdf, scatterplotmatrix, scatter_hist

# DataFrame category plot
category_scatter(x="feature_1", y="feature_2", label_col="class", data=df)

# ECDF and scatter/hist plots
ecdf(df["feature_1"].to_numpy(), x_label="feature_1")
scatter_hist(df["feature_1"], df["feature_2"])
scatterplotmatrix(df[["feature_1", "feature_2", "feature_3"]].to_numpy(), names=["f1", "f2", "f3"])
```

Close figures when generating many plots.

## Packaged datasets

Use mlxtend datasets for tiny examples and smoke tests:

```python
from mlxtend.data import iris_data, three_blobs_data, make_multiplexer_dataset

X_iris, y_iris = iris_data()
X_blob, y_blob = three_blobs_data()
X_mux, y_mux = make_multiplexer_dataset(address_bits=2, sample_size=16, random_seed=1)
```

`mnist_data()` reads packaged 5k-sample MNIST data and is heavier than `iris_data`. `loadlocal_mnist(images_path, labels_path)` reads local IDX/ubyte files; it does not download data.

## File grouping

Use `find_files` for single-directory filename search and `find_filegroups` when multiple directories share base names:

```python
from mlxtend.file_io import find_files, find_filegroups

csvs = find_files(substring="sample", path="data", recursive=True, check_ext=".csv")
groups = find_filegroups(
    paths=["images", "labels"],
    extensions=[".png", ".txt"],
    validity_check=True,
)
```

If group counts differ, either fix missing files or rerun with `validity_check=False` only when partial groups are acceptable.

## Text and name helpers

```python
from mlxtend.text import tokenizer_words_and_emoticons, tokenizer_emoticons, generalize_names

tokens = tokenizer_words_and_emoticons("MLxtend is fun :-)")
emoticons = tokenizer_emoticons("ok :-) nope :-(")
name = generalize_names("Ada Lovelace", firstname_output_letters=1)
```

Use `generalize_names_duplcheck(df, col_name)` when duplicate detection after name generalization matters.

## Math and vector-space helpers

```python
from mlxtend.math import num_combinations, num_permutations, vectorspace_orthonormalization

n_pairs = num_combinations(5, 2)
n_ordered = num_permutations(5, 2)
orth_basis = vectorspace_orthonormalization(array)
```

These helpers are convenience utilities; for large numerical workloads prefer NumPy/SciPy directly unless mlxtend's exact behavior is needed.

## Small utils

- Use `format_kwarg_dictionaries(default_kwargs, user_kwargs, protected_keys)` when merging plotting kwargs and preserving protected keys.
- Use `check_Xy(X, y)` to validate supervised arrays before calling mlxtend estimators or plotting helpers.
- Use `Counter` only for interactive progress; avoid noisy progress counters in quiet automation.
