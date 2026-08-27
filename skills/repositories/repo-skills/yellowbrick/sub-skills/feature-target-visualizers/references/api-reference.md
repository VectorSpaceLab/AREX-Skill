# Feature and Target Visualizer API Reference

This reference summarizes the Yellowbrick feature and target diagnostics owned by this sub-skill. Use it together with the shared lifecycle/headless guidance in [visualizer patterns](../../../references/visualizer-patterns.md).

## Imports

```python
from yellowbrick.features import (
    Rank1D, Rank2D, rank1d, rank2d,
    RadialVisualizer, RadViz, radviz,
    ParallelCoordinates, parallel_coordinates,
    PCA, PCADecomposition, pca_decomposition,
    Manifold, manifold_embedding,
    JointPlot, JointPlotVisualizer, joint_plot,
)

from yellowbrick.target import (
    ClassBalance, class_balance,
    BalancedBinningReference, balanced_binning_reference,
    FeatureCorrelation,
)
from yellowbrick.target.feature_correlation import feature_correlation
```

Notes:

- `RadViz` is an alias for `RadialVisualizer`.
- `PCADecomposition` is an alias for `PCA`.
- `JointPlotVisualizer` is an alias for `JointPlot`.
- The `FeatureCorrelation` class is available from `yellowbrick.target`; the quick helper is safest to import from `yellowbrick.target.feature_correlation`.

## Feature ranking visualizers

| Visualizer | Constructor shape | Fit/draw behavior | Main options | Use when |
|---|---|---|---|---|
| `Rank1D` | `Rank1D(ax=None, algorithm="shapiro", features=None, orient="h", show_feature_names=True, color=None, **kwargs)` | Call `fit(X, y=None)` to validate feature names, then `transform(X)` to compute `ranks_`, draw bars, and return `X` unchanged. | `algorithm="shapiro"`; `orient="h"` or `"v"`; `features` length must match `X.shape[1]`. | Rank each feature independently, usually for distribution/normality screening. |
| `Rank2D` | `Rank2D(ax=None, algorithm="pearson", features=None, colormap="RdBu_r", show_feature_names=True, **kwargs)` | Call `fit(X, y=None)`, then `transform(X)` to compute a square `ranks_` matrix, draw the lower-triangle heatmap, and return `X` unchanged. | `algorithm` in `{"pearson", "covariance", "spearman", "kendalltau"}`. | Inspect pairwise correlation/covariance-style relationships among columns. |

Quick helpers: `rank1d(X, y=None, ..., show=True)` and `rank2d(X, y=None, ..., show=True)`. For saving to files, prefer the class API or keep the returned visualizer and call `show(outpath=...)` yourself.

## Raw feature-space visualizers

| Visualizer | Constructor shape | Fit/draw behavior | Main options | Use when |
|---|---|---|---|---|
| `RadialVisualizer` / `RadViz` | `RadialVisualizer(ax=None, features=None, classes=None, colors=None, colormap=None, alpha=1.0, **kwargs)` | `fit(X, y)` validates discrete targets, internally min-max normalizes features for plotting, draws points inside a feature anchor circle, and returns self. `transform(X)` passes data through. | `features`, `classes`, `colors`, `colormap`, `alpha`. Defaults to discrete target handling. | See whether classes separate when all features pull points around a circle. |
| `ParallelCoordinates` | `ParallelCoordinates(ax=None, features=None, classes=None, normalize=None, sample=1.0, random_state=None, shuffle=False, colors=None, colormap=None, alpha=None, fast=False, vlines=True, vlines_kwds=None, **kwargs)` | `fit(X, y)` validates target/colors, optionally subsamples and normalizes, draws class-colored lines, and returns self. `transform(X)` passes data through. | `normalize` in `{None, "minmax", "maxabs", "standard", "l1", "l2"}`; `sample` as count or fraction; `shuffle`; `fast`. | Compare many features across classes; use `sample` or `fast=True` when there are too many rows. |

Quick helpers: `radviz(X, y, ..., show=True)` and `parallel_coordinates(X, y, ..., show=True)`.

## Projection visualizers

