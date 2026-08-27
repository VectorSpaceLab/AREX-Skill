# Discovery and Learning API Reference

This reference summarizes the pgmpy APIs owned by `learning-structure-and-parameters`. It is intentionally self-contained; use it instead of relying on old notebook imports or source checkout paths.

## Canonical packages

| Task | Prefer | Avoid by default | Notes |
|---|---|---|---|
| Causal/structure discovery | `pgmpy.causal_discovery` | Legacy discovery classes in `pgmpy.estimators` | Canonical discovery estimators use `fit(...)`, then `causal_graph_` and `adjacency_matrix_`. |
| CI tests | `pgmpy.ci_tests` | Legacy CI helpers | Use `get_ci_test(...)` for name/auto detection or instantiate a test class directly. |
| Structure scores | `pgmpy.structure_score` | Legacy score classes in `pgmpy.estimators` | Use `get_scoring_method(...)` or pass a configured score instance. |
| BN parameter estimation | `pgmpy.parameter_estimator` | Legacy `MaximumLikelihoodEstimator`, `BayesianEstimator`, `ExpectationMaximization` | New estimators are initialized objects passed to `model.fit(...)` or fit directly. |
| Marginal/factor-graph fitting | Usually reroute | Legacy marginal estimators | This is not the canonical BN CPD-estimation path; coordinate with modeling/factors guidance. |

## Unified discovery pattern

```python
from pgmpy.causal_discovery import PC

est = PC(ci_test="chi_square", return_type="dag", show_progress=False)
est.fit(data)
learned_graph = est.causal_graph_
adjacency = est.adjacency_matrix_
```

`fit(...)` returns the fitted estimator object, not a standalone graph. Do not expect legacy `estimate(...)` examples to match this API.

## Discovery estimators

| Estimator | Typical data | Use when | Key knobs | Result attributes |
|---|---|---|---|---|
| `PC` | Discrete, continuous, or mixed when paired with a suitable CI test | Constraint-based discovery and CPDAG/DAG recovery from conditional independencies | `variant`, `ci_test`, `return_type`, `significance_level`, `max_cond_vars`, `orient_rule`, `expert_knowledge`, `n_jobs` | `causal_graph_`, `adjacency_matrix_`, `skeleton_`, `separating_sets_` |
| `HillClimbSearch` | Discrete, continuous, or mixed with a matching structure score | Greedy score-based search with optional start graph, max indegree, and constraints | `scoring_method`, `start_dag`, `tabu_length`, `max_indegree`, `expert_knowledge`, `return_type`, `epsilon`, `max_iter` | `causal_graph_`, `adjacency_matrix_` |
| `GES` | Discrete, continuous, or mixed with a matching structure score | Greedy equivalence search returning a PDAG or DAG | `scoring_method`, `return_type`, `min_improvement` | `causal_graph_`, `adjacency_matrix_` |
| `TOPIC` | Score-compatible tabular data | Score-based topological-order discovery | `scoring_method`, `return_type`, `min_improvement` | `causal_graph_`, `adjacency_matrix_`, `topological_order_` |
| `SP` | Small variable sets with a suitable CI test | Sparsest permutation search; factorial in variable count unless bounded | `ci_test`, `significance_level`, `max_iter`, `return_type`, `seed` | `causal_graph_`, `adjacency_matrix_`, `optimal_permutations_` |
| `ChowLiu` | Usually discrete/categorical | Tree-structured Bayesian network over all variables | `root_node`, `edge_weights_fn`, `n_jobs` | `causal_graph_`, `adjacency_matrix_` |
| `TAN` | Usually discrete/categorical classifier data | Tree-augmented Naive Bayes structure with a class node | `class_node`, `root_node`, `edge_weights_fn`, `n_jobs` | `causal_graph_`, `adjacency_matrix_` |
| `ANM` | Exactly two continuous variables | Bivariate nonlinear additive-noise direction | `regressor`, `scoring_method` | `causal_graph_`, `adjacency_matrix_`, `forward_score_`, `backward_score_` |
| `IGCI` | Exactly two continuous variables | Bivariate near-deterministic/invertible direction | `scoring_method`, `ref_measure` | `causal_graph_`, `adjacency_matrix_`, `forward_score_`, `backward_score_` |
| `ExpertInLoop` | Tabular data plus a pairwise orientation source | Iterative CI-based edge addition/removal with expert or pairwise orientation | `pairwise_estimator`, `ci_test`, `expert_knowledge`, thresholds | `causal_graph_`, `adjacency_matrix_` |
| `LLMPairwise` | Exactly two named variables; values are only an interface carrier | Optional LLM-based pair orientation for `ExpertInLoop` or direct pairwise use | `descriptions`, `llm_model`, `llm_kwargs`, `use_cache` | `causal_graph_`, `adjacency_matrix_`, LLM prompt/response attrs |

`ExpertInLoop` always needs a `pairwise_estimator` for orientations not fixed by expert knowledge. `LLMPairwise` needs the optional LiteLLM dependency and provider credentials or a local provider endpoint.

## Expert knowledge

Use `pgmpy.causal_discovery.ExpertKnowledge`, not the legacy `pgmpy.estimators.ExpertKnowledge`, with canonical discovery estimators.

