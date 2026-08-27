# Contrib Troubleshooting

Start with root troubleshooting for install, Matplotlib backend, fonts, and broad
scikit-learn/NumPy compatibility. Use this reference for contrib-specific import,
typing, optional dependency, and experimental-API failures.

## `ImportError` or `AttributeError` from top-level `yellowbrick.contrib`

Symptom examples:

- `cannot import name 'ScatterVisualizer' from 'yellowbrick.contrib'`
- `module 'yellowbrick.contrib' has no attribute 'PrePredict'`
- `module 'yellowbrick.contrib' has no attribute 'ContribEstimator'`

Fix: use concrete contrib submodules.

```python
from yellowbrick.contrib.scatter import ScatterVisualizer
from yellowbrick.contrib.prepredict import PrePredict
from yellowbrick.contrib.wrapper import ContribEstimator, wrap
from yellowbrick.contrib.classifier.boundaries import DecisionBoundariesVisualizer
from yellowbrick.contrib.missing import MissingValuesBar, MissingValuesDispersion
from yellowbrick.contrib.statsmodels import StatsModelsWrapper
```

The `yellowbrick.contrib` initializer intentionally contains little or no public
hoisting. Do not rewrite examples to import contrib classes from the top level.

## Stable visualizer exists, but user chose contrib

Contrib is experimental. If the goal is a classification report, confusion
matrix, ROC/PR curve, regression residual plot, prediction-error plot, feature
ranking, PCA/manifold projection, validation curve, learning curve, or clustering
elbow/silhouette plot, route back to the stable sub-skill first. Stay with
contrib only for decision boundaries, missing-value visualizers, wrappers,
`PrePredict`, statsmodels, or explicit contrib imports.

## `This estimator is not a classifier/regressor/clusterer`

Likely causes:

1. The estimator truly is the wrong type for the visualizer.
2. A third-party estimator implements `fit`/`predict` but lacks scikit-learn type
   metadata.
3. A package compatibility issue changes how scikit-learn identifies estimators.

Fixes:

```python
from yellowbrick.contrib.wrapper import CLASSIFIER, REGRESSOR, CLUSTERER, wrap

clf = wrap(third_party_classifier, CLASSIFIER)
reg = wrap(third_party_regressor, REGRESSOR)
ctr = wrap(third_party_clusterer, CLUSTERER)
```

For decision boundaries, `force_model=True` only bypasses the initial type check;
it does not add classifier behavior. Prefer a correctly typed classifier or
wrapper. If an ordinary scikit-learn classifier is rejected, check the root
compatibility guidance for Yellowbrick 1.5 with compatible scikit-learn and NumPy
versions.

## Wrapped estimator is missing an attribute

`ContribEstimator` proxies the underlying object. A friendly
`YellowbrickAttributeError` such as `estimator is missing the 'fit' attribute` or
`feature_importances_` means the selected Yellowbrick visualizer actually needs
that method or learned attribute.

Options:

- Choose a visualizer that needs fewer estimator attributes.
- Fit the underlying estimator before wrapping and pass `is_fitted=True` when the
  visualizer supports it.
- Subclass `ContribEstimator` and add the required property or method.
- Use `PrePredict` only for visualizers that can work from `predict()` output and
  a score; it does not add probabilities, coefficients, classes, or feature
  importances.

## `PrePredict` output length or metric errors

`PrePredict.predict(X)` returns the stored predictions and does not validate
`X`. Ensure the stored prediction vector matches the `y` passed to the visualizer
`score` call.

- Classifier `PrePredict(..., CLASSIFIER)` scores with accuracy.
- Regressor `PrePredict(..., REGRESSOR)` scores with R².
- Clusterer `PrePredict(..., CLUSTERER)` scores with silhouette score.

Do not use `PrePredict` for ROC, precision-recall, discrimination-threshold, or
other visualizers requiring `predict_proba` or `decision_function` unless you
write a custom estimator implementing those methods.

## Decision-boundary plot is slow or memory-heavy

The decision-boundary visualizer builds a mesh over the two selected features.
The default `step_size=0.0025` can create many grid points.

Mitigations:

- Select exactly two features before fitting.
- Standardize or bound feature ranges.
- Use `step_size=0.01`, `0.02`, or coarser for agent reports.
- Sample large datasets before plotting.
- Use `show_scatter=False` if the scatter overlay is not required.
- Prefer simple classifiers such as KNN, logistic regression, naive Bayes, or a
  shallow tree for demonstration plots.

## Decision-boundary class label mismatch

If too many display names are supplied, fitting can raise a Yellowbrick type
error. If labels appear swapped, the `classes` list is not aligned with the
sorted target values discovered during fit.

Fixes:

- Inspect `sorted(set(y))` and supply the same number of display labels in that
  order.
- Use `encoder` when the target values need a mapping to labels.
- For non-contiguous labels, encode targets to `0..n_classes-1` before plotting
  when using contrib scatter or boundary plots.

## Scatter visualizer says it only accepts two features

`ScatterVisualizer` is strictly bivariate.

Fixes:

- Pass a two-column matrix: `X[:, [0, 2]]`.
- Or pass `features=[0, 2]` for a NumPy matrix with more columns.
- Or pass `features=["col_a", "col_b"]` / `x="col_a", y="col_b"` for a DataFrame.
- Do not pass both `features` and `x`/`y`.

For more than two features, route to stable feature-target visualizers such as
`Rank2D`, `PCA`, `Manifold`, `ParallelCoordinates`, or `RadialVisualizer`.

## Missing-value plot fails on strings, object arrays, or NumPy 2

Use numeric arrays with `np.nan` values for the most reliable path. The missing
visualizers have older code paths for string missingness and may interact poorly
with removed NumPy string aliases in newer NumPy versions.

Fixes:

- Convert missing markers to `np.nan` and cast numeric columns to float.
- Use a DataFrame only when optional `pandas` is installed.
- Pass explicit `features=[...]` when using arrays.
- If package-wide NumPy compatibility errors appear, check root troubleshooting
  and consider a Yellowbrick-compatible NumPy pin.

## Missing-value labels or colors are wrong

When `y` is supplied, the bar chart stacks counts by target and dispersion colors
points by target. If labels are wrong:

- Ensure `classes` has the same length and order as `np.unique(y)`.
- Keep `y` one-dimensional.
- Use simple class labels for reports; avoid mixing strings and integers.

## `ModuleNotFoundError: No module named 'statsmodels'`

`StatsModelsWrapper` is optional. Install `statsmodels` in the user's environment
before using it, or route to scikit-learn regression visualizers with a native
scikit-learn estimator.

## statsmodels wrapper fit/predict fails

`StatsModelsWrapper` is a prototype around a GLM-like callable. It expects a
partial constructor that can be called as `glm_partial(y, X)` and whose fitted
results object has `predict(X)`.

Common fixes:

- Use `functools.partial(sm.GLM, family=sm.families.Gaussian())` for the standard
  documented path.
- Add an intercept/constant column yourself when the statsmodels model requires
  one; the wrapper does not modify `X`.
- For weights, formulas, robust covariance, or fitted-results objects, write a
  custom adapter implementing `fit`, `predict`, `score`, and `_estimator_type`.

## Stale contributor example patterns

Do not use the old `examples/balavenkatesan/testing.py` pattern as runtime
guidance. It depends on a missing local CSV, imports stale `yellowbrick.neighbors`
objects, and uses deprecated NumPy aliases. Prefer the synthetic workflows and
smoke helper bundled with this sub-skill.
