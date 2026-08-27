---
name: learning-structure-and-parameters
description: "Guide pgmpy causal discovery, CI tests, structure scores, expert
  knowledge, and parameter estimation from data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Learning Structure and Parameters

Use this sub-skill when the task is to learn graph structure or fit parameters from tabular data with pgmpy's canonical learning APIs. It covers causal/structure discovery, conditional-independence tests, structure scores, expert-knowledge constraints, and parameter estimators.

## Own and reroute

Own these workflows:

- Structure and causal discovery through `pgmpy.causal_discovery`: `PC`, `HillClimbSearch`, `GES`, `ChowLiu`, `TAN`, `SP`, `TOPIC`, `ANM`, `IGCI`, `ExpertKnowledge`, and optional expert/LLM-in-the-loop estimators.
- Conditional-independence test selection through `pgmpy.ci_tests`.
- Score-based structure learning through `pgmpy.structure_score`.
- Parameter fitting through `pgmpy.parameter_estimator`: `DiscreteMLE`, `DiscreteBayesianEstimator`, `DiscreteEM`, and `LinearGaussianMLE`.

Reroute these requests:

- Manual graph/model object construction, CPD authoring, factor objects, and model validation details -> `modeling-and-factors`.
- Dataset registries, benchmark loading, metrics, and graph-evaluation reports -> `data-io-and-evaluation`.
- Causal identification, adjustment/frontdoor sets, treatment-effect estimation, and `do`-effect prediction -> `causal-identification-and-effects`.

## Canonical stance

Prefer the newer canonical packages over legacy `pgmpy.estimators` examples:

1. Instantiate a discovery estimator from `pgmpy.causal_discovery`.
2. Call `fit(data)`.
3. Read learned results from `causal_graph_` and `adjacency_matrix_`.
4. If parameters are needed, build or reuse the appropriate model family and call `model.fit(data, estimator=...)` with an initialized estimator from `pgmpy.parameter_estimator`.

Only use legacy `pgmpy.estimators` when the requested class has no canonical replacement or when reproducing an old API-specific workflow is explicitly required.

## First actions for an agent

1. Identify the data type and target model family before choosing a method: discrete, continuous/Gaussian, mixed conditional-Gaussian, tree/classifier, or bivariate direction.
2. Read [references/discovery-and-learning-api.md](references/discovery-and-learning-api.md) for imports, score names, CI-test names, and estimator contracts.
3. Read [references/workflows.md](references/workflows.md) for recipes that combine discovery, expert knowledge, and parameter fitting.
4. If the user reports errors or confusing output, read [references/troubleshooting.md](references/troubleshooting.md) before changing code.
5. For a no-network local smoke check, run [scripts/learn_structure_smoke.py](scripts/learn_structure_smoke.py) with the Python environment where pgmpy is installed.

## Minimal working pattern

```python
from pgmpy.causal_discovery import HillClimbSearch
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.parameter_estimator import DiscreteBayesianEstimator

est = HillClimbSearch(scoring_method="bic-d", return_type="dag", show_progress=False).fit(data)
model = DiscreteBayesianNetwork(est.causal_graph_.edges())
model.add_nodes_from(data.columns)
model.fit(data, estimator=DiscreteBayesianEstimator(prior_type="BDeu", equivalent_sample_size=5))
```

Keep `show_progress=False` in automated smoke tests and small examples unless the user specifically wants progress bars.
