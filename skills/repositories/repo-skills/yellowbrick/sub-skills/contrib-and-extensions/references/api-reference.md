# Contrib API Reference

This reference records the concrete contrib import paths and signatures to use in
runtime guidance. The top-level `yellowbrick.contrib` package does not hoist
these classes.

## Import map

```python
from yellowbrick.contrib.scatter import ScatterVisualizer, ScatterViz, scatterviz
from yellowbrick.contrib.classifier.boundaries import (
    DecisionBoundariesVisualizer,
    decisionviz,
)
from yellowbrick.contrib.classifier import DecisionViz
from yellowbrick.contrib.missing import (
    MissingValuesBar,
    MissingValuesDispersion,
    missing_bar,
    missing_dispersion,
)
from yellowbrick.contrib.prepredict import PrePredict
from yellowbrick.contrib.wrapper import (
    ContribEstimator,
    wrap,
    classifier,
    regressor,
    clusterer,
    CLASSIFIER,
    REGRESSOR,
    CLUSTERER,
    DENSITY_ESTIMATOR,
    OUTLIER_DETECTOR,
)
from yellowbrick.contrib.statsmodels import StatsModelsWrapper
```

Avoid `from yellowbrick.contrib import ScatterVisualizer`,
`PrePredict`, `ContribEstimator`, or `StatsModelsWrapper`; those imports fail.

## Scatter visualizer

| Object | Signature | Notes |
|---|---|---|
| `ScatterVisualizer` | `(ax=None, x=None, y=None, features=None, classes=None, color=None, colormap=None, markers=None, alpha=1.0, **kwargs)` | Bivariate data visualizer for exactly two plotted features. |
| `ScatterViz` | alias of `ScatterVisualizer` | Legacy alias. |
| `scatterviz` | `(X, y=None, ax=None, features=None, classes=None, color=None, colormap=None, markers=None, alpha=1.0, **kwargs)` | Quick method; returns the fitted `ScatterVisualizer`. |

Operational constraints:

- Provide exactly two features. Use a two-column matrix, `features=[...]`, or
  `x="name", y="name"`; do not pass both `x`/`y` and `features`.
- If using a NumPy matrix with more than two columns, select columns explicitly
  with integer feature indexes such as `features=[0, 2]`.
- If using a DataFrame, `features` selects column names. DataFrame support
  depends on optional `pandas` being available in the user's environment.
- `classes` controls legend labels. Encoded targets `0..n_classes-1` are safest
  because the implementation indexes the class list with target values.
- `color` is a per-class palette; `colormap` is for continuous color mapping.

## Decision boundaries

| Object | Signature | Notes |
|---|---|---|
| `DecisionBoundariesVisualizer` | `(estimator, ax=None, x=None, y=None, features=None, classes=None, show_scatter=True, step_size=0.0025, markers=None, pcolormesh_alpha=0.8, scatter_alpha=1.0, encoder=None, is_fitted="auto", force_model=False, **kwargs)` | Experimental bivariate classifier boundary visualizer. |
| `DecisionViz` | alias exported from `yellowbrick.contrib.classifier` | Legacy alias. |
| `decisionviz` | `(estimator, X, y, ax=None, x_name=None, y_name=None, features=None, classes=None, show_scatter=True, step_size=0.0025, markers=None, pcolormesh_alpha=0.8, scatter_alpha=1.0, encoder=None, is_fitted="auto", force_model=False, **kwargs)` | Quick method; fits, finalizes, and returns the visualizer. |

Operational constraints:

- The estimator must be a classifier exposing `fit` and `predict`, unless
  `is_fitted=True` is used with an already-fitted classifier.
- The visualizer is bivariate. Select exactly two features before fitting.
- `step_size` is a fraction of the feature range used to build the mesh. The
  default is fine for small plots, but use coarser values such as `0.01` or
  `0.02` for fast reports and CI.
- `classes` must match the discovered classes. Too many class labels raises a
  Yellowbrick type error.
- Use `encoder` when target values need a mapping to display labels.
- `force_model=True` suppresses classifier checks, but it does not make a
  non-classifier behave correctly; prefer correct estimator typing or wrapping.

## Missing-value visualizers

