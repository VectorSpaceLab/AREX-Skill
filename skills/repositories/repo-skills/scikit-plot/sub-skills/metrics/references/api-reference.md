# Metrics API reference

Source anchors: `scikitplot/metrics.py`, `scikitplot/helpers.py`, `docs/metrics.rst`, `docs/functionsapidocs.rst`, `scikitplot/tests/test_metrics.py`, and the metric example programs.

All plotting functions return the Matplotlib `Axes` they draw on. If `ax=None`, scikit-plot creates a new figure and axes.

## Classification label and probability plots

### `plot_confusion_matrix`

```python
plot_confusion_matrix(
    y_true,
    y_pred,
    labels=None,
    true_labels=None,
    pred_labels=None,
    title=None,
    normalize=False,
    hide_zeros=False,
    hide_counts=False,
    x_tick_rotation=0,
    ax=None,
    figsize=None,
    cmap='Blues',
    title_fontsize='large',
    text_fontsize='medium',
)
```

- `labels` controls matrix index order.
- `true_labels` and `pred_labels` subset display rows/columns and are validated for duplicates and missing values.
- `normalize=True` normalizes by row and rounds to two decimals.
- `hide_zeros` suppresses zero cells; `hide_counts` suppresses all cell text.

### `plot_roc`

```python
plot_roc(
    y_true,
    y_probas,
    title='ROC Curves',
    plot_micro=True,
    plot_macro=True,
    classes_to_plot=None,
    ax=None,
    figsize=None,
    cmap='nipy_spectral',
    title_fontsize='large',
    text_fontsize='medium',
)
```

- `y_probas` must be a 2-D matrix with one probability/score column per class.
- `plot_micro` and `plot_macro` control aggregate curves.
- `classes_to_plot` can restrict which class curves are displayed; classes not present are ignored.
- Legacy `plot_roc_curve(y_true, y_probas, curves=('micro', 'macro', 'each_class'), ...)` is still present but deprecated in favor of `plot_roc`.

### `plot_precision_recall`

```python
plot_precision_recall(
    y_true,
    y_probas,
    title='Precision-Recall Curve',
    plot_micro=True,
    classes_to_plot=None,
    ax=None,
    figsize=None,
    cmap='nipy_spectral',
    title_fontsize='large',
    text_fontsize='medium',
)
```

- `y_probas` follows the same `(n_samples, n_classes)` convention as ROC.
- `plot_micro` controls the micro-average curve.
- `classes_to_plot` filters class-specific curves.
- Legacy `plot_precision_recall_curve(y_true, y_probas, curves=('micro', 'each_class'), ...)` is still present but deprecated in favor of `plot_precision_recall`.

## Binary probability diagnostics

### `plot_ks_statistic`

```python
plot_ks_statistic(y_true, y_probas, title='KS Statistic Plot', ax=None, figsize=None, title_fontsize='large', text_fontsize='medium')
```

- Requires exactly two classes in `y_true`.
- Uses the positive-class probability column `y_probas[:, 1]`.
- Raises `ValueError` when more than two categories are present.

### `plot_calibration_curve`

```python
plot_calibration_curve(y_true, probas_list, clf_names=None, n_bins=10, title='Calibration plots (Reliability Curves)', ax=None, figsize=None, cmap='nipy_spectral', title_fontsize='large', text_fontsize='medium')
```

- Requires binary `y_true`.
- With modern scikit-learn, string labels such as `{'A', '1'}` may fail because `calibration_curve` cannot infer `pos_label`; encode the binary target as `{0, 1}` or `{-1, 1}` before calling this scikit-plot wrapper.
- `probas_list` must be a Python list; each item can be a 2-D probability array or 1-D decision scores.
- `clf_names`, when supplied, must have the same length as `probas_list`.
- Every probability/score vector must match the shape of `y_true` after optional column extraction.

### `plot_cumulative_gain` and `plot_lift_curve`

```python
plot_cumulative_gain(y_true, y_probas, title='Cumulative Gains Curve', ax=None, figsize=None, title_fontsize='large', text_fontsize='medium')
plot_lift_curve(y_true, y_probas, title='Lift Curve', ax=None, figsize=None, title_fontsize='large', text_fontsize='medium')
```

- Both functions require binary `y_true`.
- Both use the two columns of `y_probas` to compute class-specific curves.
- Both raise `ValueError` for multiclass data.

## Clustering metric plot

### `plot_silhouette`

```python
plot_silhouette(X, cluster_labels, title='Silhouette Analysis', metric='euclidean', copy=True, ax=None, figsize=None, cmap='nipy_spectral', title_fontsize='large', text_fontsize='medium')
```

- `X` is the feature matrix used by `sklearn.metrics.silhouette_score` and `silhouette_samples`.
- `cluster_labels` must align one-to-one with rows in `X`.
- `metric` is forwarded to sklearn pairwise-distance scoring.

## Helper functions

`binary_ks_curve`, `cumulative_gain_curve`, and `validate_labels` are supporting helpers. Mention them only when diagnosing a failed metric plot; ordinary users should call the plotting functions above.
