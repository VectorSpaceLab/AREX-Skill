# sklearn Interface Troubleshooting

Use this page when a pandas/sklearn AIF360 workflow fails before falling back to legacy dataset or algorithm APIs. Optional dependency workflows are optional/unverified unless the matching extra has been installed and checked.

## Install and import problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ImportError` or warnings mentioning `tensorflow`, `fairlearn`, `torch`, `rpy2`, `inFairness`, `skorch`, or `ot` | The requested branch needs an optional extra not installed in the base package. | Install only the needed extra, for example `aif360[AdversarialDebiasing]`, `aif360[Reductions]`, `aif360[LFR]`, `aif360[FairAdapt]`, `aif360[inFairness]`, or `aif360[OptimalTransport]`; then run a tiny workflow before claiming support. |
| Base sklearn metrics import but optional estimator construction fails later with `NameError` or missing module messages | Some AIF360 modules log a warning at import time but fail only when the extra-gated class is used. | Treat the class as unavailable until the extra is installed. Do not confuse a module-level import with workflow verification. |
| `pip check` or import conflicts after upgrading sklearn | AIF360's package metadata constrains scikit-learn below 1.6 for this version. | Reinstall with a compatible scikit-learn release and re-run the base import/metric smoke. |
| `ot_distance will be unavailable` or `name 'ot' is not defined` | POT is not installed. | Install `aif360[OptimalTransport]` only for optimal-transport fairness requests; otherwise use base group metrics. |

