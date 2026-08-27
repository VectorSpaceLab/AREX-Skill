# Regressor Visualizer Troubleshooting

For broad install, backend, display, and style issues, also load the root [troubleshooting reference](../../../references/troubleshooting.md). This page focuses on regression diagnostics.

## `This estimator is not a regressor`

Symptoms:

- Instantiating `ResidualsPlot(model)`, `PredictionError(model)`, or `AlphaSelection(model)` raises a `YellowbrickTypeError` that says the estimator is not a regressor.
- A normal scikit-learn regressor fails Yellowbrick's type check after a dependency upgrade.

Causes and fixes:

1. **Wrong estimator family.** Use only regressors or pipelines whose final estimator is a regressor. Classifiers belong in the classifier sub-skill; clusterers and feature/model-selection visualizers belong in [cluster/model-selection](../../cluster-model-selection/SKILL.md).
2. **Old Yellowbrick type checks with a newer scikit-learn.** Yellowbrick 1.5 checks the estimator's `_estimator_type` attribute directly. If a current scikit-learn release removes or changes that attribute, pin to a compatible stack such as scikit-learn 1.3.x with NumPy 1.x, or use an environment already verified for this repo skill.
3. **Custom regressor lacks `_estimator_type`.** Prefer implementing scikit-learn-compatible estimator tags and `_estimator_type = "regressor"`. `force_model=True` can bypass the check for score visualizers, but use it only when you have verified that the object implements `fit`, `predict`, and `score` as a regressor.

## Estimator is fitted, refit unexpectedly, or should not be refit

Symptoms:

- A previously fitted model is refit when the visualizer calls `fit`.
- A report should use a frozen model but the code retrains it.
- Scores differ because the estimator state changed.

Fixes:

- Pass `is_fitted=True` to `ResidualsPlot` or `PredictionError` when the wrapped estimator is already fitted and should not be modified.
- Pass `is_fitted=False` when you intentionally want Yellowbrick to fit the estimator during visualizer `fit`.
- The default `is_fitted="auto"` asks Yellowbrick to infer fitted state; for reproducible reports, choose explicitly.
- For quick methods, remember that the helper calls `fit(X_train, y_train)` internally.

## Only one of `X_test` or `y_test` was supplied

Symptoms:

- `residuals_plot(...)` or `prediction_error(...)` raises `YellowbrickValueError: both X_test and y_test are required if one is specified`.

Fix:

```python
viz = residuals_plot(model, X_train, y_train, X_test, y_test, show=False)
viz.show(outpath="residuals.png", clear_figure=True)
```

If you do not have a holdout set, omit both `X_test` and `y_test`; the quick method will score on the training data.

## Histogram and Q-Q plot conflict

Symptoms:

- `ResidualsPlot(..., hist=True, qqplot=True)` raises a value error.

Fix:

```python
# Histogram/density version
ResidualsPlot(model, hist="density", qqplot=False)

# Q-Q version
ResidualsPlot(model, hist=False, qqplot=True)
```

Yellowbrick cannot draw the histogram side panel and Q-Q side panel simultaneously.

## Residuals look patterned, heteroscedastic, or non-normal

Symptoms:

- Residual points form a curve instead of a random band around zero.
- Residual spread grows or shrinks with the predicted value.
- The Q-Q panel has heavy tails or strong curvature.

Actions:

- Confirm train/test preprocessing is identical and leakage-free.
- Check outliers with `CooksDistance` and rerun the residual plot after investigating high-influence rows.
- Try target transformations, interaction features, non-linear regressors, or a different loss/metric.
- Do not claim a linear model is appropriate solely from a high `R^2`; use residual structure to validate linear assumptions.

## Prediction error plot looks distorted

Symptoms:

- The identity line is misleading or the plot does not appear square.
- Points appear good visually, but the axes ranges differ.

Fixes:

- Use `PredictionError(..., shared_limits=True, identity=True)` for diagnostic reports.
- Use `shared_limits=False` only when you explicitly need to zoom into an asymmetric target range and will state that the identity comparison is distorted.
- Keep `bestfit=True` when communicating systematic bias; turn it off for minimalist plots.

## `CooksDistance` Matplotlib stem error

Symptoms:

- `CooksDistance.fit(...)` fails with `TypeError: Axes.stem() got an unexpected keyword argument 'use_line_collection'`.

Cause:

- Yellowbrick 1.5 passes a Matplotlib argument that newer Matplotlib releases removed.

Fixes:

