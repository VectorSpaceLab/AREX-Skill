---
name: contrib-and-extensions
description: "Use Yellowbrick experimental contrib visualizers, missing-data
  plots, decision boundaries, pre-predicted outputs, third-party estimator
  wrappers, and statsmodels adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Yellowbrick Contrib and Extensions

Use this sub-skill only after checking whether a stable Yellowbrick core workflow
fits the request. Contrib APIs are useful but less stable: they live in specific
submodules, are not hoisted from `yellowbrick.contrib`, may rely on optional
packages, and may expose prototype behavior.

## Route stable workflows first

- Classification reports, confusion matrices, ROC/PR curves, threshold tuning,
  and ordinary classifier score plots: use
  [classifier visualizers](../classifier-visualizers/SKILL.md) first.
- Regression residual, prediction-error, Cook's distance, and alpha-selection
  plots: use [regressor visualizers](../regressor-visualizers/SKILL.md) first.
- Feature ranking, PCA/manifold projections, target balance/binning, and
  feature-target correlation: use
  [feature-target visualizers](../feature-target-visualizers/SKILL.md) first.
- Clustering and cross-validation/model-selection diagnostics: use
  [cluster and model selection](../cluster-model-selection/SKILL.md) first.
- Shared `fit`/`score`/`show`, axes, style, `Agg`, and saved-output patterns:
  read [visualizer patterns](../../references/visualizer-patterns.md).
- Package-wide install/display/scikit-learn compatibility failures: read root
  [troubleshooting](../../references/troubleshooting.md) before applying
  contrib-specific fixes.

Stay here when the user explicitly needs `yellowbrick.contrib` objects, an
experimental decision boundary, missing-value visualization, an adapter for a
third-party estimator, already-computed predictions, or statsmodels integration.

## Correct import paths

Do **not** import these objects from top-level `yellowbrick.contrib`; that package
initializer does not hoist them. Use the concrete modules below:

| Need | Correct import |
|---|---|
| 2D feature scatter | `from yellowbrick.contrib.scatter import ScatterVisualizer, scatterviz` |
| Decision boundaries | `from yellowbrick.contrib.classifier.boundaries import DecisionBoundariesVisualizer, decisionviz` |
| Missing-value counts/locations | `from yellowbrick.contrib.missing import MissingValuesBar, MissingValuesDispersion` |
| Pre-computed predictions | `from yellowbrick.contrib.prepredict import PrePredict` |
| Third-party estimator wrapper | `from yellowbrick.contrib.wrapper import ContribEstimator, wrap, classifier, regressor, clusterer` |
| Wrapper type constants | `from yellowbrick.contrib.wrapper import CLASSIFIER, REGRESSOR, CLUSTERER` |
| statsmodels adapter | `from yellowbrick.contrib.statsmodels import StatsModelsWrapper` |

`yellowbrick.contrib.classifier` also exports `DecisionViz` and
`DecisionBoundariesVisualizer`, but the explicit `boundaries` path is the safest
public guidance.

## Covered objects

- `ScatterVisualizer` / `scatterviz`: bivariate feature scatter for exactly two
  selected features, with `classes`, `color`/`colormap`, `markers`, and `alpha`.
- `DecisionBoundariesVisualizer` / `DecisionViz` / `decisionviz`: experimental
  two-feature classifier decision-boundary mesh with optional scatter overlay.
- `MissingValuesBar` and `MissingValuesDispersion`: missing-value counts and
  missing-value positions by feature, optionally colored by target class.
- `PrePredict`: a scikit-learn-like estimator that returns predictions computed
  elsewhere and can score classifier/regressor/clusterer outputs.
- `ContribEstimator`, `wrap`, `classifier`, `regressor`, `clusterer`: wrappers
  for third-party estimators that mostly implement the scikit-learn API but do
  not subclass scikit-learn base classes or expose Yellowbrick-friendly type
  metadata.
