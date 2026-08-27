# Feature and Target Visualizer Workflows

Use these workflows to choose, prepare, run, and save Yellowbrick feature/target diagnostics. Shared Matplotlib and lifecycle details live in [visualizer patterns](../../../references/visualizer-patterns.md).

## 1. Choose the visualizer

| User intent | Prefer | Why | Escalate/route |
|---|---|---|---|
| "Which columns look unusual independently?" | `Rank1D` | Scores each feature by a univariate ranking algorithm, usually Shapiro-Wilk. | For model-based feature importance or RFECV, route to [cluster-model-selection](../../cluster-model-selection/SKILL.md). |
| "Which columns are correlated or redundant?" | `Rank2D` | Pairwise heatmap for Pearson, covariance, Spearman, or Kendall tau. | Use `FeatureCorrelation` when the relationship is feature-to-target, not feature-to-feature. |
| "Are classes separable in raw feature space?" | `RadialVisualizer` or `ParallelCoordinates` | Class-colored multivariate views before fitting a model. | For fitted classifier reports/ROC/confusion matrices, route to [classifier-visualizers](../../classifier-visualizers/SKILL.md). |
| "Can I plot high-dimensional rows in 2D/3D quickly?" | `PCA` | Fast, linear, supports returned transformed data, optional feature projections and loadings heatmap. | Try `Manifold` only when non-linear structure is worth the cost. |
| "Can I explore non-linear embedding structure?" | `Manifold` | Wraps sklearn manifold learners including LLE, Isomap, MDS, spectral embedding, and t-SNE. | Bound rows/features, set `random_state`, and use `fit_transform` for algorithms without `transform`. |
| "How does one feature relate to another or to y?" | `JointPlot` | Scatter/hexbin plus marginal histograms and a correlation score. | For all-pairs feature screening use `Rank2D`; for all feature-to-y scores use `FeatureCorrelation`. |
| "Is my classifier target imbalanced?" | `ClassBalance` | Bar chart of class support, with optional train/test comparison. | Cross-link to [classifier-visualizers](../../classifier-visualizers/SKILL.md) after imbalance is understood. |
| "Where should I bin a continuous target?" | `BalancedBinningReference` | Histogram plus reference bin boundaries. | Use downstream modeling guidance elsewhere after deciding bins. |
| "Which features relate most to y?" | `FeatureCorrelation` | Pearson or mutual-information feature-to-target scores. | Use `JointPlot` to inspect one suspicious pair in detail. |

## 2. Prepare inputs safely

Feature visualizers assume a rectangular feature matrix:

```python
# X: array-like or DataFrame of shape (n_samples, n_features)
# y: optional or required one-dimensional array-like of length n_samples
feature_names = ["radius", "texture", "smoothness", "compactness"]
class_names = ["benign", "malignant"]
```

Rules that avoid most runtime errors:

- If `X` is a NumPy array, pass `features=feature_names` or `labels=feature_names` when names matter.
- If pandas is unavailable or optional pandas handling fails, convert DataFrames/Series explicitly to arrays and pass names manually.
- Keep `len(features) == X.shape[1]`; Yellowbrick validates this on feature visualizer `fit()`.
- Keep `len(classes)` or `len(labels)` equal to the number of discovered classes for class-colored plots.
- For projections with ambiguous numeric targets, pass `target_type="discrete"` for class labels or `target_type="continuous"` for regression-like colorbars.
- Use finite numeric features. NaNs are filtered by some visualizers, but treating missing values before plotting makes comparisons clearer.

## 3. Save plots in headless jobs

Use a non-interactive backend before importing pyplot and create one figure per visualizer.

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from yellowbrick.features import Rank2D

fig, ax = plt.subplots(figsize=(7, 6))
viz = Rank2D(ax=ax, features=feature_names, algorithm="pearson")
viz.fit(X, y)
viz.transform(X)
viz.show(outpath="feature_rank2d.png", clear_figure=True)
plt.close(fig)
```

Prefer the class API for generated reports because `show(outpath=...)` is explicit. Quick methods are good for notebooks or short checks, but many quick signatures do not expose `outpath`; keep the returned visualizer if you need to save afterward.

## 4. Rank and screen features

Use `Rank1D` for one feature at a time and `Rank2D` for pairwise structure.

```python
from yellowbrick.features import Rank1D, Rank2D

rank1 = Rank1D(features=feature_names, algorithm="shapiro", orient="h")
rank1.fit(X, y)
rank1.transform(X)
rank1.show(outpath="rank1d.png", clear_figure=True)

rank2 = Rank2D(features=feature_names, algorithm="spearman")
rank2.fit(X, y)
rank2.transform(X)
rank2.show(outpath="rank2d_spearman.png", clear_figure=True)
```

Selection tips:

- `Rank1D(algorithm="shapiro")` is about distribution shape, not predictive usefulness.
- `Rank2D(algorithm="pearson")` is the default linear correlation-style view.
- `Rank2D(algorithm="spearman")` or `"kendalltau"` is better for monotonic but non-linear relationships.
- `Rank2D(algorithm="covariance")` depends on scale; standardize first if scales differ substantially.

## 5. Inspect class separability before modeling

For compact class-separability views:

```python
from yellowbrick.features import RadialVisualizer, ParallelCoordinates

rad = RadialVisualizer(features=feature_names, classes=class_names, alpha=0.6)
rad.fit(X, y)
rad.show(outpath="radviz.png", clear_figure=True)

