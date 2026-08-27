# Cluster and Model-Selection Troubleshooting

Use this reference after checking the API and workflow guidance. For broad install, backend, font, display, or package-version issues, also read root `../../references/troubleshooting.md`.

## `KElbowVisualizer`: no elbow detected

Symptom:

```text
No 'knee' or 'elbow' point detected, pass `locate_elbow=False` to remove the warning
```

What it means:

- The score curve is too smooth or monotonic for automatic knee detection.
- The data may not have strong cluster structure.
- The tested `k` range may be too narrow or too wide.
- The selected metric may not expose the structure.

Actions:

1. Do not report a fake best `k`; state that automatic elbow detection was inconclusive.
2. Re-run with `locate_elbow=False` if the warning is noisy but the plot is still useful.
3. Try another metric: `"silhouette"` or `"calinski_harabasz"`.
4. Change the candidate range, e.g. from `(2, 8)` to `(2, 12)` or a domain-informed iterable.
5. Validate candidates with `SilhouetteVisualizer` and downstream task/domain constraints.

## Clustering estimator rejected

Symptoms:

```text
The supplied model is not a clustering estimator
could not find or make cluster_centers_ for <Estimator>
```

Common causes and fixes:

- `KElbowVisualizer` expects a clustering estimator with `n_clusters`, `fit`, and `labels_` after fit. Use `KMeans` or `MiniBatchKMeans` first.
- `SilhouetteVisualizer` needs labels from `fit_predict` or `fit` + `predict`. Algorithms without stable labels for every sample may fail.
- `InterclusterDistance` currently requires `cluster_centers_` and `labels_`; many density or hierarchical clusterers do not expose centers.
- Yellowbrick 1.5 uses legacy scikit-learn estimator-type checks. If a normal scikit-learn clusterer is rejected under a very new scikit-learn release, use a Yellowbrick-compatible scikit-learn stack before rewriting the workflow.

## Invalid clustering parameters

- Invalid `k`: pass an integer, a two-integer tuple, or an iterable of integers. A tuple uses Python range semantics, so `(2, 8)` tests 2 through 7.
- Invalid elbow metric: use only `"distortion"`, `"silhouette"`, or `"calinski_harabasz"`.
- Invalid distance metric: use a metric accepted by scikit-learn pairwise distances, or a callable.
- Invalid intercluster embedding: use `"mds"` or `"tsne"`.
- Invalid intercluster scoring: use `"membership"`; other scoring modes are not implemented.
- Intercluster legend errors on old Matplotlib: set `legend=False` or use a compatible Matplotlib version.

## Silhouette scoring failures

Common causes:

- Only one cluster was produced, or every sample became its own cluster. Silhouette score requires at least two non-empty clusters and fewer clusters than samples.
- The estimator returned noise labels or labels not matching expected cluster indexes. Try a centroidal clusterer first to verify the workflow.
- A precomputed distance matrix was passed without matching metric behavior. Keep a normal feature matrix for first-pass diagnostics.

Actions:

1. Confirm `n_clusters` and the label distribution with `np.unique(labels, return_counts=True)`.
2. Reduce or increase `k` so clusters are non-empty.
3. If using a non-centroidal algorithm, validate that Yellowbrick supports its labels before using it in an automated report.

## `ValidationCurve`: invalid `param_name` or `param_range`

Symptoms:

```text
Invalid parameter ... for estimator ...
must specify array of param values
```

Fixes:

- Use `estimator.get_params().keys()` to find the exact parameter name.
- For pipelines, include the step prefix, such as `"model__C"` or `"classifier__max_depth"`.
- Ensure `param_range` is one-dimensional. Use lists, `np.arange(...)`, or `np.logspace(...)`, not a scalar or nested array.
- Use `logx=True` only when all parameter values are positive.

## Scoring errors

Symptoms:

```text
The 'scoring' parameter ... is invalid
Target is multiclass but average='binary'
Estimator has none of the following attributes: predict_proba, decision_function
```

Fixes:

- Match scoring to task type:
  - classification: `"accuracy"`, `"f1_weighted"`, `"precision_weighted"`, `"recall_weighted"`;
  - regression: `"r2"`, `"neg_mean_absolute_error"`, `"neg_root_mean_squared_error"`;
  - clustering with known labels: metrics such as `"adjusted_rand_score"` when supported by the scorer.
- Avoid binary-only scorers on multiclass targets unless configured for multiclass.
- Probability-based scorers require estimators exposing `predict_proba` or `decision_function`.
- If the user really wants classifier ROC/PR/threshold plots, route to the classifier sub-skill instead of using model-selection curves.

## CV split failures

