# Regressor Visualizer Workflows

Use these workflows after completing the shared Yellowbrick setup from [visualizer patterns](../../../references/visualizer-patterns.md): import a non-interactive backend for headless execution, prepare data splits, instantiate a visualizer, call `fit`, call `score` when applicable, and finish with `show(outpath=..., clear_figure=True)` for files.

## 1. Choose residuals versus prediction error

Use both plots when building a regression report, but prioritize by diagnostic question:

| Diagnostic question | Preferred visualizer | What to inspect |
|---|---|---|
| Does a linear model meet residual assumptions? | `ResidualsPlot` | Residuals randomly centered around zero; no funnel shape; residual distribution roughly symmetric/normal; train/test residuals behave similarly. |
| Is error localized to a target range? | `PredictionError` | Points close to the identity line; systematic under/over-prediction; high-target or low-target spread; slope of best-fit line. |
| Are individual rows distorting a linear fit? | `CooksDistance` | Stems above the `4/n` threshold and `outlier_percentage_`; compare residuals before/after investigating influential rows. |
| Which regularization strength is stable? | `AlphaSelection` or `ManualAlphaSelection` | Smooth alpha-vs-error/score curve, chosen alpha not at an untested boundary, and cross-validation settings aligned with the task. |

Residuals answer "what does the error look like after prediction?" Prediction error answers "where do predictions deviate from the actual target scale?" Cook's distance answers "which rows change an OLS fit?" Alpha visualizers answer "how does regularization strength affect CV score/error?"

## 2. Residuals report with train/test overlays

```python
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from yellowbrick.regressor import ResidualsPlot

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=13)

viz = ResidualsPlot(
    Ridge(alpha=1.0),
    hist="density",
    train_color="steelblue",
    test_color="darkorange",
    train_alpha=0.45,
    test_alpha=0.8,
)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="regression_residuals.png", clear_figure=True, bbox_inches="tight")

print({"train_r2": viz.train_score_, "test_r2": viz.test_score_})
```

Validation checklist:

- Confirm the wrapped estimator is a regressor or a pipeline whose final estimator is a regressor.
- Use held-out data for `score` so test residuals appear separately from training residuals.
- Use `hist="density"` when comparing residual distribution shape across sample sizes; use `hist=False` for dense or small figures.
- If you need normality inspection, replace the histogram with `hist=False, qqplot=True`.
- In a report, include both the PNG and the train/test score values from `train_score_` and `test_score_`.

## 3. Q-Q residual normality check

```python
viz = ResidualsPlot(Ridge(alpha=1.0), hist=False, qqplot=True)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="regression_residuals_qq.png", clear_figure=True, bbox_inches="tight")
```

Interpretation:

- Points near a straight diagonal in the Q-Q panel are consistent with normally distributed residuals.
- Curvature, heavy tails, or split train/test behavior suggests non-normal errors, target transforms, missing features, outliers, or a non-linear model.
- Do not set `hist=True` with `qqplot=True`; Yellowbrick rejects that combination.

## 4. Prediction error plot for target-scale bias

```python
from sklearn.linear_model import Ridge
from yellowbrick.regressor import PredictionError

viz = PredictionError(
    Ridge(alpha=1.0),
    shared_limits=True,
    bestfit=True,
    identity=True,
    alpha=0.65,
)
viz.fit(X_train, y_train)
score = viz.score(X_test, y_test)
viz.show(outpath="regression_prediction_error.png", clear_figure=True, bbox_inches="tight")
```

Validation checklist:

- Use `shared_limits=True` for honest visual comparison against the identity line.
- Keep `identity=True` when diagnosing over/under-prediction.
- Keep `bestfit=True` when explaining systematic target-scale bias; turn it off only for simpler visuals.
- Report `score` or `viz.score_` beside the figure; the label in the plot is usually `R^2` unless the estimator exposes a custom `scoring` attribute.

## 5. Quick methods in scripts or notebooks

Quick methods fit and score in one call. They are concise but less flexible for file output:

```python
from yellowbrick.regressor import residuals_plot, prediction_error

resid = residuals_plot(model, X_train, y_train, X_test, y_test, hist=False, show=False)
resid.show(outpath="quick_residuals.png", clear_figure=True)

pe = prediction_error(model, X_train, y_train, X_test, y_test, show=False)
pe.show(outpath="quick_prediction_error.png", clear_figure=True)
```

