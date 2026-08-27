# Estimators And Refuters

This reference maps DoWhy `method_name` strings to built-in classic effect
estimators, refuters, and sensitivity tools. Use it with `api-reference.md` and
`workflows.md`.

## Method-name grammar

### Estimation

`model.estimate_effect` requires a method name in one of these forms:

| Grammar | Meaning | Example |
|---|---|---|
| `<identifier>.<dowhy_estimator>` | Built-in DoWhy estimator. | `backdoor.linear_regression` |
| `<identifier>.dowhy.<dowhy_estimator>` | Explicit built-in DoWhy estimator spelling. | `backdoor.dowhy.linear_regression` |
| `<identifier>.econml.<path.to.Class>` | Optional EconML estimator wrapper. | `backdoor.econml.dml.LinearDML` |
| `<identifier>.causalml.<path.to.Class>` | Optional CausalML estimator wrapper. | `backdoor.causalml.inference.meta.LRSRegressor` |

The `<identifier>` prefix is written into `identified_estimand.identifier_method`
and must match a non-null estimand key. Common prefixes are `backdoor`,
`general_adjustment`, `iv`, `frontdoor`, and `mediation`.

### Refutation

`model.refute_estimate` takes a refuter module name without an identifier prefix,
for example `random_common_cause` or `placebo_treatment_refuter`. It requires a
valid `CausalEstimate` first.

## Built-in estimator choices

| Method name | Identification prefix | Best use | Key parameters | Important limits |
|---|---|---|---|---|
| `backdoor.linear_regression` | `backdoor` or `general_adjustment` | Transparent baseline outcome model; continuous or binary treatments depending design. | `test_significance`, `confidence_intervals`, `num_simulations`, `num_null_simulations`, `need_conditional_estimates`. | Assumes linear outcome relationship; analytic intervals/std errors are not implemented with effect modifiers and fall back to bootstrap. |
| `backdoor.generalized_linear_model` | `backdoor` or `general_adjustment` | GLM outcome model such as logistic regression. | `glm_family`, `predict_score`, bootstrap parameters. | `glm_family` is required; choose a statsmodels family compatible with the outcome. |
| `backdoor.propensity_score_matching` | `backdoor` or `general_adjustment` | Binary-treatment matching on propensity score. | `propensity_score_model`, `propensity_score_column`, `target_units`. | Requires observed confounders and binary one-dimensional treatment. |
| `backdoor.propensity_score_stratification` | `backdoor` or `general_adjustment` | Binary-treatment subclassification. | `num_strata`, `clipping_threshold`, `propensity_score_model`, `propensity_score_column`. | Too few treated/control units per stratum raises errors or drops strata. |
| `backdoor.propensity_score_weighting` | `backdoor` or `general_adjustment` | Inverse-propensity weighting for binary treatment. | `weighting_scheme`, `min_ps_score`, `max_ps_score`, `propensity_score_model`, `propensity_score_column`. | Extreme propensity scores are clipped; inspect overlap. |
| `backdoor.distance_matching` | `backdoor` or `general_adjustment` | Binary-treatment matching on covariate distances. | `num_matches_per_unit`, `distance_metric`, metric params such as `p`, `V`, `VI`, `w`, and `fit_params.exact_match_cols`. | Requires observed confounders, one treatment, binary treatment, and enough matches. |
| `backdoor.doubly_robust` | `backdoor` or `general_adjustment` | ATE with outcome regression plus propensity weighting. | `regression_estimator`, `propensity_score_model`, `propensity_score_column`, `min_ps_score`, `max_ps_score`. | Built-in implementation supports one treatment, one outcome, ATE only, and no effect modifiers. |
| `iv.instrumental_variable` | `iv` | Wald or 2SLS-style instrumental variable effect. | `iv_instrument_name`. | Requires identified instruments; number of instruments must be at least number of treatments for multi-treatment 2SLS. |
| `iv.regression_discontinuity` | `iv` | Local threshold design represented as an IV problem. | `rd_variable_name`, `rd_threshold_value`, `rd_bandwidth`. | Requires meaningful threshold and enough data in the bandwidth. |
| `frontdoor.two_stage_regression` | `frontdoor` | Singleton frontdoor mediator with linear two-stage estimation. | `first_stage_model`, `second_stage_model`, bootstrap parameters. | Only singleton treatment/frontdoor mediator patterns are supported by this built-in path. |
| `mediation.two_stage_regression` | `mediation` | Natural indirect/direct effect with linear stages. | `first_stage_model`, `second_stage_model`; choose `estimand_type` in `identify_effect`. | Use with `nonparametric-nie` or `nonparametric-nde`; complex multi-mediator structures need caution. |
| `backdoor.tabpfn` | `backdoor` | Optional TabPFN outcome-model estimator for tabular data. | `model_type`, `n_estimators`, `max_num_classes`, `use_multi_gpu`, `device_ids`. | Requires `tabpfn` and `torch`; model weights/access may be gated; best under TabPFN sample/feature limits. |
| `backdoor.econml...` / `iv.econml...` | `backdoor` or `iv` | Optional advanced CATE/ML estimators. | `method_params={"init_params": {...}, "fit_params": {...}}`. | Requires EconML and its dependencies; see `econml-cate.md`. |
| `backdoor.causalml...` | usually `backdoor` | Optional CausalML meta-learners. | `method_params={"init_params": {...}}`. | Requires CausalML; supports depend on the wrapped estimator. |