| Object | Signature | Notes |
|---|---|---|
| `MissingValuesBar` | `(width=0.5, color=None, colors=None, classes=None, **kwargs)` | Horizontal bar chart of missing counts per feature; stacked by `y` when supplied. |
| `MissingValuesDispersion` | `(alpha=0.5, marker="|", classes=None, **kwargs)` | Scatter-like chart of missing positions by row index and feature. |
| `missing_bar` | `(X, y=None, ax=None, classes=None, width=0.5, color="black", **kwargs)` | Quick method; returns the Matplotlib axes. |
| `missing_dispersion` | `(X, y=None, ax=None, classes=None, alpha=0.5, marker="|", **kwargs)` | Quick method; returns the Matplotlib axes. |

Operational constraints:

- Pass a numeric array with `np.nan` values whenever possible.
- If `X` is a DataFrame, feature names are taken from columns when `features` is
  omitted; this requires optional `pandas`.
- If `X` is a NumPy array, pass `features=[...]` to avoid generic integer labels.
- When `y` is supplied, class-colored or stacked views require `classes` to match
  unique target order.
- Some older missing-value code paths reference NumPy string aliases removed in
  NumPy 2; if string/object missing-value plots fail, prefer numeric arrays and
  check the package-wide NumPy compatibility guidance.

## PrePredict estimator

| Object | Signature | Notes |
|---|---|---|
| `PrePredict` | `(data, estimator_type=None)` | Scikit-learn-like estimator whose `predict()` returns pre-computed outputs. |

`data` may be an array-like prediction vector, a callable returning predictions,
a file-like object, a string path, or a `pathlib.Path` loaded with `np.load`.
Set `estimator_type` to one of the wrapper constants:

- `CLASSIFIER`: `score(X, y)` computes accuracy.
- `REGRESSOR`: `score(X, y)` computes R².
- `CLUSTERER`: `score(X, y=None)` computes silhouette score from labels.

Limits:

- `PrePredict` does not implement `predict_proba` or `decision_function`.
- Many Yellowbrick visualizers inspect learned estimator attributes; manually
  attach required attributes or choose a simpler metric visualizer if needed.
- It ignores the shape/content of `X` when returning predictions. The user must
  ensure prediction length matches the `y` passed to `score`.

## Third-party estimator wrapper

| Object | Signature | Notes |
|---|---|---|
| `wrap` | `(estimator, estimator_type=None)` | Returns `ContribEstimator(estimator, estimator_type)`. |
| `ContribEstimator` | `(estimator, estimator_type=None)` | Proxies attributes to the wrapped estimator and raises friendlier Yellowbrick attribute errors. |
| `classifier` | `(estimator)` | Convenience wrapper with `_estimator_type="classifier"`. |
| `regressor` | `(estimator)` | Convenience wrapper with `_estimator_type="regressor"`. |
| `clusterer` | `(estimator)` | Convenience wrapper with `_estimator_type="clusterer"`. |

Use the constants `CLASSIFIER`, `REGRESSOR`, `CLUSTERER`, `DENSITY_ESTIMATOR`,
and `OUTLIER_DETECTOR` when explicit type checking is needed. The wrapper does
not add missing model methods; it only passes through existing methods and
metadata. If a visualizer needs learned attributes, create a custom
`ContribEstimator` subclass and provide properties such as `feature_importances_`,
`coef_`, `classes_`, or `predict_proba`.

## statsmodels adapter

| Object | Signature | Notes |
|---|---|---|
| `StatsModelsWrapper` | `(glm_partial, stated_estimator_type="regressor", scorer=r2_score)` | Prototype wrapper for GLM-like statsmodels objects. |

Use with optional `statsmodels` installed:

```python
from functools import partial
import statsmodels.api as sm
from yellowbrick.contrib.statsmodels import StatsModelsWrapper

glm = partial(sm.GLM, family=sm.families.Gaussian())
model = StatsModelsWrapper(glm)
```

The wrapper calls the statsmodels constructor as `glm_partial(y, X)`, fits the
statsmodels model, stores `glm_model` and `glm_results`, returns predictions from
`glm_results.predict(X)`, and scores with the supplied scorer. It is a prototype:
weights, many statsmodels options, and fitted-results shortcuts are not handled
by the wrapper itself.
