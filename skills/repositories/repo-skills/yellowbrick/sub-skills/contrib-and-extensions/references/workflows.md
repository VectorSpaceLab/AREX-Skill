# Contrib Workflows

These workflows are for experimental/contrib functionality. Prefer stable core
sub-skills for ordinary classifier, regressor, feature/target, clustering, and
model-selection work.

## Shared setup for scripts and CI

Set a non-interactive Matplotlib backend before importing `pyplot`:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

Then save with `visualizer.show(outpath="plot.png", clear_figure=True)` and close
figures in long-running scripts. See root visualizer patterns for broader axes,
style, and headless rendering conventions.

## Choose the contrib tool

| User need | Use | Route away if |
|---|---|---|
| Inspect two features with a target-colored scatter | `ScatterVisualizer` | More than two features or ranking/projection is needed; use feature-target visualizers. |
| Plot a classifier's bivariate decision surface | `DecisionBoundariesVisualizer` | The task is a standard classifier report/ROC/PR/confusion matrix; use classifier visualizers. |
| Count missing values per feature | `MissingValuesBar` | The user needs imputation/modeling, not visualization; give preprocessing guidance outside Yellowbrick. |
| Show where missing values occur by row position | `MissingValuesDispersion` | The dataset is huge; sample first or summarize with `MissingValuesBar`. |
| Use predictions computed outside Yellowbrick | `PrePredict` | The target visualizer requires probabilities, decision scores, or many learned attributes. |
| Use a non-sklearn estimator with a Yellowbrick visualizer | `wrap` or `ContribEstimator` | A native scikit-learn estimator or stable Yellowbrick path is available. |
| Use statsmodels GLM with Yellowbrick regressor plots | `StatsModelsWrapper` | `statsmodels` is not installed or the model requires weights/options unsupported by the prototype wrapper. |

## 1. Bivariate contrib scatter

```python
import numpy as np
from yellowbrick.contrib.scatter import ScatterVisualizer

X = np.asarray(X)[:, [0, 2]]
y = np.asarray(y)

viz = ScatterVisualizer(
    features=["petal length", "petal width"],
    classes=["setosa", "other"],
    markers=["o", "^"],
    alpha=0.8,
)
viz.fit(X, y)
viz.transform(X)
viz.show(outpath="scatter.png", clear_figure=True)
```

Checklist:

- Ensure `X` has exactly two plotted columns or pass feature selectors.
- Prefer integer-encoded classes starting at zero. If labels are strings or
  non-contiguous integers, encode them before calling this contrib visualizer or
  test the result carefully.
- Use explicit feature names for arrays; DataFrame column names require optional
  `pandas`.

## 2. Fast decision-boundary plot

```python
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from yellowbrick.contrib.classifier.boundaries import DecisionBoundariesVisualizer

X, y = make_moons(noise=0.25, random_state=42)
X = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

viz = DecisionBoundariesVisualizer(
    KNeighborsClassifier(n_neighbors=3),
    features=["scaled x0", "scaled x1"],
    classes=["lower", "upper"],
    step_size=0.02,
    show_scatter=True,
)
viz.fit(X_train, y_train)
viz.draw(X_test, y_test)
viz.show(outpath="decision-boundary.png", clear_figure=True)
```

Use `step_size=0.01` to `0.05` for bounded agent/CI runs. The default `0.0025`
can create a dense mesh and slow down small reports. Use `show_scatter=False` if
the mesh itself is the only required artifact.

## 3. Missing-value visualization

```python
import numpy as np
from yellowbrick.contrib.missing import MissingValuesBar, MissingValuesDispersion

X = X.astype(float, copy=True)
X[X > 1.5] = np.nan
features = [f"feature {idx}" for idx in range(X.shape[1])]

bar = MissingValuesBar(features=features, classes=["negative", "positive"])
bar.fit(X, y)
bar.show(outpath="missing-counts.png", clear_figure=True)

disp = MissingValuesDispersion(features=features, classes=["negative", "positive"])
disp.fit(X, y)
disp.show(outpath="missing-dispersion.png", clear_figure=True)
```

Use the bar chart for summary counts. Use dispersion when row order matters, such
as temporal or ingestion-order missingness. For large matrices, sample rows or
columns before dispersion because every missing coordinate becomes a plotted
point.

## 4. Wrap a third-party estimator

```python
from yellowbrick.contrib.wrapper import CLASSIFIER, wrap
from yellowbrick.classifier import ClassificationReport

wrapped = wrap(third_party_classifier, CLASSIFIER)

viz = ClassificationReport(wrapped, classes=class_names, is_fitted="auto")
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="third-party-classifier.png", clear_figure=True)
```

If the visualizer raises a missing-attribute error, the wrapper has done its job:
it surfaced a concrete attribute that the third-party model must provide. Add a
small adapter subclass when needed:

```python
from yellowbrick.contrib.wrapper import ContribEstimator, CLASSIFIER

class MyClassifierAdapter(ContribEstimator):
    _estimator_type = CLASSIFIER

    @property
    def classes_(self):
        return self.estimator.labels_

    def predict_proba(self, X):
        return self.estimator.probability_matrix(X)
```

Then pass `MyClassifierAdapter(model)` to the stable classifier visualizer.

## 5. Use pre-computed predictions

```python
from yellowbrick.contrib.prepredict import PrePredict
from yellowbrick.contrib.wrapper import CLASSIFIER
from yellowbrick.classifier import ClassificationReport

model = PrePredict(y_pred_test, CLASSIFIER)

viz = ClassificationReport(model, classes=class_names)
viz.fit(None, y_train)      # establishes visualizer state; PrePredict fit is a no-op
viz.score(None, y_test)     # draws using y_pred_test
viz.show(outpath="prepredict-report.png", clear_figure=True)
```

Use `PrePredict` when training or inference happened elsewhere and only `y_pred`
is available. It is not a substitute for estimators that need probabilities,
decision scores, feature importances, coefficients, cluster centers, or other
learned attributes. For saved predictions, pass a `.npy` path or file-like object
that `np.load` can read.

## 6. statsmodels GLM with regressor plots

```python
from functools import partial
import statsmodels.api as sm
from yellowbrick.contrib.statsmodels import StatsModelsWrapper
from yellowbrick.regressor import PredictionError

glm_gaussian = partial(sm.GLM, family=sm.families.Gaussian())
model = StatsModelsWrapper(glm_gaussian)

viz = PredictionError(model)
viz.fit(X_train, y_train)
viz.score(X_test, y_test)
viz.show(outpath="statsmodels-prediction-error.png", clear_figure=True)
```

This adapter assumes the statsmodels constructor accepts `(y, X)` and exposes a
results object with `predict(X)`. If the user needs weights, formulas, robust
covariance options, or a pre-fitted results object, write a custom adapter around
the exact statsmodels object instead of relying on the prototype wrapper.

## 7. Local smoke check

Run the bundled helper from the sub-skill directory or by path:

```bash
python scripts/contrib_smoke.py --outdir /tmp/yellowbrick-contrib-smoke
```

Expected result: a non-empty `contrib_scatter.png` and a successful wrapper check
printed to stdout. The helper uses only synthetic data and performs no network
access.
