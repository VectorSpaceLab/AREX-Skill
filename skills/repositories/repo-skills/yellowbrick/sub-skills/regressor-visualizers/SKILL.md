---
name: regressor-visualizers
description: "Use Yellowbrick regression diagnostics for residuals, prediction
  error, Cook's distance, alpha selection, and regression quick-method reports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Yellowbrick Regressor Visualizers

Use this sub-skill when the task is to diagnose or report scikit-learn regression models with Yellowbrick. It covers model score visualizers (`ResidualsPlot`, `PredictionError`), influence diagnostics (`CooksDistance`), regularization-alpha diagnostics (`AlphaSelection`, `ManualAlphaSelection`), and their quick methods.

For shared visualizer lifecycle, axes, style, and headless-rendering setup, load [visualizer patterns](../../references/visualizer-patterns.md). For installation, Matplotlib backend/font, and broad dependency troubleshooting, load the root [troubleshooting reference](../../references/troubleshooting.md). Route feature ranking and model-selection tasks such as `FeatureImportances` and `RFECV` to [cluster/model-selection](../cluster-model-selection/SKILL.md).

## Fast routing

| User goal | Use | Why |
|---|---|---|
| "Are residuals random, centered, and normally distributed?" | `ResidualsPlot` | Plots residuals (`y_pred - y`) against predicted values; optional histogram or Q-Q side panel helps evaluate linear-model assumptions. |
| "Are predictions systematically high/low across the target range?" | `PredictionError` | Plots actual target `y` against predicted target `ŷ`; identity and best-fit lines expose bias, over/under-prediction, and variance. |
| "Which rows drive an OLS fit or look like influential outliers?" | `CooksDistance` | Computes Cook's distance with an internal ordinary least-squares model and marks the `4/n` influence threshold. |
| "Which alpha did a CV linear model choose?" | `AlphaSelection` | Wraps `RidgeCV`, `LassoCV`, `LassoLarsCV`, or `ElasticNetCV`-style estimators and plots alpha versus stored CV error/score. |
| "I have a non-CV estimator with an `alpha` parameter." | `ManualAlphaSelection` | Calls `cross_val_score` over an explicit alpha grid for estimators that support `set_params(alpha=...)`. |

## Minimal model-diagnostic workflow

```python
import matplotlib
matplotlib.use("Agg")  # use before importing pyplot in headless sessions

from sklearn.datasets import make_regression
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from yellowbrick.regressor import ResidualsPlot, PredictionError

X, y = make_regression(n_samples=250, n_features=8, noise=12.0, random_state=7)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=13)

residuals = ResidualsPlot(Ridge(alpha=1.0), hist="density")
residuals.fit(X_train, y_train)
residuals.score(X_test, y_test)
residuals.show(outpath="residuals.png", clear_figure=True, bbox_inches="tight")

pe = PredictionError(Ridge(alpha=1.0), shared_limits=True, bestfit=True, identity=True)
pe.fit(X_train, y_train)
pe.score(X_test, y_test)
pe.show(outpath="prediction_error.png", clear_figure=True, bbox_inches="tight")
```

Expected public attributes after scoring: `ResidualsPlot.train_score_`, `ResidualsPlot.test_score_`, and `PredictionError.score_` contain the wrapped estimator's regression score, usually `R^2`.

## Output/report rules

- Prefer class visualizers for reports because `show(outpath=..., clear_figure=True, bbox_inches="tight")` saves and closes figures in a predictable way.
- Quick methods are fine for notebooks or one-off plots. If you need a file, call the quick method with `show=False`, then call `viz.show(outpath=...)` on the returned visualizer.
- For residual diagnostics, score the training split first through `fit(X_train, y_train)`, then overlay test points with `score(X_test, y_test)`. Yellowbrick labels train and test `R^2` separately.
- For `ResidualsPlot`, choose **either** `hist` **or** `qqplot`; `hist=True` and `qqplot=True` together raise a `YellowbrickValueError`.
- For reusable automated reports, set a non-interactive Matplotlib backend (`Agg`) before importing `matplotlib.pyplot` or Yellowbrick visualizers.

## Reference map

- [API reference](references/api-reference.md) — concrete signatures, import paths, learned attributes, and quick-method caveats.
- [Workflows](references/workflows.md) — residual-vs-prediction-error selection, train/test overlays, alpha tuning, Cook's distance, and pipeline patterns.
- [Troubleshooting](references/troubleshooting.md) — regressor type errors, fitted/refit decisions, Matplotlib issues, alpha-estimator compatibility, and report-output failures.
- [Smoke helper](scripts/regression_smoke.py) — deterministic synthetic-data `Agg` smoke that writes regression diagnostic PNGs without network access.

## Validate this sub-skill in a target environment

```bash
python skills/disco/yellowbrick/sub-skills/regressor-visualizers/scripts/regression_smoke.py --outdir /tmp/yellowbrick-regression-smoke
ls -1 /tmp/yellowbrick-regression-smoke
```

Expected output files include `residuals_density.png`, `residuals_qq.png`, `prediction_error.png`, `cooks_distance.png`, `alpha_selection.png`, `manual_alpha_selection.png`, and `manifest.json`.