Symptoms:

```text
n_splits=... cannot be greater than the number of members in each class
The least populated class in y has only ... members
```

Fixes:

- Reduce `n_splits` for small or imbalanced datasets.
- Use `StratifiedKFold` for classification and ensure every class has enough examples per fold.
- Use `KFold` or `ShuffleSplit` for regression.
- Use grouped splitters only when `groups` has the same length as `X` and `y`.
- For ordered data, set `shuffle=True` where appropriate and a fixed `random_state`.

## Expensive or stalled model-selection runs

`ValidationCurve`, `LearningCurve`, `RFECV`, and `DroppingCurve` can fit dozens or hundreds of estimator clones.

Controls:

- Start with small grids: 3-5 parameter values, 3 CV folds, and short `train_sizes`/`feature_sizes`.
- Set `n_jobs=1` for first failure diagnosis; raise it only after memory and estimator thread-safety are known.
- Set `pre_dispatch="2*n_jobs"` instead of `"all"` when arrays or estimator clones are large.
- Downsample or use synthetic data to verify plotting and scoring before full data.
- Use simpler estimators for first-pass visual checks, then rerun with the final estimator.
- Persist figures after each visualizer so a later failure does not lose earlier outputs.

## `FeatureImportances` failures

Symptoms:

```text
could not find feature importances param on <Estimator>
```

Fixes:

- Use an estimator that exposes `feature_importances_` after fit, such as tree ensembles.
- Or use a linear model exposing `coef_`, such as `LogisticRegression`, `LinearSVC`, `Ridge`, or `Lasso`.
- For already-fitted estimators, pass `is_fitted=True` to avoid unintended refits.
- If feature labels look numeric, pass `labels=[...]` or use a DataFrame with columns.
- If coefficients are negative and magnitude matters, set `absolute=True`; if raw signed values matter, set `relative=False`.
- If multidimensional coefficients trigger a stack warning, either accept the mean aggregation or set `stack=True` for a compatible multiclass model.
- If `topn` is greater than the feature count, lower `topn` before fitting.

## `RFECV` failures

Symptoms:

```text
step must be >0
estimator does not expose coef_ or feature_importances_
```

Fixes:

- Use a positive `step`; choose a larger integer step to reduce runtime on wide datasets.
- Use an estimator with `coef_` or `feature_importances_` after fit.
- Reduce `cv` folds and feature count for a first pass.
- Inspect `support_` and `ranking_` after fit before applying the selected subset elsewhere.
- If the curve is flat, state that RFECV did not find strong evidence for a specific subset size; compare with `FeatureImportances` and `DroppingCurve`.

## `DroppingCurve` failures

Symptoms:

```text
Expected feature sizes in [0, n_features]
Expected feature ratio in [0,1]
```

Fixes:

- Use positive integer feature counts less than or equal to the number of input features.
- Use float ratios greater than 0 and up to 1.0.
- Keep the grid short in CI, e.g. `[0.25, 0.5, 0.75, 1.0]`.
- Set `random_state` to make random subsets reproducible.
- Remember that `DroppingCurve` answers "how many features", not "which features".

## Matplotlib backend, fonts, and version edges

Symptoms:

```text
cannot connect to X server
font family ... not found
module 'matplotlib.cm' has no attribute 'get_cmap'
```

Fixes:

- Use `matplotlib.use("Agg")` before importing pyplot in scripts and CI.
- Treat font warnings as non-fatal if PNG/SVG output is non-empty.
- Yellowbrick 1.5 may hit compatibility edges with very new Matplotlib or scikit-learn releases. Prefer a Yellowbrick-compatible scientific stack for production reports. The bundled smoke helper includes local compatibility shims only to keep its synthetic checks focused on visualizer behavior.
- If output files are empty, rerun with `clear_figure=True`, close all Matplotlib figures between plots, and verify the output directory is writable.

## Quick triage commands

```bash
python - <<'PY'
import matplotlib
matplotlib.use("Agg")
import yellowbrick, sklearn, matplotlib as mpl
print("yellowbrick", yellowbrick.__version__)
print("sklearn", sklearn.__version__)
print("matplotlib", mpl.__version__)
PY

python skills/disco/yellowbrick/sub-skills/cluster-model-selection/scripts/model_selection_smoke.py --task elbow --outdir /tmp/yb-elbow
python skills/disco/yellowbrick/sub-skills/cluster-model-selection/scripts/model_selection_smoke.py --task validation --outdir /tmp/yb-validation
python skills/disco/yellowbrick/sub-skills/cluster-model-selection/scripts/model_selection_smoke.py --task dropping --outdir /tmp/yb-dropping
```