## Choosing a native built-in estimator

1. Start from identification, not estimator availability.
2. For a simple ATE baseline, use `backdoor.linear_regression` and a refuter.
3. For binary treatment with measured confounders and overlap concerns, compare
   at least one propensity method with a regression method.
4. For natural experiments, use `iv.instrumental_variable` only after the graph
   identifies instruments and the design assumptions are credible.
5. For frontdoor or mediation, use `two_stage_regression` and verify singleton
   mediator/frontdoor assumptions.
6. For heterogeneous effects with ML, use optional EconML/CausalML only after
   dependencies and target feature schema are verified.
7. For high-cost optional TabPFN, verify package, model access, and compute
   budget; do not use it as a default required estimator.

## Parameters that matter

### Common estimation parameters

| Parameter | Applies to | Notes |
|---|---|---|
| `target_units` | Most estimators | Strings `ate`, `att`, `atc`; subset lambda or DataFrame only where supported. |
| `control_value`, `treatment_value` | Most estimators | Scalars or lists depending treatment dimensionality. |
| `effect_modifiers` | Regression/EconML/some estimators | Drives conditional effects; not part of identification. |
| `fit_estimator=False` | `CausalModel.estimate_effect` | Reuse cached estimator for exact method name and compatible schema. |
| `test_significance=True` or `'bootstrap'` | Estimators | May use estimator-specific p-values or bootstrap; set simulation count for runtime. |
| `confidence_intervals=True` or `'bootstrap'` | Estimators | Bootstrap defaults can be expensive; use small counts for smoke tests. |
| `method_params["fit_params"]` | Estimator `fit` calls | Use for options such as `exact_match_cols` or EconML `fit` kwargs. |
| `need_conditional_estimates` | Estimator init | `auto` computes conditional estimates when effect modifiers exist; set `False` for speed. |

### Matching and propensity specifics

| Parameter | Meaning |
|---|---|
| `propensity_score_model` | Any classifier with `fit` and `predict_proba`; default is logistic regression. |
| `propensity_score_column` | Reuse an existing propensity-score column or name one to create. |
| `weighting_scheme` | For weighting: `ips_weight`, `ips_stabilized_weight`, or `ips_normalized_weight`; target-specific prefixes are derived internally. |
| `min_ps_score`, `max_ps_score` | Clip propensity scores to avoid infinite weights. |
| `num_strata`, `clipping_threshold` | Control stratification bins and minimum treated/control units per stratum. |
| `distance_metric`, `num_matches_per_unit` | Nearest-neighbor matching choices. |
| `fit_params.exact_match_cols` | Distance matching columns that must match exactly before continuous distance matching. |

### IV and natural experiment specifics

| Parameter | Meaning |
|---|---|
| `iv_instrument_name` | Use one or more identified instruments explicitly; defaults to all identified instruments. |
| `rd_variable_name` | Running variable for regression discontinuity; used as a local instrument. |
| `rd_threshold_value` | Threshold where assignment changes. |
| `rd_bandwidth` | Local window around the threshold; too narrow yields low data, too wide weakens local design. |

### Two-stage specifics

| Parameter | Meaning |
|---|---|
| `first_stage_model` | Optional first-stage `CausalEstimator` class or instance; default linear regression. |
| `second_stage_model` | Optional second-stage `CausalEstimator` class or instance; default linear regression. |

## Built-in refuters

