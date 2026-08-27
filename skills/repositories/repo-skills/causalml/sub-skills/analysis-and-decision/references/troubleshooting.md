# Analysis and decision troubleshooting

Use this checklist when scoring, sensitivity, feature-selection, interpretation, or optimization APIs produce surprising results.

## Metric frame and orientation problems

### Scores look inverted

Curve and ranking functions sort model columns in descending order. Higher predictions are treated as higher treatment priority. If a model emits a lower-is-better risk or cost score, negate or transform it before calling `get_cumgain`, `get_qini`, `auuc_score`, `get_toc`, or `rate_score`.

### Feature columns are being scored as models

Metric helpers treat every non-reserved column as a model prediction column. Build a narrow scoring frame containing only:

- `y` when observed outcomes are needed,
- `w` when binary treatment is needed,
- `tau` or another treatment-effect proxy when available,
- one or more prediction columns.

Do not pass the full modeling DataFrame with raw features unless each non-reserved feature is intended to be scored as a prediction.

### Wrong treatment labels or control-name mistakes

Most metric/ranking APIs assume binary `w` with `1` = treated and `0` = control. For string or multi-arm labels, create an explicit binary contrast:

```python
score_df["w"] = (source_df["treatment_group_key"] == "treatment1").astype(int)
```

For learners or optimization APIs with `control_name`, make sure the supplied control label exactly matches the data. A mismatch changes which group is treated as baseline and can silently invert CATE/value columns.

### Qini with true treatment effects fails or behaves unexpectedly

Even when `tau` is available, keep a binary treatment column for Qini workflows because Qini uses cumulative treated counts. For safest compatibility, include `y`, `w`, `tau`, and model prediction columns in the scoring frame.

### Observational curves are overconfident

When only observed `y` and `w` are supplied, uplift/TOC curves use difference-in-means within prioritized subsets. This is appropriate for randomized experiments but can be biased in observational data. For observational settings, compute cross-fitted doubly robust pseudo-outcomes and pass them as the treatment-effect column for ranking metrics.

### Bootstrap interval errors

- `n_bootstrap` must be at least 2.
- `alpha` must satisfy `0 < alpha < 1`.
- `qini_score(..., return_ci=True)` can report `NaN` p-values for degenerate scores with zero or non-finite standard error.
- `auuc_score(..., tmle=True, return_ci=True)` and `qini_score(..., tmle=True, return_ci=True)` are not supported; use TMLE plotting helpers with `ci=True` or non-TMLE score intervals.

## CATE scoring issues

### `dr_score` asks for `X` or `pseudo_outcome_col`

Provide one of:

- a precomputed pseudo-outcome column, usually from `compute_dr_pseudo_outcomes`, or
- `X`, outcome/treatment columns, and outcome learner(s) so pseudo-outcomes can be computed internally.

For repeated model comparisons, precompute the pseudo-outcome once and reuse it.

### Lower score is better

`dr_score`, `plug_in_t_score`, and `rlearner_score` are losses. A smaller value means the model's CATE estimates are closer to the surrogate effect target.

### Extreme propensity scores dominate

Use `p_clip_bounds` in `compute_dr_pseudo_outcomes`/`dr_score`, and inspect overlap. Very small or very large propensities can produce high-variance pseudo-outcomes and unstable ranking curves.

## TMLE validation issues

### `TMLELearner` has no `fit_predict`

In causalml 0.17.0, `TMLELearner` exposes `estimate_ate` but not `fit_predict`. Use TMLE through `estimate_ate` or the TMLE metric helpers, not as a base learner for workflows that require `fit_predict`.

### Segment curves have too few rows per segment

`get_tmlegain` and `get_tmleqini` segment rows by ranked model score. Reduce `n_segment`, increase data size, or check treatment balance if segment ATEs are unstable.

## Sensitivity analysis issues

### Learner does not support required methods

Base sensitivity summaries call learner `fit_predict` and `estimate_ate`. Use S/T/X/R/DR-style learners that expose these methods. TMLE-only learners are not drop-in compatible with the base sensitivity summary path.

### String treatment labels break selection bias

Selection-bias confounding functions multiply by `treatment`, so use numeric `0`/`1` treatment for `SensitivitySelectionBias`. For string-labeled data, create a binary copy and use a learner configured with the matching `control_name` if needed.

### `Subset Data` raises on missing sample size

