# Cluster and Model-Selection Workflows

These workflows are designed for future agents building Yellowbrick reports in scripts, notebooks, or CI. For shared lifecycle, style, axes, and `Agg` setup, load root `../../references/visualizer-patterns.md` first.

## Headless report setup

Use a non-interactive backend before importing pyplot or creating figures:

```python
import matplotlib
matplotlib.use("Agg")
```

Then save with:

```python
viz.show(outpath="plot.png", clear_figure=True, bbox_inches="tight", dpi=120)
```

Use class visualizers when you need attributes, error handling, or a saved report. Use quick methods with `show=False` when you want one-line fitting but still need controlled saving.

## Workflow 1: choose `k` without overclaiming

1. Generate or load numeric features. Do not route through dataset loaders from this sub-skill; use the datasets/text sub-skill when data cache behavior matters.
2. Run `KElbowVisualizer` across a bounded `k` range.
3. If `elbow_value_` is not detected, report that automatic elbow detection is inconclusive.
4. Compare at least one candidate with `SilhouetteVisualizer`; optionally map centers with `InterclusterDistance`.
5. Summarize uncertainty, metric choice, and candidate ranges.

```python
from sklearn.cluster import KMeans
from yellowbrick.cluster import KElbowVisualizer, SilhouetteVisualizer, InterclusterDistance

base = KMeans(random_state=42, n_init=10)

elbow = KElbowVisualizer(
    base,
    k=(2, 9),
    metric="distortion",
    timings=False,
    locate_elbow=True,
)
elbow.fit(X)
elbow.show(outpath="elbow_distortion.png", clear_figure=True, bbox_inches="tight")

candidate_k = elbow.elbow_value_ or 4
clusterer = KMeans(n_clusters=candidate_k, random_state=42, n_init=10)

sil = SilhouetteVisualizer(clusterer, colors="yellowbrick")
sil.fit(X)
sil.show(outpath="silhouette.png", clear_figure=True, bbox_inches="tight")

icd = InterclusterDistance(
    KMeans(n_clusters=candidate_k, random_state=42, n_init=10),
    embedding="mds",
    scoring="membership",
    legend=False,
    random_state=42,
)
icd.fit(X)
icd.show(outpath="intercluster_distance.png", clear_figure=True, bbox_inches="tight")
```

Interpretation rules:

- `distortion` usually decreases as `k` increases; look for the point where gains flatten.
- `silhouette` ranges from -1 to 1; higher average values are better, but inspect cluster-width balance as well.
- `calinski_harabasz` is often useful when distortion has no obvious elbow.
- If several metrics disagree, do not invent certainty. Report likely candidates and recommend domain or downstream validation.
- `InterclusterDistance` is a center-distance visualization, not proof of original-space overlap.

## Workflow 2: tune one hyperparameter with `ValidationCurve`

Use validation curves for one hyperparameter at a time. Start with a short range and small CV count, then expand.

```python
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from yellowbrick.model_selection import ValidationCurve

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
param_range = np.logspace(-2, 1, 4)

viz = ValidationCurve(
    LogisticRegression(max_iter=1000, solver="liblinear"),
    param_name="C",
    param_range=param_range,
    logx=True,
    cv=cv,
    scoring="f1_weighted",
    n_jobs=1,
    pre_dispatch="2*n_jobs",
)
viz.fit(X, y)
viz.show(outpath="validation_curve_C.png", clear_figure=True, bbox_inches="tight")
```

Read the curve as a bias/variance diagnostic:

- Low train and validation scores together suggest underfitting.
- High train score with lower validation score suggests variance/overfitting.
- A flat validation score may mean the chosen hyperparameter is not influential, the range is wrong, or another hyperparameter dominates.
- Always use the exact estimator parameter name. For a pipeline, include the step prefix, e.g. `"model__C"`.

## Workflow 3: ask whether more data or CV splits change conclusions

Use `LearningCurve` to assess sample-size sensitivity, and `CVScores` to show fold-to-fold variability.

