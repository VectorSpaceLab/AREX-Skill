---
name: cluster-model-selection
description: "Use Yellowbrick clustering diagnostics and model-selection
  visualizers for k selection, validation curves, cross-validation scores,
  RFECV, feature importances, and dropping curves."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Yellowbrick Cluster and Model Selection Visualizers

Use this sub-skill when the user needs Yellowbrick visual diagnostics for unsupervised clustering or for scikit-learn model-selection workflows that train many estimator clones. It covers:

- clustering diagnostics: `KElbowVisualizer`, `SilhouetteVisualizer`, `InterclusterDistance`, and `kelbow_visualizer`/`silhouette_visualizer`/`intercluster_distance` quick methods;
- cross-validation and hyperparameter diagnostics: `ValidationCurve`, `LearningCurve`, and `CVScores`;
- feature selection and feature-rank diagnostics: `RFECV`, `FeatureImportances`, and `DroppingCurve`.

## Route elsewhere when

- The request is for classifier score plots such as confusion matrices, ROC/PR curves, class prediction error, classification reports, or discrimination thresholds: route to [classifier visualizers](../classifier-visualizers/SKILL.md).
- The request is for regressor score plots such as residuals, prediction error, Cook's distance, or alpha selection: route to [regressor visualizers](../regressor-visualizers/SKILL.md).
- The request is for dataset download/cache/loaders or text visualizers: route to `../text-and-datasets/SKILL.md` when that sub-skill is available.
- The request is mainly about Matplotlib backend, `show(outpath=...)`, axes reuse, Yellowbrick style, or shared lifecycle mechanics: read root [visualizer patterns](../../references/visualizer-patterns.md) first, then return here for cluster/model-selection choices.
- The failure is a broad installation, backend, font, display, or scikit-learn compatibility issue: read root [troubleshooting](../../references/troubleshooting.md), then this sub-skill's [troubleshooting](references/troubleshooting.md).

## Fast routing

| User goal | Use | Key requirements |
|---|---|---|
| Pick a candidate number of clusters `k` | `KElbowVisualizer` | Centroid-style clusterer with `n_clusters`, `fit`, and `labels_`; tune `k`, `metric`, `timings`, and `locate_elbow`. |
| Compare cluster density and imbalance for one `k` | `SilhouetteVisualizer` | Clusterer with `fit_predict` or `fit`+`predict`; at least two non-empty clusters. |
| Show relative cluster-center distances | `InterclusterDistance` | Clusterer with `cluster_centers_` and `labels_`; `embedding` is `"mds"` or `"tsne"`; `scoring` is currently `"membership"`. |
| Tune one estimator hyperparameter | `ValidationCurve` | Exact `param_name`, 1-D `param_range`, explicit `cv`, valid `scoring`, bounded `n_jobs`. |
| Ask whether more data helps | `LearningCurve` | Bounded `train_sizes`, explicit `cv`, valid `scoring`; works with classifiers, regressors, and some clusterers. |
| Show fold-to-fold score spread | `CVScores` | Estimator plus `cv` strategy and scoring; displays per-fold bars and mean line. |
| Choose number of features with recursive elimination | `RFECV` | Estimator must expose `coef_` or `feature_importances_` after fit; `step` must be positive. |
| Rank features from a fitted model | `FeatureImportances` | Estimator must expose `feature_importances_` or `coef_`; pass `labels`, `relative`, `absolute`, `stack`, and `topn` deliberately. |
| Estimate how many random features are enough | `DroppingCurve` | Bounded `feature_sizes`, explicit `cv`, `scoring`, `n_jobs`, and `random_state`; trains many clones. |

## Required read order for future agents

1. Read [API reference](references/api-reference.md) for import paths, signatures, learned attributes, and validation constraints.
2. Read [workflows](references/workflows.md) for bounded recipes covering k selection, CV/scoring/n_jobs choices, feature ranking, RFECV, and dropping curves.
3. If anything fails, read [troubleshooting](references/troubleshooting.md) and then root [troubleshooting](../../references/troubleshooting.md) for shared install/display/compatibility issues.
4. Run [model_selection_smoke.py](scripts/model_selection_smoke.py) with synthetic data when you need a safe local check. It forces Matplotlib `Agg`, performs no network access, and writes PNGs plus `manifest.json`.