`SensitivitySubsetData` requires `sample_size`; pass a fraction such as `0.5` through `sensitivity_analysis(..., sample_size=0.5)` or the class constructor.

### MSM rejects the learner or Gamma values

`SensitivityMSM` requires S-, T-, or DR-learner-style objects whose `fit_predict(return_components=True)` returns potential-outcome regressions. X-learner and R-learner are not supported. All `gamma` values must be at least `1.0`.

### `SensitivityRandomFeature` import fails

There is no public `SensitivityRandomFeature` class in causalml 0.17.0. Use `SensitivityRandomCause` to add an irrelevant random feature or `SensitivityRandomReplace` to replace an existing feature.

## Feature selection and interpretation issues

### `FilterSelect` method spelling

Use exact method strings: `"F"`, `"LR"`, `"KL"`, `"ED"`, or `"Chi"`. Other strings are routed to divergence logic and may fail unclearly.

### Binary-outcome requirement

`LR`, `KL`, `ED`, and `Chi` require the outcome column to contain only `{0, 1}`. Use `F` for continuous outcomes.

### Invalid polynomial order

For `F` and `LR`, `order` must be `1`, `2`, or `3`.

### Nulls in divergence features

For `KL`, `ED`, and `Chi`, pass `null_impute="mean"`, `"median"`, or `"most_frequent"`, or impute selected feature columns before calling `FilterSelect`. With `null_impute=None`, nulls raise an exception.

### Statsmodels convergence or singular design warnings

`LR` uses logistic regression with interaction terms. If it fails to converge or sees separation/singularity, reduce polynomial order, remove constant or near-constant features, combine sparse bins, or use `F`/divergence filters as a screening fallback.

### SHAP or importances fail

Meta-learner interpretation helpers build a tau model from `X` to `tau`. Use a tree-compatible model for `model_tau_feature`; SHAP uses `shap.TreeExplainer`. If optional SHAP or LightGBM dependencies are missing or incompatible, install/repair those dependencies or use non-SHAP feature filters.

### `FeatureEffectExplainer` import fails

`FeatureEffectExplainer` is not present as a public causalml 0.17.0 API. Use meta-learner `get_importance`, `plot_importance`, `get_shap_values`, `plot_shap_values`, `plot_shap_dependence`, uplift tree `feature_importances_`, or `FilterSelect`.

## Optimization issues

### `PolicyLearner` estimator rejects `sample_weight`

The `policy_learner` is fit with `sample_weight=abs(dr_score)`. Choose a classifier whose `fit` accepts `sample_weight`, such as decision-tree or many ensemble classifiers, or wrap the estimator accordingly.

### `PolicyLearner.predict_proba` indexing fails

`predict_proba` returns column `[:, 1]`. The underlying policy classifier must expose `predict_proba` with a binary class layout. Check `policy.model_pi.classes_` if the positive class is not where expected.

### Pandas indexing errors in `PolicyLearner`

The cross-fitting implementation indexes `X` with NumPy index arrays. Convert feature data to `X.values` or another NumPy array before fitting.

### Counterfactual unit selector sees missing classes

`CounterfactualUnitSelector` trains classifiers on observed treatment/outcome segments. If a segment is absent in a fold or full data, `predict_proba` columns may not match expected segment logic. Increase data, stratify sampling, or choose a simpler base classifier with robust class handling.

### Counterfactual value recommendations return integers

`CounterfactualValueEstimator.predict_best()` returns integer indices into `[control_name] + treatment_names`, not labels. Convert with the same `conditions` list used to build cost matrices.

### Counterfactual value columns are misordered

`cate[:, j]` must correspond to `treatment_names[j]`, and cost matrices must follow `[control_name] + treatment_names`. Misordered conditions are the most common cause of plausible but wrong value recommendations.

### PNS/PN/PS bounds divide by zero or fail

Use exact `type` values: `"PNS"`, `"PN"`, or `"PS"`. Ensure binary `T`/`Y` values and non-zero required observational cells: `(T=1, Y=1)` for `PN`, `(T=0, Y=0)` for `PS`.

## Stale or absent modules

Do not route current neural, validation, or interpretation work through `causalml.inference.nn`; that module path is absent in causalml 0.17.0. Current neural backends are under TensorFlow, Torch, and JAX subpackages and are handled by the deep-models sub-skill.