pc = ParallelCoordinates(
    features=feature_names,
    classes=class_names,
    normalize="standard",
    sample=200,
    shuffle=True,
    random_state=42,
)
pc.fit(X, y)
pc.show(outpath="parallel_coordinates.png", clear_figure=True)
```

Selection tips:

- `RadialVisualizer` normalizes columns internally for the circular layout, but extreme outliers can still dominate perceived structure.
- `ParallelCoordinates(normalize="standard"|"minmax"|"l1"|"l2"|"maxabs")` makes differently-scaled axes comparable.
- Use `sample=<int>` or a fraction for large datasets. Use `fast=True` when drawing every instance is too slow and density detail is less important.

## 6. Use PCA before expensive manifold learning

PCA is the default first projection because it is fast, deterministic with `random_state`, and returns transformed features.

```python
from yellowbrick.features import PCA

viz = PCA(
    features=feature_names,
    classes=class_names,
    scale=True,
    projection=2,
    proj_features=True,
    random_state=42,
)
Xp = viz.fit_transform(X, y)
viz.show(outpath="pca_projection.png", clear_figure=True)
```

PCA choices:

- `scale=True` is usually appropriate unless features are already intentionally scaled.
- `projection=2` is easiest to save and annotate; `projection=3` requires a 3D axes and is harder to compare in static reports.
- `proj_features=True` adds feature loading arrows; use explicit feature names.
- `heatmap=True` shows feature contributions in 2D only and is incompatible with 3D projections.

## 7. Bound manifold learning

Use `Manifold` when PCA hides known non-linear structure. Always bound the problem first: sample rows, select columns, set `random_state`, and set `n_neighbors` for neighbor methods.

```python
from yellowbrick.features import Manifold

viz = Manifold(
    manifold="isomap",
    n_neighbors=10,
    features=feature_names,
    classes=class_names,
    target_type="discrete",
    random_state=42,
)
embedding = viz.fit_transform(X_small, y_small)
viz.show(outpath="isomap_projection.png", clear_figure=True)
```

Algorithm tradeoffs:

| Algorithm | Separate `fit`/`transform`? | Practical guidance |
|---|---:|---|
| `lle`, `ltsa`, `hessian`, `modified` | Yes | Local-neighborhood views; sensitive to `n_neighbors`; can fail or look unstable with small/noisy data. |
| `isomap` | Yes | Good first non-linear manifold choice after PCA; specify `n_neighbors`. |
| `mds` | No | Often expensive in memory/time; use very small samples and `fit_transform`. |
| `spectral` | No | Graph-based embedding; neighbor-sensitive; use `fit_transform`. |
| `tsne` | No | Stochastic and expensive; use small samples, set `random_state`, and use `fit_transform`. |

Do not generate every manifold/doc-style image in normal agent runs. The manifold image-generation examples are reference patterns only; they include downloads or expensive algorithm sweeps that are unsuitable for routine verification.

## 8. Diagnose the target

Use target visualizers outside estimator pipelines.

```python
from yellowbrick.target import ClassBalance, BalancedBinningReference, FeatureCorrelation

# Classification target support.
bal = ClassBalance(labels=class_names)
bal.fit(y_train, y_test)  # omit y_test for single-split balance mode
bal.show(outpath="class_balance.png", clear_figure=True)

# Continuous target bin reference.
binref = BalancedBinningReference(target="price", bins=5)
binref.fit(y_regression)
binref.show(outpath="target_binning.png", clear_figure=True)

# Feature-to-target scores.
fc = FeatureCorrelation(method="mutual_info-regression", labels=feature_names, sort=True)
fc.fit(X, y_regression, random_state=42)
fc.show(outpath="feature_correlation.png", clear_figure=True)
```

Target choices:

- `ClassBalance.fit(y_train, y_test=None)` takes target vectors only; do not pass `X` as the first argument.
- `ClassBalance(labels=...)` should use labels in the same order as the encoded target classes.
- `BalancedBinningReference` expects a one-dimensional numeric target.
- Use `FeatureCorrelation(method="pearson")` for linear association, `"mutual_info-regression"` for continuous targets, and `"mutual_info-classification"` for class targets.

## 9. Drill into one relationship with JointPlot

```python
from yellowbrick.features import JointPlot

# Feature-vs-target: one selected feature against y.
jp = JointPlot(columns="age", correlation="spearman", hist="density")
jp.fit(X_dataframe, y)
jp.show(outpath="age_target_jointplot.png", clear_figure=True)

# Feature-vs-feature: two selected feature columns.
jp2 = JointPlot(columns=["age", "income"], kind="hex", hist=True)
jp2.fit(X_dataframe)
jp2.show(outpath="age_income_jointplot.png", clear_figure=True)
```

Use `kind="hex"`/`"hexbin"` for dense continuous pairs. Use `hist=False` if Matplotlib histogram axes are causing layout issues or if the plot must stay compact.

## 10. Smoke-test this sub-skill

Run the bundled helper to verify imports, headless rendering, one feature ranking/projection workflow, and target diagnostics without network access:

```bash
python skills/disco/yellowbrick/sub-skills/feature-target-visualizers/scripts/feature_target_smoke.py --outdir ./yellowbrick-feature-target-smoke
```

The helper creates synthetic data and writes PNG files for feature and target visualizers. It is not a benchmark and does not validate image similarity.