Rules:

- Provide both `X_test` and `y_test`; providing only one raises a value error.
- Use `show=False` when you need to save the figure later.
- Do not rely on quick methods for multi-panel report layouts unless you pass explicit `ax` objects.

## 6. Cook's distance influence screen

```python
from yellowbrick.regressor import CooksDistance

viz = CooksDistance(draw_threshold=True, linefmt="C0-", markerfmt=",")
viz.fit(X_train, y_train)
viz.show(outpath="cooks_distance.png", clear_figure=True, bbox_inches="tight")

mask_less_influential = viz.distance_ <= viz.influence_threshold_
print({
    "influence_threshold": viz.influence_threshold_,
    "outlier_percentage": viz.outlier_percentage_,
})
```

Use this before or beside linear regression diagnostics. It assumes an internal OLS model and should not be described as influence for a random forest, boosted tree, neural network, or other non-linear estimator. If you filter rows based on Cook's distance, rerun residual and prediction-error plots and disclose the filtering decision.

## 7. Alpha tuning with built-in CV estimators

```python
import numpy as np
from sklearn.linear_model import LassoCV
from yellowbrick.regressor import AlphaSelection

alpha_grid = np.logspace(-4, 1, 30)
model = LassoCV(alphas=alpha_grid, cv=5, random_state=0, max_iter=10000)

viz = AlphaSelection(model)
viz.fit(X_train, y_train)
viz.show(outpath="alpha_selection.png", clear_figure=True, bbox_inches="tight")
```

Validation checklist:

- Use an estimator whose class name ends with `CV` and stores alpha/error paths that Yellowbrick can read.
- Prefer `LassoCV`, `LassoLarsCV`, or `ElasticNetCV` when modern `RidgeCV` no longer exposes `cv_values_` in the expected form.
- Make sure the selected alpha is not pinned to the minimum or maximum grid value; expand the grid if it is.
- Keep `cv`, `random_state`, and `max_iter` explicit in reproducible reports.

## 8. Manual alpha tuning for non-CV estimators

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
viz.fit(X_train, y_train)
viz.show(outpath="manual_alpha_selection.png", clear_figure=True, bbox_inches="tight")
```

Validation checklist:

- The estimator must be unfitted and must accept `set_params(alpha=...)`.
- Keep `len(alphas) * cv` small enough for CI or agent runs.
- Match `scoring` to the business metric and explain whether larger or smaller is better.
- If you use negative loss scoring such as `neg_mean_squared_error`, remember that values closer to zero are better even though the plot y-axis says `error (or score)`.

## 9. Pipelines

Yellowbrick regression score visualizers can either wrap a full preprocessing+regressor pipeline or appear as the final step in a scikit-learn `Pipeline`.

Wrap the full pipeline when preprocessing must be applied inside the diagnostic:

```python
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from yellowbrick.regressor import PredictionError

model = Pipeline([
    ("impute", SimpleImputer()),
    ("scale", StandardScaler()),
    ("ridge", Ridge(alpha=1.0)),
])

viz = PredictionError(model)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="pipeline_prediction_error.png", clear_figure=True)
```

Use the visualizer as the final pipeline step only when the downstream code expects a pipeline object and you will retrieve the visualizer step for `show`:

```python
pipe = Pipeline([
    ("scale", StandardScaler()),
    ("residuals", ResidualsPlot(Ridge(alpha=1.0), hist=False)),
])
pipe.fit(X_train, y_train)
pipe.score(X_test, y_test)
pipe["residuals"].show(outpath="pipeline_residuals.png", clear_figure=True)
```

## 10. Validation command

Run the bundled helper after installing Yellowbrick and its compatible dependencies:

```bash
python skills/disco/yellowbrick/sub-skills/regressor-visualizers/scripts/regression_smoke.py --outdir /tmp/yellowbrick-regression-smoke
```

The helper uses only synthetic data and should create six PNG files plus a manifest. Treat missing PNGs, zero-byte PNGs, or a nonzero exit as a failed runtime check.