## Minimal k-selection workflow

```python
import matplotlib
matplotlib.use("Agg")

from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from yellowbrick.cluster import KElbowVisualizer, SilhouetteVisualizer

X, _ = make_blobs(n_samples=240, n_features=6, centers=4, random_state=42)

elbow = KElbowVisualizer(
    KMeans(random_state=42, n_init=10),
    k=(2, 8),
    metric="distortion",
    timings=False,
)
elbow.fit(X)
elbow.show(outpath="k_elbow.png", clear_figure=True, bbox_inches="tight")

chosen_k = elbow.elbow_value_ or 4
sil = SilhouetteVisualizer(KMeans(n_clusters=chosen_k, random_state=42, n_init=10))
sil.fit(X)
sil.show(outpath="silhouette.png", clear_figure=True, bbox_inches="tight")
```

Do not treat `elbow_value_ is None` as a hard failure. A smooth elbow curve often means the data are not strongly clustered or the candidate range/metric is not informative; compare `metric="silhouette"`, `metric="calinski_harabasz"`, and explicit silhouette plots before recommending a final `k`.

## Minimal model-selection workflow

```python
import numpy as np
import matplotlib
matplotlib.use("Agg")

from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from yellowbrick.model_selection import ValidationCurve, CVScores

X, y = make_classification(
    n_samples=180, n_features=10, n_informative=5, random_state=42
)
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

validation = ValidationCurve(
    LogisticRegression(max_iter=1000, solver="liblinear"),
    param_name="C",
    param_range=np.logspace(-2, 1, 4),
    logx=True,
    cv=cv,
    scoring="f1_weighted",
    n_jobs=1,
)
validation.fit(X, y)
validation.show(outpath="validation_curve.png", clear_figure=True, bbox_inches="tight")

scores = CVScores(
    LogisticRegression(max_iter=1000, solver="liblinear"),
    cv=cv,
    scoring="f1_weighted",
)
scores.fit(X, y)
scores.show(outpath="cv_scores.png", clear_figure=True, bbox_inches="tight")
```

## Expensive-run controls

Model-selection visualizers clone and fit estimators many times. Before running on user data, bound the work:

- Use synthetic or sampled data first to validate imports, scoring, and output paths.
- Set explicit `cv` with a small fold count during exploration; increase folds only after the visualizer works.
- Keep `param_range`, `train_sizes`, and `feature_sizes` short; expand ranges in a second pass.
- Use `n_jobs=1` for debuggability and memory-constrained agents. Raise `n_jobs` only when the estimator is thread/process safe and the host has capacity.
- Use `pre_dispatch="2*n_jobs"` or another bounded value when parallel jobs allocate large arrays.
- Set `random_state` on estimators, CV splitters, and `DroppingCurve` for reproducible review artifacts.
- Prefer `show(outpath=..., clear_figure=True, bbox_inches="tight")` over interactive display in scripts and CI.

## Validation checklist

Before handing off a cluster/model-selection result:

- Confirm the task belongs here rather than classifier/regressor score-plot sub-skills.
- Confirm the estimator exposes the methods/attributes required by the chosen visualizer.
- Confirm `param_name`, `param_range`, `train_sizes`, `feature_sizes`, `cv`, `scoring`, `n_jobs`, and `pre_dispatch` are explicit and bounded.
- Confirm saved output files are non-empty under a non-interactive Matplotlib backend.
- Inspect learned attributes such as `k_values_`, `k_scores_`, `silhouette_score_`, `train_scores_mean_`, `test_scores_mean_`, `cv_scores_`, `features_`, `feature_importances_`, `support_`, `ranking_`, and `valid_scores_mean_` before summarizing conclusions.
- If an elbow is not detected, report uncertainty and recommend alternate metrics/ranges instead of inventing a best `k`.
