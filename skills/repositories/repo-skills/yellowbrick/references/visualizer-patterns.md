# Yellowbrick Visualizer Patterns

## When to read

Read this before composing a Yellowbrick plot, embedding a visualizer in a
scikit-learn pipeline, saving figures in a headless environment, or choosing
where style/axes code belongs.

## Core lifecycle

Yellowbrick visualizers follow scikit-learn conventions but render Matplotlib
figures.

| Visualizer family | Typical lifecycle | Notes |
|---|---|---|
| Classifier/regressor score visualizers | `visualizer.fit(X_train, y_train)` then `visualizer.score(X_test, y_test)` then `visualizer.show(outpath=...)` | The wrapped estimator is fitted during `fit` unless `is_fitted=True` or `is_fitted="auto"` detects it. |
| Feature/target visualizers | `fit`, `transform`, `fit_transform`, or quick functions depending on class | They usually do not wrap predictive estimators. Keep feature names and labels aligned with columns/target values. |
| Clustering visualizers | `fit(X)` or `fit(X, y=None)` then `show` | Some compute many estimator fits over `k`, CV splits, or parameter ranges; bound them for smoke checks. |
| Text visualizers | vectorized matrices, token lists, tagged corpora, or raw documents depending on class | Optional parser/embedding dependencies are not installed by default. |
| Quick methods | `roc_auc(...)`, `residuals_plot(...)`, `kelbow_visualizer(...)` | Good for one-off reports; class APIs are better when an agent needs more control. |

`show(outpath=...)` saves the figure and returns the axes. Use
`clear_figure=True` when creating many plots in one process to avoid Matplotlib
state bleed. If a visualizer exposes `finalize()`, it is normally called by
`show()`; call it directly only when tests need to assert axes state without
saving or displaying.

## Headless rendering

Agents, CI jobs, and servers should force a non-interactive backend before any
`matplotlib.pyplot` import:

```python
import matplotlib
matplotlib.use("Agg", force=True)
```

Then save files explicitly:

```python
visualizer.fit(X_train, y_train)
visualizer.score(X_test, y_test)
visualizer.show(outpath="report.png", clear_figure=True)
```

Matplotlib may emit warnings about missing generic fonts such as Arial or
Liberation Sans. Treat those as appearance warnings if a non-empty output file
is produced; install fonts or set another font only when publication rendering
matters.

## Axes, figures, and style

- Pass `ax=` when composing Yellowbrick plots into a larger Matplotlib figure.
- Use `size=(width_px, height_px)` for visualizers that accept size in pixels.
- Use `set_aesthetic()`, `set_style()`, `set_palette()`, and `color_palette()`
  from `yellowbrick.style` for Yellowbrick's Seaborn-like style helpers.
- Prefer visualizer-level `colors`, `colormap`, `classes`, `features`, and
  `labels` arguments over ad-hoc Matplotlib edits when possible.
- When multiple visualizers are created in one script, close or clear figures
  after saving.

## Estimator wrapping and pipelines

Score visualizers wrap scikit-learn estimators. They proxy many estimator
attributes but still need the wrapped model to be compatible with the task:
classifiers for classifier visualizers, regressors for regression visualizers,
and clusterers for clustering visualizers.

Use `is_fitted=True` when a model has already been fitted and should not be
retrained. Use `is_fitted=False` to force fitting. The default `"auto"` asks
Yellowbrick to inspect the estimator.

For scikit-learn pipelines, put preprocessing before the model and wrap the
final estimator when the visualizer expects raw `X` values after preprocessing.
When using a `Pipeline` as the estimator, make sure the final step exposes the
methods required by the selected visualizer, such as `predict_proba` for ROC or
precision-recall curves.

## Data and label alignment

- Keep `X` and `y` lengths equal after filtering or splitting.
- Pass `classes=` or `labels=` when target values are encoded or when plots must
  show human-readable names.
- Pass `features=` or `feature_names=` when arrays do not preserve column names.
- For optional pandas workflows, ensure pandas is installed; otherwise use
  numpy arrays and explicit feature names.
- For downloaded Yellowbrick datasets, read the text/datasets sub-skill before
  relying on network fetches.

## Safe smoke-check pattern

Use a small synthetic dataset, one estimator fit, a non-interactive backend,
and an explicit output directory. The root `scripts/check_yellowbrick_visualizer.py`
and each sub-skill's script follow this pattern and avoid network, credentials,
large downloads, destructive writes, and long training.
