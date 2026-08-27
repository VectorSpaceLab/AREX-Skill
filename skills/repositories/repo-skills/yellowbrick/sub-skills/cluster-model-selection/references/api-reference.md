# Yellowbrick Cluster/Model-Selection API Reference

This reference summarizes the Yellowbrick APIs owned by the `cluster-model-selection` sub-skill. Use it to choose imports, parameters, and learned attributes before writing code.

## Imports

```python
from yellowbrick.cluster import (
    KElbowVisualizer,
    KElbow,
    kelbow_visualizer,
    SilhouetteVisualizer,
    silhouette_visualizer,
    InterclusterDistance,
    intercluster_distance,
)
from yellowbrick.model_selection import (
    ValidationCurve,
    validation_curve,
    LearningCurve,
    learning_curve,
    CVScores,
    cv_scores,
    RFECV,
    rfecv,
    FeatureImportances,
    feature_importances,
    DroppingCurve,
    dropping_curve,
)
```

Prefer class visualizers for reproducible scripts and saved reports. Use quick methods only for notebook-style one-offs or when you pass `show=False` and save the returned visualizer yourself.

## Clustering diagnostics

### `KElbowVisualizer`

Signature:

```python
KElbowVisualizer(
    estimator,
    ax=None,
    k=10,
    metric="distortion",
    distance_metric="euclidean",
    timings=True,
    locate_elbow=True,
    **kwargs,
)
```

Use for preliminary `k` selection on centroid-style clusterers such as `KMeans` and `MiniBatchKMeans`.

- `k` may be an integer, a `(start, stop)` tuple, or an iterable of integers.
  - Integer `10` becomes `2..10` inclusive.
  - Tuple `(2, 8)` becomes `range(2, 8)` with stop exclusive.
  - Iterable values are used exactly.
- `metric` must be one of `"distortion"`, `"silhouette"`, or `"calinski_harabasz"`.
- `distance_metric` is used for distortion/silhouette distance calculations; use a scikit-learn pairwise distance metric name or a callable.
- `timings=True` adds a second y-axis showing fit time per `k`; set `False` for compact reports.
- `locate_elbow=True` attempts automatic knee detection. If no knee is found, Yellowbrick emits a warning and sets `elbow_value_` to `None`.
- `fit(X, y=None, **kwargs)` forwards extra fit parameters such as `sample_weight` to the wrapped estimator when supported.

Learned attributes after `fit`:

- `k_values_`: tested values of `k`;
- `k_scores_`: score for each `k`;
- `k_timers_`: fit time for each `k`;
- `elbow_value_`: detected best `k`, or `None`;
- `elbow_score_`: score at the detected elbow, or `0` when none is found.

Quick method:

```python
viz = kelbow_visualizer(
    KMeans(random_state=0, n_init=10), X,
    k=(2, 8), metric="distortion", timings=False, show=False,
)
viz.show(outpath="elbow.png", clear_figure=True)
```

### `SilhouetteVisualizer`

Signature:

```python
SilhouetteVisualizer(estimator, ax=None, colors=None, is_fitted="auto", **kwargs)
```

Use after choosing one candidate `k` to inspect cluster density and imbalance. The estimator must provide labels through `fit_predict`, or through `fit` plus `predict`. Yellowbrick computes `silhouette_score` and per-sample `silhouette_samples`, draws one band per cluster, and adds a vertical average-score line.

Key parameters and attributes:

- `colors` may be a Yellowbrick/matplotlib colormap name or an iterable of colors.
- `is_fitted` controls whether Yellowbrick should refit the wrapped estimator.
- `silhouette_score_`: mean silhouette coefficient;
- `silhouette_samples_`: per-sample coefficients;
- `n_samples_`, `n_clusters_`, `y_tick_pos_`: plot support attributes.

Use several `SilhouetteVisualizer` plots side-by-side or in separate files when comparing `k` values; do not rely on one silhouette plot alone.

### `InterclusterDistance`

Signature:

```python
InterclusterDistance(
    estimator,
    ax=None,
    min_size=400,
    max_size=25000,
    embedding="mds",
    scoring="membership",
    legend=True,
    legend_loc="lower left",
    legend_size=1.5,
    random_state=None,
    is_fitted="auto",
    **kwargs,
)
```

Use to map learned cluster centers into two dimensions while scaling point size by cluster membership.

- `estimator` must expose `cluster_centers_` and `labels_` after fitting.
- `embedding` is `"mds"` or `"tsne"`; `"mds"` is usually the safer default.
- `scoring` currently supports `"membership"` only.
- `legend=False` is useful in tiny or crowded figures.
- `random_state` matters for stochastic embeddings.

Learned attributes after `fit`:

- `cluster_centers_`: proxied from the estimator;
- `embedded_centers_`: 2-D embedded centers;
- `scores_`: cluster sizes for the selected scoring method;
- `fit_time_`: timer for fit plus embedding.

Important interpretation rule: overlap in the 2-D map does not prove overlap in the original feature space; it indicates the embedding could not fully separate centers in two dimensions.

## Cross-validation and hyperparameter diagnostics

### `ValidationCurve`

Signature:

```python
ValidationCurve(
    estimator,
    param_name,
    param_range,
    ax=None,
    logx=False,
    groups=None,
    cv=None,
    scoring=None,
    n_jobs=1,
    pre_dispatch="all",
    markers="-d",
    **kwargs,
)
```

Use to vary exactly one hyperparameter and compare training vs cross-validation scores.

