# pgmpy Package Map

Read this when choosing the correct pgmpy module, optional extra, or compatibility path before a workflow.

## Installation and extras

| Need | Public install direction | Notes |
|---|---|---|
| Core modeling, discovery, estimation, inference, sampling, I/O, metrics | `pip install pgmpy` or `conda install conda-forge::pgmpy` | Supports Python 3.10 through 3.14 according to package metadata. |
| Local repo maintenance/testing | `pip install -e .[tests]` | Run focused pytest targets first. Do not install all extras unless the selected tests need them. |
| Functional Bayesian networks | `pip install "pgmpy[torch]"` | Requires `torch` and `pyro-ppl`; call `pgmpy.config.set_backend("torch")` before constructing `FunctionalBayesianNetwork`. CPU torch is enough for small functional-model checks; CUDA is optional unless the user explicitly needs GPU tensors. |
| LLM-assisted discovery | `pip install "pgmpy[optional]"` plus provider credentials/network | `ExpertInLoop` and `LLMPairwise` can require `litellm` and external provider configuration. Do not run provider calls without user approval. |
| Plotting | `pip install "pgmpy[optional]"` plus system graph dependencies when needed | `pygraphviz` may require system Graphviz headers/libraries; plotting is optional for core workflows. |
| Documentation/notebooks | `pip install "pgmpy[docs]"` | Docs/notebook execution is not needed for normal package use. |

## Canonical modules

| Workflow | Canonical imports | Use for | Important notes |
|---|---|---|---|
| Graph primitives | `pgmpy.base` (`DAG`, `PDAG`, `MAG`, `ADMG`, `UndirectedGraph`, `SimpleCausalModel`) | Graph-only causal and probabilistic structure, role annotations, graph algorithms | `DAG` extends `networkx.DiGraph`; `PDAG`/`MAG`/`ADMG` use typed-edge core graph semantics. Audit edge semantics when moving code between them. |
| Probabilistic models | `pgmpy.models` | `DiscreteBayesianNetwork`, `LinearGaussianBayesianNetwork`, `FunctionalBayesianNetwork`, `DynamicBayesianNetwork`, Markov/factor/junction/cluster graphs, `NaiveBayes` | `BayesianNetwork` and `MarkovNetwork` are deprecated aliases; prefer the explicit discrete classes. |
| CPDs and factors | `pgmpy.factors.discrete`, `pgmpy.factors.continuous`, `pgmpy.factors.hybrid` | `TabularCPD`, `DiscreteFactor`, `NoisyORCPD`, `LinearGaussianCPD`, `FunctionalCPD` | Match model family to CPD/factor family. Functional CPDs require torch/Pyro. |
| Structure/causal discovery | `pgmpy.causal_discovery` | PC, GES, HillClimbSearch, ChowLiu, TAN, TOPIC, SP, ANM, IGCI, expert/LLM-guided discovery | New discovery code belongs here, not in legacy `pgmpy.estimators`. |
| CI tests | `pgmpy.ci_tests` | `ChiSquare`, `GSq`, `PowerDivergence`, `FisherZ`, `Pearsonr`, `GCM`, multivariate tests, `get_ci_test` | Choose tests by data type and assumptions; many return structured `_CITestResult` objects. |
| Structure scores | `pgmpy.structure_score` | K2, BDeu, BDs, LogLikelihood, AIC/BIC and Gaussian/conditional-Gaussian variants, `get_scoring_method` | Match discrete/continuous/mixed data. Score names and estimator wrappers can fail when data type is wrong. |
| Parameter estimation | `pgmpy.parameter_estimator` | `DiscreteMLE`, `DiscreteBayesianEstimator`, `DiscreteEM`, `LinearGaussianMLE` | Preferred over legacy estimator imports for new code. Use `state_names`/priors for sparse discrete data. |
| Inference | `pgmpy.inference` | `VariableElimination`, `BeliefPropagation`, `ApproxInference`, `CausalInference`, `DBNInference` | Use observational inference for conditioning; route do-calculus and ATE to causal workflows. |
| Sampling | `pgmpy.sampling` | `BayesianModelSampling`, `GibbsSampling` | Model-level `simulate(...)` is often the easiest entry point. |
| Causal identification | `pgmpy.identification` | `Adjustment`, `Frontdoor` | Identify/validate effect strategies from role-aware causal graphs before estimation. |
| Causal prediction | `pgmpy.prediction` | `NaiveAdjustmentRegressor`, `DoubleMLRegressor`, `NaiveIVRegressor` | Uses graph roles to choose exposures/outcomes/adjustment/instrument columns. |
| Data/model registries | `pgmpy.datasets`, `pgmpy.example_models` | `list_datasets`, `load_dataset`, `list_models`, `load_model` | Some assets may require network/cache; use local bundled example models for no-network smoke checks. |
| I/O | `pgmpy.readwrite` and model `.save/.load` | BIF, XMLBIF, NET, UAI, XDSL, XBN, PomdpX readers/writers | Prefer model-level `save`/`load` when supported; use reader/writer classes for format-specific options. |
| Metrics | `pgmpy.metrics` | SHD, adjacency/orientation confusion matrices, correlation/Fisher/implied-CI/structure-score metrics | Align node sets and graph types before scoring. |

## Legacy compatibility notes

- `pgmpy.estimators` still exposes many older classes for backwards compatibility. For new code, use the canonical packages above.
- `pgmpy.estimators.ExpertKnowledge` and `pgmpy.causal_discovery.ExpertKnowledge` are incompatible classes. Use the `causal_discovery` version for new discovery workflows.
- When updating a base-class API, update the matching extension template and focused tests so future contributors do not copy stale scaffolds.

## Backend and optional-dependency boundaries

- The minimum verified scope for this skill is CPU core workflows. Do not claim torch/Pyro, LLM provider, plotting, or remote-data verification unless a target environment proves those extras.
- `pgmpy.config.set_backend("torch")` is global. Reset to NumPy after optional torch examples when the rest of a workflow expects NumPy arrays.
- A visible GPU does not imply pgmpy needs CUDA. Use CUDA only when the user explicitly asks for GPU tensor behavior or when their own optional torch workflow requires it.

## Fast route examples

- "Why does `FunctionalBayesianNetwork` raise about numpy backend?" → `modeling-and-factors` troubleshooting.
- "Which score for continuous causal discovery?" → `learning-structure-and-parameters` API and workflows.
- "What is P(Disease | symptoms)?" → `inference-sampling-and-simulation`.
- "What is P(Y | do(X=x)) or ATE?" → `causal-identification-and-effects`.
- "How do I load `bnlearn/alarm` or save BIF?" → `data-io-and-evaluation`.
- "Where should a new CI test live?" → `extending-pgmpy`.
