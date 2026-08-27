# Workflows

Use these recipes as operating patterns. They assume the caller already has a clean pandas `DataFrame` whose column names are pgmpy variable names.

## 1. Choose method by data and objective

| Situation | Prefer | Avoid |
|---|---|---|
| Discrete/categorical structure | `PC(ci_test="chi_square" or "g_sq")`, `HillClimbSearch(scoring_method="bic-d"/"k2"/"bdeu")`, `GES(scoring_method="bic-d")` | Continuous CI tests or Gaussian scores on categorical states. |
| Continuous approximately Gaussian structure | `PC(ci_test="pearsonr" or "fisher_z")`, `HillClimbSearch(scoring_method="bic-g")`, `GES(scoring_method="bic-g")` | Discrete scores such as `"bic-d"` unless variables have been discretized intentionally. |
| Mixed discrete/continuous structure | Mixed CI tests such as `"pillai"`; conditional-Gaussian scores such as `"bic-cg"` | Blind auto-detection without checking dtypes and category encoding. |
| Tree-structured BN | `ChowLiu(root_node=...)` | Full DAG search when a tree constraint is known. |
| Tree-augmented Naive Bayes | `TAN(class_node=..., root_node=...)` | Unconstrained search when classifier structure is required. |
| Exactly two continuous variables | `ANM` or `IGCI` depending on assumptions | Multivariate discovery classes; bivariate methods require exactly two columns. |
| Need domain constraints | `ExpertKnowledge` with required/forbidden edges, temporal order, root nodes, or search space | Post-hoc edge edits that invalidate fitted attributes or CPDs. |
| Need CPDs after learned structure | Convert/instantiate the right model family and call `model.fit(data, estimator=...)` | Expecting discovery estimators to learn parameters. |

## 2. Discrete discovery then CPD fitting

```python
from pgmpy.causal_discovery import HillClimbSearch
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.parameter_estimator import DiscreteBayesianEstimator

structure = HillClimbSearch(
    scoring_method="bic-d",
    max_indegree=3,
    return_type="dag",
    show_progress=False,
).fit(data)

model = DiscreteBayesianNetwork(structure.causal_graph_.edges())
model.add_nodes_from(data.columns)

state_names = {col: sorted(data[col].dropna().unique()) for col in data.columns}
model.fit(
    data,
    estimator=DiscreteBayesianEstimator(
        state_names=state_names,
        prior_type="BDeu",
        equivalent_sample_size=5,
    ),
)
model.check_model()
```

Why this pattern:

- `return_type="dag"` avoids trying to parameterize a partially directed result.
- `state_names` protects small datasets where a valid state is absent in the sample.
- Bayesian smoothing avoids zero-probability CPD columns in sparse data.

## 3. Constraint-based discovery with expert knowledge

```python
from pgmpy.causal_discovery import ExpertKnowledge, PC

expert = ExpertKnowledge(
    forbidden_edges=[("outcome", "exposure")],
    required_edges=[("exposure", "outcome")],
    temporal_order=[["exposure", "baseline"], ["outcome"]],
)

pc = PC(
    variant="stable",
    ci_test="chi_square",
    return_type="dag",
    significance_level=0.01,
    max_cond_vars=3,
    expert_knowledge=expert,
    show_progress=False,
)
pc.fit(data)
learned_dag = pc.causal_graph_
```

Use the same `ExpertKnowledge` object style with `HillClimbSearch`. If constraints make the problem impossible, fix the knowledge rather than silently dropping the constraint.

## 4. Continuous Gaussian structure and parameters

```python
from pgmpy.causal_discovery import HillClimbSearch
from pgmpy.models import LinearGaussianBayesianNetwork
from pgmpy.parameter_estimator import LinearGaussianMLE

search = HillClimbSearch(
    scoring_method="bic-g",
    return_type="dag",
    max_indegree=3,
    show_progress=False,
).fit(continuous_data)

model = LinearGaussianBayesianNetwork(search.causal_graph_.edges())
model.add_nodes_from(continuous_data.columns)
model.fit(continuous_data, estimator=LinearGaussianMLE(std_estimator="unbiased"))
```

Use `PC(ci_test="pearsonr" or "fisher_z")` when the task emphasizes conditional independencies rather than score optimization.

## 5. Mixed-data structure learning

