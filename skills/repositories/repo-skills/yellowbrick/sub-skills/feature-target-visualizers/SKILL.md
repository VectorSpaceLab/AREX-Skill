---
name: feature-target-visualizers
description: "Use Yellowbrick feature and target visualizers for feature
  ranking, projection diagnostics, class balance, target binning, and
  feature-target correlation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Feature and Target Visualizers

Use this sub-skill when the task is to diagnose raw features, projected feature space, or the target variable before or alongside modeling with Yellowbrick. It covers `Rank1D`, `Rank2D`, `RadialVisualizer`, `ParallelCoordinates`, `PCA`, `Manifold`, `JointPlot`, `ClassBalance`, `BalancedBinningReference`, and `FeatureCorrelation`.

## Route first

- For common `fit`/`transform`/`show`, Matplotlib backend, style, axes, and headless saving patterns, read [shared visualizer patterns](../../references/visualizer-patterns.md).
- For API signatures and imports, read [API reference](references/api-reference.md).
- For visualizer choice and task workflows, read [workflows](references/workflows.md).
- For feature/target-specific failures, read [troubleshooting](references/troubleshooting.md); for package-wide install/display issues, also read [root troubleshooting](../../references/troubleshooting.md).

## Use this sub-skill for

- Ranking or screening columns: `Rank1D` for univariate distribution scoring; `Rank2D` for pairwise correlation/covariance-style structure.
- Class-separability plots in raw feature space: `RadialVisualizer`/`RadViz` and `ParallelCoordinates`.
- Dimensionality reduction plots: `PCA` for fast linear projections; `Manifold` for non-linear embeddings when the cost and algorithm limitations are acceptable.
- Pairwise or feature-vs-target distribution plots: `JointPlot`.
- Target diagnostics: `ClassBalance`, `BalancedBinningReference`, and `FeatureCorrelation`.
- Headless smoke checks for feature/target visualizer usage with `scripts/feature_target_smoke.py`.

## Route elsewhere

- Route cross-validation, validation/learning curves, feature importance, RFECV, clustering elbow/silhouette/intercluster distance, and other model-selection curves to [cluster-model-selection](../cluster-model-selection/SKILL.md).
- Route text-specific feature visualizers and dataset downloader/cache questions to [text-and-datasets](../text-and-datasets/SKILL.md).
- Route model-fitted classifier reports, confusion matrices, ROC/PR curves, prediction-error bars, and threshold tuning to [classifier-visualizers](../classifier-visualizers/SKILL.md). Stay here for `ClassBalance`; cross-link to classifier visualizers when the user proceeds from target imbalance to model diagnostics.

## Intake checklist

Before giving code or debugging advice, identify:

1. Whether the task is about `X` features, `y` target, or both.
2. Data shape: feature visualizers generally need `X.shape == (n_samples, n_features)`; target-only visualizers need a one-dimensional `y`.
3. Feature names and class names: prefer explicit `features`, `labels`, or `classes` lists when arrays are used or when optional pandas support is unavailable.
4. Whether `y` is classification-like or continuous; force `target_type="discrete"` or `target_type="continuous"` for projection visualizers when automatic inference is ambiguous.
5. Runtime constraints: use PCA before manifold learning for quick checks; sample rows or features for expensive plots; set a non-interactive Matplotlib backend for headless execution.
6. Output requirement: for files or CI reports, use the class API and `visualizer.show(outpath=..., clear_figure=True)`.

## Minimal operating pattern

```python
import matplotlib
matplotlib.use("Agg")  # set before pyplot in headless jobs
import matplotlib.pyplot as plt

from yellowbrick.features import Rank2D

fig, ax = plt.subplots(figsize=(7, 6))
viz = Rank2D(ax=ax, features=feature_names, algorithm="pearson")
viz.fit(X, y)
viz.transform(X)
viz.show(outpath="rank2d.png", clear_figure=True)
plt.close(fig)
```

Use `fit_transform(X, y)` for `PCA` and for `Manifold` algorithms that do not support a separate `transform()` step. Use separate target visualizers outside sklearn prediction pipelines because they fit directly on `y` rather than on `(X, y)` estimator data.