```python
from pgmpy.causal_discovery import ExpertKnowledge, HillClimbSearch

expert = ExpertKnowledge(
    required_edges=[("cause", "effect")],
    forbidden_edges=[("effect", "cause")],
    temporal_order=[["cause", "baseline"], ["effect"]],
    root_nodes={"cause"},
)
est = HillClimbSearch(scoring_method="bic-d", expert_knowledge=expert, return_type="dag")
est.fit(data)
```

Important fitted behavior:

- `fit(data)` resolves `required_edges_`, `forbidden_edges_`, `temporal_ordering_`, and `search_space_`.
- `temporal_order` must cover the data variables exactly when data is provided.
- `root_nodes` forbid incoming edges into those nodes.
- `search_space="marginally_dependent"` screens candidate edges with a marginal CI test and needs data.
- Required edges that create cycles can make score-based discovery fail; fix the constraints before retrying.

## CI test selection

Use `get_ci_test(test=..., data=...)` to resolve names or defaults. CI test objects are callable as `test(X, Y, Z, significance_level=...)` and expose raw `statistic_`, `p_value_`, and `effect_size_` after a run.

| Data/use | Names and classes | Notes |
|---|---|---|
| Discrete/categorical | `"chi_square"` / `ChiSquare`, `"g_sq"` / `GSq`, `"log_likelihood"`, `"modified_log_likelihood"`, `"power_divergence"` | Use with categorical state data. `PowerDivergence` has `lambda_` variants such as Cressie-Read. |
| Continuous | `"pearsonr"` / `Pearsonr`, `"fisher_z"` / `FisherZ`, `"gcm"` / `GCM`, `"pearsonr_equivalence"` | Use numeric columns. `Pearsonr` is the continuous auto default. |
| Mixed/discrete-continuous | `"pillai"` / `PillaiTrace`, `"generalized_cov"`, `"hotelling_lawley"`, `"roys_largest_root"`, `"wilks_lambda"` | Use when discrete and continuous variables are both present; some tests accept an sklearn-style residual estimator. |
| Deterministic independencies | `"independence_match"` / `IndependenceMatch` | Use when passing an `Independencies` object rather than data-backed testing. |

If `ci_test=None`, pgmpy auto-detects a default from data type: discrete -> chi-square, continuous -> Pearson correlation, mixed -> Pillai trace.

## Structure score selection

Use `get_scoring_method(scoring_method, data)` for auto detection or string lookup. To tune score-specific arguments, pass an initialized score object such as `BDeu(data, equivalent_sample_size=20)`.

| Data type | Score strings/classes | Default when `scoring_method=None` |
|---|---|---|
| Discrete | `"k2"` / `K2`, `"bdeu"` / `BDeu`, `"bds"` / `BDs`, `"ll-d"` / `LogLikelihood`, `"aic-d"` / `AIC`, `"bic-d"` / `BIC` | `"bic-d"` |
| Continuous/Gaussian | `"ll-g"` / `LogLikelihoodGauss`, `"aic-g"` / `AICGauss`, `"bic-g"` / `BICGauss` | `"bic-g"` |
| Mixed conditional-Gaussian | `"ll-cg"` / `LogLikelihoodCondGauss`, `"aic-cg"` / `AICCondGauss`, `"bic-cg"` / `BICCondGauss` | `"bic-cg"` |

Score objects cache local scores by default. Increase or disable `max_cache_size` only when repeated local-score calls are thrashing memory or cache.

## Parameter estimators

| Estimator | Model family | Use when | Key arguments | Output |
|---|---|---|---|---|
| `DiscreteMLE` | `DiscreteBayesianNetwork` or `DAG` promoted to a discrete BN | Complete discrete data and straightforward maximum-likelihood CPDs | `state_names`, `n_jobs`; supports `sample_weight` | `parameters_` list of `TabularCPD` |
| `DiscreteBayesianEstimator` | `DiscreteBayesianNetwork` or `DAG` promoted to a discrete BN | Sparse discrete data, smoothing, or priors | `prior_type` (`"BDeu"`, `"K2"`, `"dirichlet"`), `equivalent_sample_size`, `pseudo_counts`, `state_names`, `n_jobs`; supports `sample_weight` | `parameters_` list of `TabularCPD` |
| `DiscreteEM` | Discrete BN with latent variables or fully missing latent columns | Latent variables or incomplete observations needing EM | `latent_card`, `m_step_estimator`, `max_iter`, `atol`, `batch_size`, `seed`, `init_cpds`, `show_progress` | `parameters_` list of `TabularCPD` including latent variables |
| `LinearGaussianMLE` | `LinearGaussianBayesianNetwork` | Continuous linear-Gaussian CPDs | `std_estimator` (`"unbiased"` or `"mle"`) | `parameters_` list of `LinearGaussianCPD` |

Recommended entry point:

```python
model.fit(data, estimator=DiscreteBayesianEstimator(prior_type="BDeu", equivalent_sample_size=5))
```

Direct estimator use is also valid when you need to inspect `parameters_` before adding CPDs:

```python
estimator = DiscreteMLE(state_names=state_names)
estimator.fit(model, data)
model.add_cpds(*estimator.parameters_)
```