- `StatsModelsWrapper`: a lightweight prototype adapter for statsmodels GLM-like
  estimators so Yellowbrick regressor visualizers can call `fit`, `predict`, and
  `score`.

## Required read order for future agents

1. Read [API reference](references/api-reference.md) for exact signatures,
   import paths, type constants, optional dependencies, and behavior limits.
2. Read [workflows](references/workflows.md) for safe recipes covering scatter,
   decision boundaries, missing values, wrappers, `PrePredict`, statsmodels, and
   headless saving.
3. If anything fails, read contrib-specific
   [troubleshooting](references/troubleshooting.md), then root
   [troubleshooting](../../references/troubleshooting.md) for package-wide
   dependency and Matplotlib issues.
4. For a no-network smoke check, run
   [contrib_smoke.py](scripts/contrib_smoke.py). It forces Matplotlib `Agg`,
   uses synthetic data, writes a PNG, and performs a tiny wrapper check.

## Minimal operating patterns

### Contrib scatter

```python
from yellowbrick.contrib.scatter import ScatterVisualizer

viz = ScatterVisualizer(features=["feature_a", "feature_b"], classes=["no", "yes"])
viz.fit(X_two_columns, y_encoded_as_0_or_1)
viz.transform(X_two_columns)
viz.show(outpath="contrib_scatter.png", clear_figure=True)
```

Use `features=[...]` for arrays, or `x="col_a", y="col_b"` for named data.
`ScatterVisualizer` accepts only two plotted features; route broader feature EDA
to stable feature-target visualizers.

### Decision boundaries

```python
from sklearn.neighbors import KNeighborsClassifier
from yellowbrick.contrib.classifier.boundaries import DecisionBoundariesVisualizer

viz = DecisionBoundariesVisualizer(
    KNeighborsClassifier(n_neighbors=3),
    features=["x0", "x1"],
    classes=["class 0", "class 1"],
    step_size=0.02,          # coarser than the default for fast reports
    show_scatter=True,
)
viz.fit(X_train_2d, y_train)
viz.draw(X_test_2d, y_test)
viz.show(outpath="decision_boundary.png", clear_figure=True)
```

Decision boundaries are classifier-only and bivariate. Use a small sample or a
coarser `step_size` for CI and agent-generated reports because the mesh grid can
be expensive.

### Wrapping non-sklearn estimators

```python
from yellowbrick.contrib.wrapper import wrap, CLASSIFIER
from yellowbrick.classifier import ClassificationReport

model = wrap(third_party_classifier, CLASSIFIER)
viz = ClassificationReport(model, classes=class_names, is_fitted="auto")
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="wrapped_report.png", clear_figure=True)
```

Set the estimator type explicitly when Yellowbrick or scikit-learn cannot infer
whether the wrapped object is a classifier, regressor, clusterer, density
estimator, or outlier detector. Add properties to a custom `ContribEstimator`
subclass when a visualizer needs learned attributes such as `classes_`, `coef_`,
`feature_importances_`, or `predict_proba`.

## Validation checklist

Before handing off a contrib workflow:

- Confirm imports use concrete contrib submodules, not top-level
  `yellowbrick.contrib`.
- Confirm a stable core visualizer is not a better fit.
- Confirm classifier/regressor/clusterer type metadata for wrappers and
  `PrePredict`.
- Confirm decision-boundary and scatter inputs contain exactly two plotted
  features, with explicit feature names where arrays are used.
- Confirm class display names match encoded target order; use encoders or sorted
  labels deliberately.
- Confirm optional `pandas` or `statsmodels` requirements are installed before
  giving code that depends on them.
- Confirm headless scripts set `matplotlib.use("Agg")` before importing
  `pyplot` and write non-empty files with `show(outpath=...)`.
- Ignore stale contributor example patterns that depend on missing local data,
  obsolete contrib modules, or deprecated NumPy aliases.
