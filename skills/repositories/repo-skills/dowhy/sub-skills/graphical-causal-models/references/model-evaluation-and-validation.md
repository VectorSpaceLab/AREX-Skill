# Model Evaluation and Validation

GCM validation can reject assumptions or reveal weak fits, but it cannot prove a
causal graph or mechanism is correct. Treat results as diagnostic evidence.

## Evaluation overview

Use `gcm.evaluate_causal_model` after assigning and fitting mechanisms when the
user needs a broad diagnostic summary:

```python
result = gcm.evaluate_causal_model(
    causal_model,
    data,
    max_num_samples=1000,
    evaluate_causal_mechanisms=True,
    compare_mechanism_baselines=False,
    evaluate_invertibility_assumptions=True,
    evaluate_overall_kl_divergence=True,
    evaluate_causal_structure=True,
)
print(result)
```

The result can include:

- causal-mechanism performance by node,
- invertible functional causal model assumption checks,
- average marginal KL divergence between generated and observed data,
- graph-structure falsification output.

Use `max_num_samples` to bound runtime. Set individual `evaluate_*` flags to
`False` when a task only needs one diagnostic family.

## Mechanism performance

Mechanism evaluation uses cross-validation. Typical reported metrics include:

- KL divergence for root-node generated versus observed distributions,
- MSE, normalized MSE, and R2 for numerical non-root nodes,
- F1 for categorical non-root nodes,
- CRPS for probabilistic calibration and predictive quality.

`compare_mechanism_baselines=True` compares assigned mechanisms against
baseline models. This can be useful for model selection but can be expensive
for large graphs or heavy predictors.

## Generated distribution fit

The generated-distribution diagnostic draws samples from the fitted GCM and
compares generated and observed marginals. It is useful for checking whether the
fitted model resembles the observed joint data, but it is not a guarantee of
correct causal direction. Markov-equivalent or otherwise observationally
similar graphs can generate similar observational distributions while implying
different interventions.

## Graph structure refutation

Use `gcm.refute_causal_structure` when the user wants an explicit graph/data
compatibility check:

```python
rejection, summary = gcm.refute_causal_structure(
    graph,
    data,
    significance_level=0.05,
    fdr_control_method="fdr_bh",
)
```

The function checks two families of implications:

- edge dependence: each node should depend on each direct parent;
- local Markov conditions: a node should be independent of non-descendants
  given its parents.

The return value is a `RejectionResult` plus a nested summary of p-values,
FDR-adjusted p-values, and success flags. A rejected graph indicates that the
chosen tests found contradictions. A non-rejected graph means the tests did not
find enough evidence to reject it; it does not confirm the graph.

## Invertible mechanism refutation

Use `gcm.refute_invertible_model` for fitted invertible structural models:

```python
rejection = gcm.refute_invertible_model(
    causal_model,
    data,
    significance_level=0.05,
    fdr_control_method=None,
)
```

This tests whether reconstructed noise is independent of mechanism inputs for
non-root nodes. It validates the invertible mechanism assumption, not the graph
structure. Run it before relying on point counterfactuals or anomaly
attribution when data size permits.

## Independence tests

Use `gcm.independence_test` for standalone checks:

```python
p = gcm.independence_test(X, Y, conditioned_on=Z, method="kernel")
```

Supported method names include:

- `"kernel"` for kernel-based tests,
- `"approx_kernel"` for approximate kernel tests,
- `"regression"` for regression-based tests,
- `"gcm"` for generalized covariance measure tests.

The null hypothesis is independence or conditional independence. A small
p-value rejects that null. A large p-value should be reported as "not rejected"
rather than "independent proven".

## Evaluation config

Use `gcm.model_evaluation.EvaluateCausalModelConfig` to control evaluation:

```python
config = gcm.model_evaluation.EvaluateCausalModelConfig(
    mechanism_evaluation_kfolds=3,
    max_num_permutations_falsify=20,
    falsify_graph_significance_level=0.1,
    n_jobs=1,
)
result = gcm.evaluate_causal_model(causal_model, data, config=config)
```

Important controls:

- `mechanism_evaluation_kfolds`: lower for faster mechanism diagnostics.
- `baseline_models_regression` and `baseline_models_classification`: customize
  baseline comparisons.
- `bootstrap_runs_invertible`: number of subsets for invertibility tests.
- `max_num_permutations_falsify`: lower for faster graph falsification.
- `independence_test_*` and `conditional_independence_test_*`: choose tests
  appropriate for sample size and data type.
- `n_jobs`: parallelism for supported evaluation pieces.

## Confidence intervals

Use confidence intervals for stochastic or approximate causal queries:

```python
median, intervals = gcm.confidence_intervals(
    lambda: gcm.arrow_strength(causal_model, target_node="Y"),
    num_bootstrap_resamples=20,
    n_jobs=1,
)
```

For GCM query functions whose first argument is a fitted model, use
`gcm.bootstrap_sampling` for query-only bootstrapping:

```python
median, intervals = gcm.confidence_intervals(
    gcm.bootstrap_sampling(gcm.arrow_strength, causal_model, target_node="Y"),
    num_bootstrap_resamples=20,
)
```

Use `gcm.fit_and_compute` when model-fitting uncertainty should be included:

```python
median, intervals = gcm.confidence_intervals(
    gcm.fit_and_compute(
        gcm.arrow_strength,
        causal_model,
        bootstrap_training_data=data,
        target_node="Y",
    ),
    num_bootstrap_resamples=20,
)
```

Trade-off:

- Query-only bootstrapping is cheaper and assumes the fitted model is fixed.
- Fit-and-compute bootstrapping is more honest about training-data uncertainty
  but can be much slower because the model is refitted repeatedly.

## Recommended validation sequence

For a new GCM analysis:

1. Validate graph/data column alignment and acyclicity.
2. Inspect mechanism assignments before fitting.
3. Fit the model and run a bounded evaluation summary.
4. If using counterfactuals or anomaly attribution, run invertible-model
   refutation when feasible.
5. If graph validity is central to the conclusion, run graph refutation with a
   runtime budget.
6. For approximate attribution or influence scores, use confidence intervals or
   repeat under multiple seeds/sample sizes.
7. Report non-rejection carefully and include model/graph assumptions in the
   final answer.