- `param_name` must match an estimator parameter key, including pipeline prefixes such as `"classifier__C"`.
- `param_range` must be a one-dimensional array-like of values to evaluate.
- `logx=True` is appropriate for multiplicative ranges such as `C`, `alpha`, or `gamma`.
- `scoring` must be valid for the estimator and target. Examples: `"f1_weighted"`, `"accuracy"`, `"r2"`, `"neg_mean_absolute_error"`, `"adjusted_rand_score"`.
- Pass explicit `cv` for reproducibility; small exploratory values such as 3 folds are often enough before expanding.
- `n_jobs` and `pre_dispatch` are forwarded to scikit-learn's validation-curve utility.

Learned attributes: `train_scores_`, `train_scores_mean_`, `train_scores_std_`, `test_scores_`, `test_scores_mean_`, `test_scores_std_`.

### `LearningCurve`

Signature:

```python
LearningCurve(
    estimator,
    ax=None,
    groups=None,
    train_sizes=np.linspace(0.1, 1.0, 5),
    cv=None,
    scoring=None,
    exploit_incremental_learning=False,
    n_jobs=1,
    pre_dispatch="all",
    shuffle=False,
    random_state=None,
    **kwargs,
)
```

Use to ask whether an estimator benefits from more training examples and whether the gap between train and validation scores suggests bias or variance.

- `train_sizes` must be one-dimensional. Floats are fractions of the maximum training size; integers are absolute sample counts.
- `shuffle=True` plus `random_state` makes size prefixes less order-dependent.
- `exploit_incremental_learning=True` can speed estimators supporting `partial_fit`, but keep it `False` unless you know the estimator supports it correctly.

Learned attributes: `train_sizes_`, `train_scores_`, `train_scores_mean_`, `train_scores_std_`, `test_scores_`, `test_scores_mean_`, `test_scores_std_`.

### `CVScores`

Signature:

```python
CVScores(estimator, ax=None, cv=None, scoring=None, color=None, **kwargs)
```

Use to visualize fold-to-fold score variability as bars plus an average-score line.

- Works with classification and regression estimators and pipelines that implement ordinary scikit-learn `fit`/`score` behavior.
- Does not expose `n_jobs`; control runtime through the estimator and the selected CV splitter.
- Use stratified splitters for classification support stability and shuffled splitters for ordered data.

Learned attributes: `cv_scores_` and `cv_scores_mean_`.

## Feature selection and ranking

### `FeatureImportances`

Signature:

```python
FeatureImportances(
    estimator,
    ax=None,
    labels=None,
    relative=True,
    absolute=False,
    xlabel=None,
    stack=False,
    colors=None,
    colormap=None,
    is_fitted="auto",
    topn=None,
    **kwargs,
)
```

Use to rank model-learned importances or coefficients.

- The estimator must expose `feature_importances_` or `coef_` after fit.
- If `labels` is `None` and `X` is a DataFrame, column names are used; otherwise numeric feature indexes are used.
- `relative=True` scales values so the strongest absolute component is 100.
- `absolute=True` converts negative coefficients to magnitudes before sorting/scaling.
- `stack=True` draws per-class stacked importances for compatible multiclass coefficient arrays.
- `topn=3` shows the three strongest features; `topn=-3` shows the three weakest.
- `is_fitted=True` prevents refitting an already-fitted estimator.

Learned attributes: `features_`, `feature_importances_`, and `classes_` when classifier classes are available.

### `RFECV`

Signature:

```python
RFECV(estimator, ax=None, step=1, groups=None, cv=None, scoring=None, **kwargs)
```

Use to visualize recursive feature elimination with cross-validation.

- The estimator must expose `coef_` or `feature_importances_` after fit.
- `step` must be positive. Values `>= 1` are numbers of features removed per iteration; values in `(0, 1)` are fractions of the feature count.
- `cv` and `scoring` are forwarded to `cross_val_score`.
- Yellowbrick wraps scikit-learn `RFE`, not scikit-learn `RFECV`, so inspect Yellowbrick's learned attributes rather than expecting scikit-learn RFECV internals.

Learned attributes: `n_features_`, `support_`, `ranking_`, `cv_scores_`, `rfe_estimator_`, and `n_feature_subsets_`. After fit, estimator methods such as `predict` and `score` are delegated to `rfe_estimator_`.

### `DroppingCurve`

Signature:

```python
DroppingCurve(
    estimator,
    ax=None,
    feature_sizes=np.linspace(0.1, 1.0, 5),
    groups=None,
    logx=False,
    cv=None,
    scoring=None,
    n_jobs=None,
    pre_dispatch="all",
    random_state=None,
    **kwargs,
)
```

Use to estimate performance as random subsets of features are retained. This complements `RFECV`: `RFECV` asks which specific features to keep, while `DroppingCurve` asks how many features of a similar type may be enough.

- Float `feature_sizes` are ratios of total features; integer values are absolute feature counts.
- Keep feature-size grids short during exploration, e.g. `[0.25, 0.5, 0.75, 1.0]`.
- Set `random_state` to make random feature subsets reproducible.
- `n_jobs` and `pre_dispatch` control the internal validation curve over feature subset sizes.

Learned attributes: `feature_sizes_`, `train_scores_`, `train_scores_mean_`, `train_scores_std_`, `valid_scores_`, `valid_scores_mean_`, and `valid_scores_std_`.

## Quick-method save pattern

All quick methods return the fitted visualizer. For automation, use `show=False` and save explicitly:

```python
viz = validation_curve(
    estimator, X, y,
    param_name="C",
    param_range=[0.1, 1.0, 10.0],
    cv=cv,
    scoring="f1_weighted",
    show=False,
)
viz.show(outpath="validation_curve.png", clear_figure=True, bbox_inches="tight")
```