| Visualizer | Constructor shape | Transform behavior | Main options | Use when |
|---|---|---|---|---|
| `PCA` | `PCA(ax=None, features=None, classes=None, scale=True, projection=2, proj_features=False, colors=None, colormap=None, alpha=0.75, random_state=None, colorbar=True, heatmap=False, **kwargs)` | `fit(X, y=None)` fits a scaler/PCA pipeline and records `pca_components_`; `transform(X, y=None)` draws and returns an array of shape `(n_samples, projection)`; `fit_transform(X, y=None)` does both. | `projection=2` or `3`; `scale`; `proj_features` for biplot-like arrows; `heatmap=True` only with 2D; pass `target_type` through `**kwargs` if auto target inference is ambiguous. | Fast first-pass linear projection, feature loadings, or lower-dimensional exploratory plot. |
| `Manifold` | `Manifold(ax=None, manifold="mds", n_neighbors=None, features=None, classes=None, colors=None, colormap=None, target_type="auto", projection=2, alpha=0.75, random_state=None, colorbar=True, **kwargs)` | `fit_transform(X, y=None)` fits, draws, records `fit_time_`, and returns the embedding. A separate `fit()`/`transform()` only works for algorithms whose sklearn transformer implements `transform`. | `manifold` in `{"lle", "ltsa", "hessian", "modified", "isomap", "mds", "spectral", "tsne"}` or a transformer instance; `n_neighbors`; `target_type`; `projection`; `random_state`. | Non-linear structure exploration when runtime cost is acceptable. Start small and explicit. |

Manifold algorithm caveats:

- `lle`, `ltsa`, `hessian`, `modified`, and `isomap` support a separate `transform()` path after `fit()` in the tested API surface.
- `mds`, `spectral`, and `tsne` require simultaneous fitting and transforming; call `fit_transform()` rather than `fit()` then `transform()`.
- Neighbor-based algorithms warn and choose defaults when `n_neighbors` is omitted: generally 5, with a larger default for Hessian LLE.
- Use `target_type="discrete"` for class labels and `target_type="continuous"` for regression/ordered targets; avoid relying on old snippets that use a `target=` keyword.

Quick helpers: `pca_decomposition(X, y=None, ..., show=True)` and `manifold_embedding(X, y=None, ..., show=True)`.

## Joint feature/target plot

| Visualizer | Constructor shape | Fit behavior | Main options | Use when |
|---|---|---|---|---|
| `JointPlot` | `JointPlot(ax=None, columns=None, correlation="pearson", kind="scatter", hist=True, alpha=0.65, joint_kws=None, hist_kws=None, **kwargs)` | `fit(X, y=None)` selects one or two variables, draws a scatter or hexbin joint plot, optionally draws marginal histograms, and records `corr_`. | `columns=None`, one column, or two columns; `correlation` in `{"pearson", "covariance", "spearman", "kendalltau"}`; `kind="scatter"`, `"hex"`, or `"hexbin"`; `hist=True`, `False`, `None`, `"density"`, or `"frequency"`. | Inspect a single pair of features or feature-vs-target relationship with marginal distributions. |

Column rules:

- `columns=None`: either pass `X` as a two-column matrix with no `y`, or pass one-dimensional `X` and one-dimensional `y`.
- `columns=<single index/name>`: pass a 2D `X` and a one-dimensional `y`; the selected feature is plotted against the target.
- `columns=[left, right]`: pass a 2D `X`; the two selected features are plotted against each other. In this API surface, `y` does not color the paired feature plot.

Quick helper: `joint_plot(X, y, ..., show=True)`.

## Target visualizers

| Visualizer | Constructor shape | Fit behavior | Main options | Use when |
|---|---|---|---|---|
| `ClassBalance` | `ClassBalance(ax=None, labels=None, colors=None, colormap=None, **kwargs)` | `fit(y_train, y_test=None)` expects one-dimensional binary or multiclass targets. With only `y_train`, draws balance mode; with both train/test targets, draws compare mode. | `labels` must match the discovered classes and be ordered consistently with target values, such as `LabelEncoder.classes_`. | Check imbalance before modeling or compare train/test support after splitting. |
| `BalancedBinningReference` | `BalancedBinningReference(ax=None, target=None, bins=4, **kwargs)` | `fit(y)` expects a one-dimensional numeric target, draws a histogram, stores `bin_edges_`, and marks bin reference lines. | `target` is the x-axis label; `bins` controls the histogram/reference count. | Choose target bins for regression-to-classification or stratified analysis. |
| `FeatureCorrelation` | `FeatureCorrelation(ax=None, method="pearson", labels=None, sort=False, feature_index=None, feature_names=None, color=None, **kwargs)` | `fit(X, y, **kwargs)` computes feature-to-target scores, draws horizontal bars, and stores `features_` and `scores_`. | `method` in `{"pearson", "mutual_info-regression", "mutual_info-classification"}`; `labels`; `sort`; `feature_index`; `feature_names`. | Rank features by linear correlation or mutual information against a dependent variable. |

Quick helpers: `class_balance(y_train, y_test=None, ..., show=True)`, `balanced_binning_reference(y, ..., show=True)`, and `feature_correlation(X, y, ..., show=True)`.