## Fetcher, data, and cache problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Fetcher hangs, times out, or fails with network errors | First use needs network because cache is cold. | Avoid fetchers for no-network smokes. For real workflows, pass a caller-approved `data_home`, keep `cache=True`, or require the user to provide a warmed cache/data file. |
| `fetch_meps` prompts for terms or raises `PermissionError: Terms not agreed.` | MEPS data require explicit acceptance. | Ask the caller to confirm terms acceptance; then use `accept_terms=True`. Do not silently bypass the prompt. |
| Unexpected row drops or shapes | `dropna=True`, `numeric_only=True`, default `dropcols`, or dataset-specific preprocessing changed the data. | Check the exact fetcher signature in [API reference](api-reference.md#dataset-functions). Remember `standardize_dataset` applies `usecols`, `dropcols`, `numeric_only`, then `dropna`. |
| `NumericConversionWarning` with `numeric_only=True` | Protected attributes or target values are non-numeric while feature columns are being filtered. | This can be expected. Preserve protected attrs in the index, set `numeric_only=False`, encode categories deliberately, or pass explicit numeric protected arrays. |
| A fetched target is not binary | Some loaders are regression or multiclass-like. | Use metric/estimator branches appropriate to the target. For Law School GPA, treat the target as regression unless the caller defines a policy-safe binarization. |

## Protected-attribute and pandas API misuse

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `TypeError: arr does not include protected attributes in the index` | An upstream transform returned an ndarray or DataFrame with no protected-index levels. | Re-wrap transformed arrays as a DataFrame/Series with the original index, or pass explicit `prot_attr` arrays of matching length. |
| `Expected Series or DataFrame for arr` | `prot_attr=None` was used with non-pandas arrays. | Use pandas `Series`/`DataFrame` with protected attrs in the index, or pass explicit protected-attribute arrays via `prot_attr`. |
| `Expected 2 protected attribute groups` | A metric/postprocessor requested binary groups but the chosen `prot_attr` has one group or more than two groups. | Pick a binary protected attribute, binarize with a documented policy, or use metrics that support multi/intersectional groups. |
| Metrics look inverted | `priv_group` or `pos_label` is wrong for the dataset convention. | Inspect `y.unique()`, `y.index.get_level_values(...)`, and the fetcher notes. Difference metrics compute unprivileged minus privileged; ratio metrics compute unprivileged over privileged. |
| `sample_weight` seems ignored or misaligned | Some sklearn/AIF360 APIs treat weights positionally, and `RejectOptionClassifierCV` ignores weights during scoring. | Keep `X`, `y`, and weights in the same row order. For ROC CV, expect a warning and document that fairness scoring is unweighted. |

## Metric-specific failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `disparate_impact_ratio` returns zero, infinite, or warns about division | The privileged selection/base rate denominator is zero. | Choose the correct `priv_group`, inspect group rates, or pass `zero_division=0`/`1` for deterministic handling. |
| `average_odds_error(..., priv_group=None)` fails | Automatic privileged group inference requires exactly two groups. | Pass a concrete `priv_group` or select/binarize a protected attribute. |
| `make_scorer` appears to optimize the wrong direction | AIF360 scorers transform fairness metrics for sklearn's higher-is-better convention. | For differences, expect negative absolute disparity. For ratios, pass `is_ratio=True` and expect `min(ratio, 1/ratio)`. |
| `consistency_score` fails on categorical/string features | KNN-based consistency needs numeric feature arrays. | Encode or select numeric features first, then preserve index only if later group metrics need it. |
| `mdss_bias_score` gives a trivial score | `subset=None` scores the full set, or the specified subset does not match rows/features. | Provide an explicit subset mapping or hand off to `detectors-and-explainers` for full MDSS subgroup scanning. |
| `ot_distance` type or mode errors | The optional OT metric expects `Series` predictions for `binary`/`continuous` modes and `DataFrame` predictions for `nominal`/`ordinal` modes. | Match `mode` to target/prediction shape, install `aif360[OptimalTransport]`, and run a tiny call before using it in a workflow. |

## Estimator and workflow-specific failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Reweighing` does not fit into an sklearn `Pipeline` as a normal transformer | It returns transformed sample weights, not a transformed feature matrix. | Use `ReweighingMeta` around an estimator that accepts `sample_weight`, or call `fit_transform` manually and pass the returned weights to the classifier. |
| `ReweighingMeta` raises that the estimator has no `sample_weight` fit parameter | The wrapped estimator cannot consume reweighted samples. | Choose an estimator with `fit(..., sample_weight=...)` or use a different mitigation method. |
| `AdversarialDebiasing does not work in eager execution mode` | TensorFlow eager execution is enabled. | In TensorFlow v1-compatible workflows, disable eager execution before fitting. This branch is optional/unverified unless TensorFlow is installed and a tiny fit passes. |
| `FairAdapt` fails before fit or tries to reach R package installation | `rpy2`, R, or required R packages are missing. | Prepare R/rpy2 and the required R packages in a controlled environment before constructing `FairAdapt`; treat the workflow as optional/unverified until run. |
| Reductions wrappers cannot import `fairlearn` or reject constraints | `aif360[Reductions]` is missing, or `constraints` is not a supported string/Moment. | Install the Reductions extra and use supported constraints such as `DemographicParity`, `EqualizedOdds`, `TruePositiveRateParity`, `FalsePositiveRateParity`, `ErrorRateParity`, or `BoundedGroupLoss` for grid-search regression. |
| `GridSearchReduction.predict_proba` raises `NotImplementedError` | The selected branch is regression or an underlying model without probabilities. | Use `predict` for regression, or choose a classification estimator/constraint that exposes probabilities. |
| `SenSeI`/`SenSR` fail around torch modules, criteria, or distances | The `inFairness` extra or required torch/skorch objects are not prepared. | Install `aif360[inFairness]`, build distance objects, pass a torch module and criterion, and set `regression` explicitly for ambiguous targets. |
| `PostProcessingMeta` says the postprocessor needs `predict_proba` | The base estimator lacks `predict_proba` while the postprocessor has `requires_proba=True`. | Use a base classifier with `predict_proba`, calibrate/wrap it, or choose a postprocessor that does not require probabilities. |
| `PostProcessingMeta` leaks data or gives unstable results | It was placed inside a larger pipeline or fit with inappropriate validation splitting. | Put preprocessing/model pipeline inside `PostProcessingMeta(estimator=...)`. Tune `val_size`, `shuffle`, and `random_state` through the meta-estimator options. |
| `RejectOptionClassifier` or `CalibratedEqualizedOdds` says binary classification is required | More than two class labels or probability columns were supplied. | Reduce to a binary task with a documented policy, provide `labels` matching probability columns, or choose a different fairness workflow. |
| `RejectOptionClassifier` margin/threshold validation fails | `threshold` is outside `[0, 1]`, or `margin > min(threshold, 1-threshold)`. | Use a valid threshold and margin, or let `RejectOptionClassifierCV` generate valid combinations. |

## When to route away

- If the input is an AIF360 legacy dataset object, use the sibling `datasets-and-metrics` sub-skill.
- If the request asks for legacy mitigation classes under `aif360.algorithms`, use the sibling `mitigation-algorithms` sub-skill.
- If the request asks to discover biased subgroups with MDSS or FACTS or to explain legacy metric objects in text/JSON, use the sibling `detectors-and-explainers` sub-skill.