```python
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from yellowbrick.model_selection import LearningCurve, CVScores

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
model = LogisticRegression(max_iter=1000, solver="liblinear")

lc = LearningCurve(
    model,
    train_sizes=np.linspace(0.3, 1.0, 4),
    cv=cv,
    scoring="f1_weighted",
    n_jobs=1,
    shuffle=True,
    random_state=42,
)
lc.fit(X, y)
lc.show(outpath="learning_curve.png", clear_figure=True, bbox_inches="tight")

scores = CVScores(model, cv=cv, scoring="f1_weighted")
scores.fit(X, y)
scores.show(outpath="cv_scores.png", clear_figure=True, bbox_inches="tight")
```

Use classification-appropriate scorers (`accuracy`, `f1_weighted`, `roc_auc_ovr_weighted` when probabilities are available) for classifiers and regression scorers (`r2`, `neg_mean_absolute_error`, `neg_root_mean_squared_error`) for regressors. For clusterers, use a scorer compatible with clustering predictions and available target/membership information.

## Workflow 4: feature ranking, RFECV, and dropping curves

Use `FeatureImportances` when you need model-learned feature ranks, `RFECV` when you need to select a subset by recursive elimination, and `DroppingCurve` when you need to estimate how many randomly retained features are enough.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from yellowbrick.model_selection import FeatureImportances, RFECV, DroppingCurve

labels = [f"feature_{idx}" for idx in range(X.shape[1])]
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

fi = FeatureImportances(
    RandomForestClassifier(n_estimators=50, random_state=42),
    labels=labels,
    topn=min(10, X.shape[1]),
)
fi.fit(X, y)
fi.show(outpath="feature_importances.png", clear_figure=True, bbox_inches="tight")

selector = RFECV(
    LogisticRegression(max_iter=1000, solver="liblinear"),
    step=2,
    cv=cv,
    scoring="f1_weighted",
)
selector.fit(X, y)
selector.show(outpath="rfecv.png", clear_figure=True, bbox_inches="tight")

# A compact feature-size grid keeps the first pass bounded.
drop = DroppingCurve(
    LogisticRegression(max_iter=1000, solver="liblinear"),
    feature_sizes=[0.25, 0.5, 0.75, 1.0],
    cv=cv,
    scoring="f1_weighted",
    n_jobs=1,
    pre_dispatch="2*n_jobs",
    random_state=42,
)
drop.fit(X, y)
drop.show(outpath="dropping_curve.png", clear_figure=True, bbox_inches="tight")
```

Selection rules:

- `FeatureImportances` is a ranking visualizer; it does not cross-validate a selected subset.
- `RFECV` is specific-feature selection and can be expensive because each feature subset performs CV over recursive elimination.
- `DroppingCurve` does not tell you which features to keep; it estimates performance as feature count changes under random subsets.
- For high-dimensional sparse text or one-hot data, first use a tiny sample and a short `feature_sizes` grid; route text/vectorizer details to the text/datasets sub-skill.

## Pipeline patterns

Two safe patterns are common:

1. Wrap a complete preprocessing-plus-estimator pipeline as the estimator:

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
viz = ValidationCurve(pipe, param_name="logisticregression__C", param_range=[0.1, 1.0, 10.0], cv=3)
viz.fit(X, y)
```

2. Use a visualizer as the final pipeline step when the visualizer itself should draw during pipeline `fit`:

```python
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("model_selection", CVScores(LogisticRegression(max_iter=1000), cv=3)),
])
pipe.fit(X, y)
pipe["model_selection"].show(outpath="cv_scores.png", clear_figure=True)
```

Keep Yellowbrick visualizers at the end of a pipeline. They are not general-purpose feature transformers for downstream estimators.

## Bounded smoke helper

Run the bundled helper before expensive user data runs:

```bash
python skills/disco/yellowbrick/sub-skills/cluster-model-selection/scripts/model_selection_smoke.py --outdir /tmp/yellowbrick-model-selection-smoke --task all
```

For targeted checks:

```bash
python skills/disco/yellowbrick/sub-skills/cluster-model-selection/scripts/model_selection_smoke.py --outdir /tmp/yellowbrick-elbow --task elbow
python skills/disco/yellowbrick/sub-skills/cluster-model-selection/scripts/model_selection_smoke.py --outdir /tmp/yellowbrick-validation --task validation
python skills/disco/yellowbrick/sub-skills/cluster-model-selection/scripts/model_selection_smoke.py --outdir /tmp/yellowbrick-dropping --task dropping
```

Expected output is one or more PNG files and a `manifest.json` with data shape, compatibility patches applied by the helper, and output byte sizes.
