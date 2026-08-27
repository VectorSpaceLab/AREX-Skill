# DoWhy GCM API Reference

This reference records the GCM APIs that are safe entry points for this
sub-skill. Use `from dowhy import gcm` or `import dowhy.gcm as gcm` in user
code. Graphs are normally NetworkX directed graphs, and data are pandas
DataFrames whose column labels match graph node labels.

## Core prerequisites

- The graph must be acyclic.
- Every graph node used by fitting or queries must have a data column with the
  same label.
- Every node must have a causal mechanism before `gcm.fit` or any query that
  validates fitted mechanisms.
- Root nodes need a stochastic model. Non-root nodes need a conditional
  stochastic model; structural models need functional causal models for
  non-root nodes.
- Fitting records each node's parents at fit time. If the graph structure is
  modified afterward, refit before drawing samples or running causal queries.
- Many GCM tasks assume causal sufficiency: the noise of a node should be
  independent of its parents after conditioning on modeled parents.

## Model classes

| Class | Verified constructor | Use when |
|---|---|---|
| `gcm.ProbabilisticCausalModel` | `(graph=None, graph_copier=nx.DiGraph, remove_existing_mechanisms=False)` | You need a flexible probabilistic graph for fitting, drawing samples, interventions, GCM ACE, direct arrow strength, distribution-change attribution, or model evaluation. |
| `gcm.StructuralCausalModel` | same constructor | You need functional causal mechanisms of parents plus noise, such as intrinsic influence or parent relevance. |
| `gcm.InvertibleStructuralCausalModel` | same constructor | You need to reconstruct sample-specific noise from observed data, such as point counterfactuals or anomaly attribution. |

Useful methods on model objects:

- `causal_model.set_causal_mechanism(node, mechanism)` assigns a mechanism.
- `causal_model.causal_mechanism(node)` returns the assigned mechanism.
- `causal_model.clone()` clones the graph and unfitted mechanisms.

## Automatic mechanism assignment

Verified signature:

```python
gcm.auto.assign_causal_mechanisms(
    causal_model,
    based_on,
    quality=gcm.auto.AssignmentQuality.GOOD,
    override_models=False,
    experimental_allow_nans=False,
)
```

Behavior:

- Root nodes receive an empirical distribution by default.
- Continuous non-root nodes receive additive noise models with selected
  regressors.
- Ordered discrete non-root nodes receive discrete additive noise models.
- Categorical non-root nodes receive classifier-based functional causal models;
  represent true categories as strings when automatic assignment should treat
  them as categorical.
- `AssignmentQuality.GOOD` evaluates a smaller, faster model set.
- `AssignmentQuality.BETTER` evaluates a larger model set and can be slower.
- `override_models=False` keeps already assigned mechanisms and validates their
  compatibility with the graph. Use `override_models=True` to replace existing
  mechanisms.
- `experimental_allow_nans=True` allows some numerical missing-data cases, but
  not every downstream GCM method supports missing data.

## Manual mechanisms

Common public mechanisms:

- Root distributions: `gcm.EmpiricalDistribution`, `gcm.ScipyDistribution`,
  `gcm.BayesianGaussianMixtureDistribution`,
  `gcm.GaussianMixtureDensityEstimator`, `gcm.KernelDensityEstimator1D`.
- Continuous structural mechanisms: `gcm.AdditiveNoiseModel` and
  `gcm.PostNonlinearModel`.
- Ordered discrete structural mechanisms: `gcm.DiscreteAdditiveNoiseModel`.
- Categorical mechanisms: `gcm.ClassifierFCM`.
- Prediction-model helpers live under `gcm.ml`, such as linear regressors,
  gradient boosting models, and scikit-learn adapters.

Manual assignment is the safer choice when the user has domain knowledge about
mechanism form, monotonicity, known noise, or known model families.

## Fit and draw APIs

Verified signatures:

```python
gcm.fit(causal_model, data, return_evaluation_summary=False)
gcm.draw_samples(causal_model, num_samples) -> pandas.DataFrame
```

