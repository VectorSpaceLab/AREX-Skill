# Regressor Visualizers API Reference

This reference records the public Yellowbrick regression diagnostics used by this sub-skill. Imports shown here are package import paths, not source-tree links.

## Imports

```python
from yellowbrick.regressor import (
    ResidualsPlot,
    PredictionError,
    CooksDistance,
    residuals_plot,
    prediction_error,
    cooks_distance,
)
from yellowbrick.regressor import AlphaSelection, ManualAlphaSelection
from yellowbrick.regressor.alphas import alphas, manual_alphas
```

Do **not** use `from yellowbrick.regressor import alphas` for the quick method: in Yellowbrick 1.5 that name can resolve to the `yellowbrick.regressor.alphas` module. Import `alphas` and `manual_alphas` from `yellowbrick.regressor.alphas`.

## Score visualizers

### `ResidualsPlot`

Signature:

```python
ResidualsPlot(
    estimator,
    ax=None,
    hist=True,
    qqplot=False,
    train_color="b",
    test_color="g",
    line_color="#111111",
    train_alpha=0.75,
    test_alpha=0.75,
    is_fitted="auto",
    **kwargs,
)
```

Purpose: wrap a scikit-learn regressor and draw residuals (`y_pred - y`) on the vertical axis against predicted values on the horizontal axis.

Lifecycle:

```python
viz = ResidualsPlot(model, hist="density")
viz.fit(X_train, y_train)       # fits model if needed and draws train residuals
train_r2 = viz.train_score_
test_r2 = viz.score(X_test, y_test)  # draws test residuals, returns score
viz.show(outpath="residuals.png", clear_figure=True)
```

Important parameters and attributes:

- `hist`: `True`, `False`, `None`, `"frequency"`, or `"density"`. The side histogram uses a second axes.
- `qqplot`: `True` or `False`. Set `hist=False` when `qqplot=True`.
- `train_color`, `test_color`, `line_color`, `train_alpha`, `test_alpha`: train/test overlay appearance.
- `is_fitted`: `"auto"`, `True`, or `False`; controls whether the wrapped estimator is refit during visualizer `fit`.
- `train_score_` and `test_score_`: usually train/test `R^2` scores.

Quick method:

```python
residuals_plot(
    estimator,
    X_train,
    y_train,
    X_test=None,
    y_test=None,
    ax=None,
    hist=True,
    qqplot=False,
    train_color="b",
    test_color="g",
    line_color="#111111",
    train_alpha=0.75,
    test_alpha=0.75,
    is_fitted="auto",
    show=True,
    **kwargs,
)
```

If either `X_test` or `y_test` is supplied, both are required. With `show=False`, the quick method returns a `ResidualsPlot` after calling `finalize()`.

### `PredictionError`

Signature:

```python
PredictionError(
    estimator,
    ax=None,
    shared_limits=True,
    bestfit=True,
    identity=True,
    alpha=0.75,
    is_fitted="auto",
    **kwargs,
)
```

Purpose: wrap a scikit-learn regressor and plot actual target values `y` against predicted values `ŷ` to expose bias, variance, and over/under-prediction.

Lifecycle:

```python
viz = PredictionError(model, shared_limits=True, bestfit=True, identity=True)
viz.fit(X_train, y_train)
r2 = viz.score(X_test, y_test)
viz.show(outpath="prediction_error.png", clear_figure=True)
```

Important parameters and attributes:

- `shared_limits=True`: forces equal x/y limits and a square figure, making the identity line meaningful.
- `bestfit=True`: draws a linear best-fit line through observed/predicted pairs.
- `identity=True`: draws the `y = x` line.
- `alpha`: scatter-point transparency.
- `is_fitted`: `"auto"`, `True`, or `False` refit control.
- `score_`: score returned by the wrapped estimator, usually `R^2`.
- Optional appearance kwargs include `point_color` and `line_color`.

Quick method:

```python
prediction_error(
    estimator,
    X_train,
    y_train,
    X_test=None,
    y_test=None,
    ax=None,
    shared_limits=True,
    bestfit=True,
    identity=True,
    alpha=0.75,
    is_fitted="auto",
    show=True,
    **kwargs,
)
```

If only training data is supplied, the quick method scores on the training set. Provide both `X_test` and `y_test` for held-out scoring.

## Influence diagnostic

### `CooksDistance`

Signature:

```python
CooksDistance(
    ax=None,
    draw_threshold=True,
    linefmt="C0-",
    markerfmt=",",
    **kwargs,
)
```

Purpose: compute Cook's distance for each row of `X` using an internal ordinary-least-squares `LinearRegression` model. Use it for influence/outlier analysis before deciding whether a linear model is appropriate.

Lifecycle:

```python
viz = CooksDistance(draw_threshold=True)
viz.fit(X, y)
viz.show(outpath="cooks_distance.png", clear_figure=True)
```

Learned attributes after `fit`:

- `distance_`: one Cook's distance value per row.
- `p_values_`: F-test p-values with the same shape as `distance_`.
- `influence_threshold_`: rule-of-thumb threshold `4 / n_samples`.
- `outlier_percentage_`: percent of rows with `distance_ > influence_threshold_`.

Quick method:

```python
cooks_distance(
    X,
    y,
    ax=None,
    draw_threshold=True,
    linefmt="C0-",
    markerfmt=",",
    show=True,
    **kwargs,
)
```

`CooksDistance` is OLS-specific; it does not wrap your production regressor. For non-linear model influence, use it only as a linear-sensitivity screen or choose a model-specific influence method outside Yellowbrick.

## Alpha visualizers

### `AlphaSelection`

Signature:

```python
AlphaSelection(estimator, ax=None, is_fitted="auto", **kwargs)
```

Purpose: wrap a compatible `*CV` regularized linear regressor and draw its stored alpha/error curve after fitting.

Expected estimators:

- `RidgeCV` with stored CV values/results available in the installed scikit-learn version.
- `LassoCV`, `LassoLarsCV`, and `ElasticNetCV` with `alphas_`/`mse_path_`-style learned attributes.

Lifecycle:

```python
import numpy as np
from sklearn.linear_model import LassoCV
from yellowbrick.regressor import AlphaSelection

alpha_grid = np.logspace(-4, 1, 30)
viz = AlphaSelection(LassoCV(alphas=alpha_grid, cv=5, random_state=0))
viz.fit(X, y)
viz.show(outpath="alpha_selection.png", clear_figure=True)
```

Important behavior:

- The estimator class name must end with `CV`; otherwise instantiate `ManualAlphaSelection`.
- The visualizer searches for alpha values in `cv_alphas_`, `alphas_`, or `alphas`.
- It searches for errors/scores in `mse_path_` or `cv_values_`; incompatible or changed scikit-learn estimators can raise `YellowbrickValueError`.
- For older `RidgeCV`, Yellowbrick sets `store_cv_values=True` when that parameter exists.

Quick method:

```python
alphas(estimator, X, y=None, ax=None, is_fitted="auto", show=True, **kwargs)
```

Import it with `from yellowbrick.regressor.alphas import alphas`.

### `ManualAlphaSelection`

Signature:

```python
ManualAlphaSelection(
    estimator,
    ax=None,
    alphas=None,
    cv=None,
    scoring=None,
    **kwargs,
)
```

Purpose: score an unfitted non-`CV` regressor over an explicit alpha grid by repeatedly calling `estimator.set_params(alpha=alpha)` and `sklearn.model_selection.cross_val_score`.

Lifecycle:

```python
import numpy as np
from sklearn.linear_model import Ridge
from yellowbrick.regressor import ManualAlphaSelection

alpha_grid = np.logspace(-3, 2, 20)
viz = ManualAlphaSelection(
    Ridge(),
    alphas=alpha_grid,
    cv=5,
    scoring="neg_mean_squared_error",
)
viz.fit(X, y)
viz.show(outpath="manual_alpha_selection.png", clear_figure=True)
```

Important behavior:

- The estimator class name must **not** end with `CV`; use `AlphaSelection` for built-in CV estimators.
- The estimator must implement `set_params(alpha=...)`.
- `cv` and `scoring` are passed to `cross_val_score`; keep alpha grids and fold counts bounded in CI.
- The plotted y-axis is labeled `error (or score)`. Interpret the curve according to the chosen `scoring`; for negative losses, less negative is usually better.

Quick method:

```python
manual_alphas(
    estimator,
    X,
    y=None,
    ax=None,
    alphas=None,
    cv=None,
    scoring=None,
    show=True,
    **kwargs,
)
```

Import it with `from yellowbrick.regressor.alphas import manual_alphas`.