| `method_name` | Diagnostic | Key parameters | Expected signal |
|---|---|---|---|
| `random_common_cause` | Adds an independent random covariate as a common cause. | `num_simulations`, `random_state`, `n_jobs`, `verbose`. | Estimate should remain in the same ballpark. |
| `placebo_treatment_refuter` | Replaces treatment with random or permuted placebo. | `num_simulations`, `placebo_type` (`"Random Data"` or `"permute"`), `random_state`, `n_jobs`, `verbose`. | Effect on placebo should be near zero. Use `permute` for IV placebo paths. |
| `data_subset_refuter` | Reruns estimator on random data subsets. | `subset_fraction`, `num_simulations`, `random_state`, `n_jobs`, `verbose`. | Estimate should be stable under reasonable subsampling. |
| `bootstrap_refuter` | Reruns on bootstrap samples and optional noise in variables. | `num_simulations`, `sample_size`, `required_variables`, `noise`, `probability_of_change`, `random_state`, `n_jobs`, `verbose`. | Estimate should be stable under resampling/noise. |
| `dummy_outcome_refuter` | Replaces outcome with known synthetic/dummy outcome. | `num_simulations`, `transformation_list`, `true_causal_effect`, `required_variables`, `bucket_size_scale_factor`, `min_data_point_threshold`, `random_state`, `n_jobs`, `verbose`. | Estimated effect should match the known dummy effect, often zero. |
| `add_unobserved_common_cause` | Sensitivity to unobserved confounding. | See below. | Effect should not flip or become practically unacceptable under plausible confounding. |
| `assess_overlap` | Overlap diagnostic for propensity methods. | Method-specific overlap options. | Use before trusting propensity-based estimates. |

`show_progress_bar=True` can be passed to `model.refute_estimate`; simulation
refuters also accept `n_jobs` and `verbose` where supported.

## Sensitivity analysis choices

### Direct simulation unobserved common cause

```python
result = model.refute_estimate(
    identified_estimand,
    estimate,
    method_name="add_unobserved_common_cause",
    simulation_method="direct-simulation",
    confounders_effect_on_treatment="binary_flip",  # or "linear"
    confounders_effect_on_outcome="linear",         # or "binary_flip"
    effect_strength_on_treatment=0.01,
    effect_strength_on_outcome=0.02,
    n_jobs=1,
    verbose=0,
)
```

Use arrays/lists for effect strengths to see a range or heatmap-like grid of
new effects. If effect strengths are omitted, DoWhy can infer ranges from
observed confounders; state the assumption that observed confounders bound the
unobserved one.

### Linear partial R2 sensitivity

```python
result = model.refute_estimate(
    identified_estimand,
    estimate,
    method_name="add_unobserved_common_cause",
    simulation_method="linear-partial-R2",
    benchmark_common_causes=["W1"],
    effect_fraction_on_treatment=[1, 2, 3],
    effect_fraction_on_outcome=1,
    percent_change_estimate=1.0,
    plot_estimate=False,
)
```

Best for linear-regression-style estimates. Output includes robustness-value and
bias-adjusted quantities. Stop if benchmark variables are absent or partial R2
values exceed valid ranges.

### Non-parametric partial R2 sensitivity

```python
result = model.refute_estimate(
    identified_estimand,
    estimate,
    method_name="add_unobserved_common_cause",
    simulation_method="non-parametric-partial-R2",
    partial_r2_confounder_treatment=0.05,
    partial_r2_confounder_outcome=0.05,
    num_splits=3,
    plot_estimate=False,
)
```

Use this for non-parametric/ML estimators when required nuisance estimators and
sample sizes are available. It is heavier than direct simulation.

### E-value

```python
result = model.refute_estimate(
    identified_estimand,
    estimate,
    method_name="add_unobserved_common_cause",
    simulation_method="e-value",
    plot_estimate=False,
)
```

Use for supported linear regression or GLM estimates when a risk-ratio-style
unmeasured-confounding diagnostic is appropriate. Stop if the estimator/family
is unsupported by the E-value analyzer.

## Parallel refutation

The refuters `bootstrap_refuter`, `placebo_treatment_refuter`,
`random_common_cause`, `data_subset_refuter`, `dummy_outcome_refuter`, and
direct-simulation `add_unobserved_common_cause` accept `n_jobs` and `verbose` in
this DoWhy build. Use conservative defaults in examples:

```python
ref = model.refute_estimate(
    identified_estimand,
    estimate,
    method_name="data_subset_refuter",
    num_simulations=20,
    n_jobs=1,      # change to -1 or a positive core count after a smoke run
    verbose=0,
    random_state=7,
)
```

Do not default to all cores in reusable code. Refuters repeatedly fit estimators;
parallelism can multiply memory and optional-ML model cost.

## Native behavior anchors preserved

The generated skill preserves these native behavior facts for later verification
planning:

- `backdoor.linear_regression` is the core CPU-safe estimator baseline.
- `backdoor.propensity_score_matching` covers binary-treatment propensity
  workflows.
- The auto identifier detects no directed path and marks the effect as zero.
- `estimate_effect`, `do`, and `refute_estimate` raise `ValueError` when
  `method_name=None`.
- IV estimation raises a clear error when no valid instruments are present or
  too few instruments exist.
- Random common cause, placebo treatment, data subset, bootstrap, dummy outcome,
  and add-unobserved-common-cause refuters are the main robustness/sensitivity
  surfaces.