Notes:

- `gcm.fit` fits each mechanism independently using its node and parent columns.
- `return_evaluation_summary=True` returns a lightweight
  `CausalModelEvaluationResult` focused on causal-mechanism performance.
- `gcm.draw_samples` validates the DAG and fitted local structures, then draws
  root-node samples and propagates downstream mechanisms in topological order.

## What-if APIs

Verified signatures:

```python
gcm.interventional_samples(
    causal_model,
    interventions,
    observed_data=None,
    num_samples_to_draw=None,
) -> pandas.DataFrame

gcm.counterfactual_samples(
    causal_model,
    interventions,
    observed_data=None,
    noise_data=None,
) -> pandas.DataFrame

gcm.average_causal_effect(
    causal_model,
    target_node,
    interventions_alternative,
    interventions_reference,
    observed_data=None,
    num_samples_to_draw=None,
) -> float
```

Intervention dictionaries map node names to callables. Atomic interventions use
functions such as `lambda _: value`; soft interventions can transform the
pre-intervention value, for example `lambda x: x + 0.5`.

For `interventional_samples` and `average_causal_effect`, pass exactly one of
`observed_data` or `num_samples_to_draw`. For `counterfactual_samples`, pass
exactly one of `observed_data` or `noise_data`. Starting from `observed_data`
requires an `InvertibleStructuralCausalModel` so noise can be reconstructed.

## Influence and relevance APIs

Verified signatures:

```python
gcm.arrow_strength(
    causal_model,
    target_node,
    parent_samples=None,
    num_samples_conditional=2000,
    max_num_runs=5000,
    tolerance=0.01,
    n_jobs=-1,
    difference_estimation_func=None,
) -> dict

gcm.intrinsic_causal_influence(
    causal_model,
    target_node,
    prediction_model="approx",
    attribution_func=None,
    num_training_samples=100000,
    num_samples_randomization=250,
    num_samples_baseline=1000,
    max_batch_size=-1,
    auto_assign_quality=gcm.auto.AssignmentQuality.GOOD,
    shapley_config=None,
) -> dict

gcm.parent_relevance(
    causal_model,
    target_node,
    parent_samples=None,
    subset_scoring_func=None,
    num_samples_randomization=5000,
    num_samples_baseline=500,
    max_batch_size=100,
    shapley_config=None,
) -> tuple

gcm.feature_relevance_distribution(
    prediction_method,
    feature_samples,
    subset_scoring_func,
    max_num_samples_randomization=5000,
    max_num_baseline_samples=500,
    max_batch_size=100,
    randomize_features_jointly=True,
    shapley_config=None,
) -> numpy.ndarray

gcm.feature_relevance_sample(
    prediction_method,
    feature_samples,
    baseline_samples,
    subset_scoring_func,
    baseline_target_values=None,
    average_set_function=False,
    max_batch_size=100,
    randomize_features_jointly=True,
    shapley_config=None,
) -> numpy.ndarray
```

Interpretation shortcut:

- `arrow_strength` ranks direct incoming edges to one target node.
- `intrinsic_causal_influence` ranks upstream noise contributions to a target.
- `parent_relevance` explains the fitted mechanism of one target in terms of
  its direct parents and noise.
- `feature_relevance_*` explains arbitrary prediction functions using
  background feature samples.

## Root-cause and distribution-change APIs

Verified signatures:

```python
gcm.anomaly_scores(
    causal_model,
    anomaly_data,
    num_samples_conditional=10000,
    num_samples_unconditional=10000,
    anomaly_scorer_factory=gcm.RescaledMedianCDFQuantileScorer,
) -> dict

gcm.attribute_anomalies(
    causal_model,
    target_node,
    anomaly_samples,
    anomaly_scorer=None,
    attribute_mean_deviation=False,
    num_distribution_samples=3000,
    shapley_config=None,
) -> dict

gcm.distribution_change(
    causal_model,
    old_data,
    new_data,
    target_node,
    invariant_nodes=None,
    num_samples=2000,
    difference_estimation_func=..., 
    independence_test=..., 
    conditional_independence_test=..., 
    mechanism_change_test_significance_level=0.05,
    mechanism_change_test_fdr_control_method="fdr_bh",
    auto_assignment_quality=None,
    return_additional_info=False,
    shapley_config=None,
    graph_factory=nx.DiGraph,
) -> dict or tuple

gcm.distribution_change_robust(
    causal_model,
    old_data,
    new_data,
    target_node,
    target_functional="mean",
    sample_weight=None,
    xfit=True,
    xfit_folds=5,
    train_size=0.5,
    calib_size=0.2,
    split_random_state=0,
    method="MR",
    regressor=gcm.ml.create_linear_regressor,
    classifier=gcm.ml.create_logistic_regression_classifier,
    calibrator=None,
    all_indep=False,
    crop=0.001,
    shapley_config=None,
) -> dict

gcm.unit_change(
    background_df,
    foreground_df,
    input_column_names,
    background_mechanism,
    foreground_mechanism=None,
    shapley_config=None,
) -> pandas.DataFrame
```

`distribution_change` fits old and new cloned mechanisms internally. If
`auto_assignment_quality` is `None`, the reference model must already have
mechanisms assigned so they can be cloned and re-fit. If a quality is supplied,
mechanisms are assigned separately on old and new data.

## Evaluation, refutation, and uncertainty APIs

Verified signatures:

```python
gcm.evaluate_causal_model(
    causal_model,
    data,
    max_num_samples=-1,
    evaluate_causal_mechanisms=True,
    compare_mechanism_baselines=False,
    evaluate_invertibility_assumptions=True,
    evaluate_overall_kl_divergence=True,
    evaluate_causal_structure=True,
    config=None,
) -> CausalModelEvaluationResult

gcm.refute_causal_structure(
    causal_graph,
    data,
    independence_test=gcm.kernel_based,
    conditional_independence_test=gcm.kernel_based,
    significance_level=0.05,
    fdr_control_method="fdr_bh",
) -> tuple

gcm.refute_invertible_model(
    causal_model,
    data,
    independence_test=gcm.kernel_based,
    significance_level=0.05,
    fdr_control_method=None,
) -> gcm.RejectionResult

gcm.independence_test(X, Y, conditioned_on=None, method="kernel", **kwargs)
gcm.confidence_intervals(estimation_func, confidence_level=0.95,
                         num_bootstrap_resamples=20,
                         bootstrap_results_summary_func=..., n_jobs=1)
gcm.bootstrap_sampling(function, *args, **kwargs)
gcm.fit_and_compute(function, causal_model, bootstrap_training_data,
                    bootstrap_data_subset_size_fraction=0.75,
                    auto_assign_quality=None, *args, **kwargs)
```

`gcm.model_evaluation.EvaluateCausalModelConfig` controls folds, baseline
models, independence tests, graph-falsification permutations, significance
levels, and `n_jobs`. Use it when default validation is too slow or too broad.

## Shapley and runtime controls

```python
gcm.shapley.ShapleyConfig(
    approximation_method=gcm.shapley.ShapleyApproximationMethods.AUTO,
    num_permutations=25,
    num_subset_samples=5000,
    min_percentage_change_threshold=0.05,
    n_jobs=None,
)
```

Approximation methods include `AUTO`, `EXACT`, `EXACT_FAST`,
`EARLY_STOPPING`, `PERMUTATION`, and `SUBSET_SAMPLING`. `AUTO` uses exact
computation for small player counts and approximation for larger ones. For
large graphs or many samples, set a smaller `num_permutations` or use
permutation/subset sampling intentionally.

Global controls:

```python
gcm.config.disable_progress_bars()
gcm.config.enable_progress_bars()
gcm.config.set_default_n_jobs(n_jobs)
```

Disable progress bars in scripts or tests that need clean output. Set `n_jobs`
only after considering nested parallelism: confidence intervals, Shapley
estimation, model evaluation, and some estimators can each parallelize.