```python
from pgmpy.causal_discovery import PC, HillClimbSearch

pc = PC(ci_test="pillai", return_type="pdag", show_progress=False).fit(mixed_data)
hc = HillClimbSearch(scoring_method="bic-cg", return_type="dag", show_progress=False).fit(mixed_data)
```

Mixed scores help learn structure, but parameterization still depends on the target model family. If the user needs CPDs, decide whether the final model is discrete, linear-Gaussian, or a custom/hybrid model before fitting parameters.

## 6. Chow-Liu and TAN structures

```python
from pgmpy.causal_discovery import ChowLiu, TAN

# Tree over all variables.
tree = ChowLiu(root_node="root", show_progress=False).fit(discrete_data)

# Tree-augmented Naive Bayes: class node points to every feature.
tan = TAN(class_node="class", root_node="feature_1", show_progress=False).fit(classifier_data)
```

Both estimators return a directed `DAG` in `causal_graph_`. To fit CPDs, create a `DiscreteBayesianNetwork` from those edges and use a discrete parameter estimator.

## 7. Bivariate direction: ANM and IGCI

```python
from pgmpy.causal_discovery import ANM, IGCI

anm = ANM(scoring_method="independence").fit(two_column_continuous_data)
igci = IGCI(scoring_method="slope", ref_measure="uniform").fit(two_column_continuous_data)
```

Use `ANM` when additive noise and nonlinearity/non-Gaussian noise are plausible. Use `IGCI` when the relationship is close to deterministic, invertible, and monotonic. Both raise if there are not exactly two continuous, non-constant variables or the direction is tied/ambiguous.

## 8. EM for latent or missing discrete data

```python
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.parameter_estimator import DiscreteEM

model = DiscreteBayesianNetwork([("A", "H"), ("H", "B")], latents={"H"})

em = DiscreteEM(
    latent_card={"H": 2},
    init_cpds="uniform",
    max_iter=50,
    seed=7,
    show_progress=False,
)
model.fit(observed_data, estimator=em)
```

Operational notes:

- Fully missing columns that correspond to model nodes can be treated as latent variables.
- Rows with partially missing observed columns are dropped by EM preprocessing; warn the user if this changes the sample size materially.
- Set `latent_card` and `init_cpds` for reproducibility.
- The M-step estimator must support weighted data; `DiscreteMLE()` and `DiscreteBayesianEstimator(...)` are valid choices.

## 9. Optional expert/LLM-in-the-loop orientation

```python
from pgmpy.causal_discovery import ExpertInLoop, LLMPairwise

pairwise = LLMPairwise(
    descriptions={"smoke": "whether a person smokes", "cancer": "cancer diagnosis"},
    llm_model="provider/model-name",
    llm_kwargs={"temperature": 0},
)

est = ExpertInLoop(pairwise_estimator=pairwise, show_progress=False)
est.fit(data)
```

This workflow is optional and was not verified in the minimum environment. It requires the optional LiteLLM dependency plus provider credentials or a reachable local provider endpoint. For deterministic offline work, supply a custom pairwise estimator instead of `LLMPairwise`.

## 10. Translate legacy examples

| Legacy pattern | Canonical replacement |
|---|---|
| `from pgmpy.estimators import PC; PC(data).estimate(...)` | `from pgmpy.causal_discovery import PC; PC(...).fit(data).causal_graph_` |
| `HillClimbSearch(data).estimate(scoring_method=...)` | `pgmpy.causal_discovery.HillClimbSearch(scoring_method=...).fit(data)` |
| `TreeSearch(...).estimate(estimator_type="chow-liu")` | `pgmpy.causal_discovery.ChowLiu(...).fit(data)` |
| `TreeSearch(...).estimate(estimator_type="tan", class_node=...)` | `pgmpy.causal_discovery.TAN(class_node=...).fit(data)` |
| `MaximumLikelihoodEstimator` for BN CPDs | `pgmpy.parameter_estimator.DiscreteMLE()` |
| `BayesianEstimator` for BN CPDs | `pgmpy.parameter_estimator.DiscreteBayesianEstimator(...)` |
| `ExpectationMaximization` for discrete latent CPDs | `pgmpy.parameter_estimator.DiscreteEM(...)` |

Some legacy classes still exist for compatibility or specialized workflows, but default to canonical imports unless the user explicitly asks for legacy parity.