- Prefer a Yellowbrick/Matplotlib combination verified for Cook's distance, or update Yellowbrick if a fixed release is available.
- For smoke testing only, the bundled `regression_smoke.py` applies a local compatibility wrapper that drops the removed keyword before calling `CooksDistance`.
- Do not copy the smoke-test monkeypatch into production modeling code without documenting the dependency issue.

## Cook's distance has NaNs, infinities, or unstable values

Symptoms:

- Cook's distance values are not finite.
- The OLS model is singular or leverage values are unstable.

Causes and fixes:

- Check that `X` is a 2D numeric matrix with no NaNs or infinities.
- Remove constant, duplicate, or perfectly collinear columns before using Cook's distance.
- Ensure `n_samples` is substantially larger than `n_features`; the visualizer computes an OLS projection matrix.
- Interpret `CooksDistance` as an OLS influence screen, not as influence for arbitrary non-linear models.

## `AlphaSelection` rejects the estimator

Symptoms:

- `AlphaSelection(Ridge())` or another non-CV estimator raises a `YellowbrickTypeError` saying to try `ManualAlphaSelection`.
- `ManualAlphaSelection(RidgeCV())` raises a `YellowbrickTypeError` saying to try `AlphaSelection`.

Fix:

- Use `AlphaSelection` for estimators whose class name ends in `CV` and stores alpha/error paths.
- Use `ManualAlphaSelection` for non-CV estimators that accept `set_params(alpha=...)`.

```python
from sklearn.linear_model import LassoCV, Ridge
from yellowbrick.regressor import AlphaSelection, ManualAlphaSelection

AlphaSelection(LassoCV(alphas=alpha_grid, cv=5))
ManualAlphaSelection(Ridge(), alphas=alpha_grid, cv=5, scoring="r2")
```

## `AlphaSelection` cannot find alphas or errors

Symptoms:

- `YellowbrickValueError: could not find alphas param ...`
- `YellowbrickValueError: could not find errors param ...`

Causes and fixes:

- The fitted estimator does not expose one of the attributes Yellowbrick searches: `cv_alphas_`, `alphas_`, `alphas`, `mse_path_`, or `cv_values_`.
- Some scikit-learn versions changed `RidgeCV`'s stored CV attributes. Try `LassoCV`, `ElasticNetCV`, or `LassoLarsCV`, use `ManualAlphaSelection`, or pin to a compatible scikit-learn version.
- Fit the visualizer with real `X, y`; the attributes are usually created during estimator `fit`.
- For older `RidgeCV`, ensure CV values are stored; Yellowbrick sets `store_cv_values=True` when that parameter exists.

## Manual alpha selection is slow

Symptoms:

- `ManualAlphaSelection.fit` takes too long in CI or an agent run.

Cause:

- Work scales roughly with `len(alphas) * cv * estimator_fit_cost`.

Fixes:

- Use a coarse alpha grid first, for example `np.logspace(-3, 2, 10)`.
- Reduce `cv` for smoke checks, then rerun a larger grid in a dedicated experiment.
- Prefer estimator-specific CV classes (`LassoCV`, `ElasticNetCV`, `RidgeCV` when compatible) when they are available.

## Figure output missing or empty

Symptoms:

- No PNG appears after running a script.
- The script opens a GUI or hangs in a headless worker.
- Quick methods show a plot but do not save it.

Fixes:

```python
import matplotlib
matplotlib.use("Agg")

viz = PredictionError(model)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="prediction_error.png", clear_figure=True, bbox_inches="tight")
```

- Set the backend before importing `matplotlib.pyplot` or Yellowbrick visualizers.
- Use class visualizers for file output, or quick methods with `show=False` followed by `viz.show(outpath=...)`.
- Treat missing-font warnings as display warnings if the PNG is created and non-empty; install fonts or set Matplotlib font config only when appearance matters.

## Smoke helper fails

Run:

```bash
python skills/disco/yellowbrick/sub-skills/regressor-visualizers/scripts/regression_smoke.py --outdir /tmp/yellowbrick-regression-smoke
```

Expected files: `residuals_density.png`, `residuals_qq.png`, `prediction_error.png`, `cooks_distance.png`, `alpha_selection.png`, `manual_alpha_selection.png`, and `manifest.json`.

If it fails:

1. Read the traceback and identify whether it is a regressor type-check, Matplotlib backend/stem, alpha-path, or dependency problem.
2. Confirm the environment has Yellowbrick, scikit-learn, NumPy, SciPy, and Matplotlib versions that are mutually compatible.
3. Re-run with a clean output directory and check that each PNG is non-empty.
