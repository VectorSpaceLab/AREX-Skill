# Model and Factor API Reference

## Purpose

Read this when selecting a pgmpy graph/model/factor class, checking constructor arguments, or debugging CPD/factor validation. The facts here were distilled from pgmpy's public guides/API tables, source, tests, and installed-package signature inspection.

## Class selection map

| Need | Use | Construction notes | Validation notes |
|---|---|---|---|
| Directed graph structure with causal roles but no probabilities | `pgmpy.base.DAG` | `DAG(ebunch=[("X", "Y")], roles={"exposures": "X", "outcomes": "Y"})` or call `with_role`. | Use graph algorithms/role checks. Use a full BN only when CPDs/probabilities are needed. |
| Partially directed equivalence class | `pgmpy.base.PDAG` | Edge tuples are `(u, v, edge_type)` with `"->"`, `"<-"`, or `"--"`. | `directed_edges`, `undirected_edges`, Meek-rule utilities, acyclic-extension checks. |
| Latent-confounding mixed graph | `pgmpy.base.ADMG` | Supports directed `"->"`/`"<-"` and bidirected `"<>"` edges. | Directed part must remain acyclic. Bidirected edges encode latent common causes. |
| Maximal ancestral graph | `pgmpy.base.MAG` | Supports directed, bidirected, and undirected edges. | Use for latent/selection-aware causal graph reasoning; `is_maximal()` and visibility utilities are MAG-specific. |
| Causal role template | `pgmpy.base.SimpleCausalModel` | `SimpleCausalModel(exposures="X", outcomes="Y", confounders="Z", mediators="M", instruments="I")`. | Automatically creates standard role-based edges. Use `DAG` directly when the structure is not the standard template. |
| Discrete Bayesian network | `pgmpy.models.DiscreteBayesianNetwork` + `TabularCPD` | Directed acyclic graph; add one `TabularCPD` per node. | `check_model()` requires every node CPD, parent/evidence agreement, state names for CPD variables, valid columns, and parent-child cardinality/state-name consistency. |
| Linear Gaussian Bayesian network | `pgmpy.models.LinearGaussianBayesianNetwork` + `LinearGaussianCPD` | Directed acyclic graph over continuous variables; each CPD has intercept plus one coefficient per parent. | `check_model()` verifies each CPD's evidence set equals graph parents. Cardinality is not defined. |
| Arbitrary torch/Pyro functional model | `pgmpy.models.FunctionalBayesianNetwork` + `FunctionalCPD` | Requires `pgmpy[torch]`, `config.set_backend("torch")`, and CPD callables returning Pyro distributions. | Optional surface in this skill: minimum environment did not install torch/Pyro. `check_model()` checks CPD parent sets. |
| Dynamic Bayesian network | `pgmpy.models.DynamicBayesianNetwork` + `TabularCPD` | Nodes/CPD variables/evidence are time-slice tuples such as `("W", 0)`, `("W", 1)`. Define first two slices and transition edges. | `check_model()` checks parent/evidence agreement and column sums; `initialize_initial_state()` can fill mirrored slice CPDs when structure/CPDs permit. |
| Undirected Markov model | `pgmpy.models.DiscreteMarkovNetwork` + `DiscreteFactor` | Add undirected edges and factors over node scopes. | Factors must cover variables, have consistent cardinalities, and factor scopes must be compatible with graph edges. |
| Factor graph | `pgmpy.models.FactorGraph` + `DiscreteFactor` nodes | Bipartite graph: variable nodes connect to factor nodes. Add factors to the graph and connect them to all variables in their scope. | `check_model()` enforces bipartite variable/factor structure, one factor per factor node, full factor coverage, and cardinality consistency. |
| Cluster graph / junction tree | `ClusterGraph`, `JunctionTree` + clique factors | Nodes are tuples/lists/sets representing cliques. Edges require non-empty sepsets. Junction trees must stay acyclic and connected. | Each clique needs a factor with exactly that scope; cardinalities must agree across factors. Junction trees also check connectedness. |
| Simple Markov chain | `pgmpy.models.MarkovChain` | Initialize variables/cardinalities, add transition models, optionally set start state with `pgmpy.factors.discrete.State`. | Transition matrices/dicts must match variable cardinality and row probabilities. Use the inference/sampling sub-skill for sampling workflows. |

## Graph roles and typed edges

Directed `DAG` and probabilistic directed models expose role helpers inherited from pgmpy's role mixin:

```python
from pgmpy.base import DAG

G = DAG([("U", "X"), ("X", "Y"), ("U", "Y")], roles={"exposures": "X", "outcomes": "Y"})
G = G.with_role("adjustment", {"U"})
assert G.get_role("exposures") == ["X"]
assert set(G.get_role("adjustment")) == {"U"}
```

Role properties include `latents`, `observed`, `exposures`, and `outcomes`. `with_role(role, variables, inplace=False)` returns a copy unless `inplace=True`; it raises if a variable is not in the graph. `is_valid_causal_structure()` requires at least one exposure and one outcome.

`PDAG`, `ADMG`, and `MAG` are built on a typed-edge multigraph. Use `get_edges(data=True)`, `get_edge_type(u, v)`, and `has_edge(u, v, edge_type)` rather than assuming NetworkX `DiGraph` semantics. Supported edge-type families:

| Graph | Supported edge types | Meaning |
|---|---|---|
| `PDAG` | `"->"`, `"<-"`, `"--"` | Directed and undirected edges in a CPDAG/PDAG. |
| `ADMG` | `"->"`, `"<-"`, `"<>"` | Directed plus bidirected latent-confounding edges. |
| `MAG` | `"->"`, `"<-"`, `"<>"`, `"--"` | Directed, bidirected, and selection-bias undirected edges. |

## CPDs and factors

| Object | Constructor | Shape/order contract | Common methods |
|---|---|---|---|
| `TabularCPD` | `TabularCPD(variable, variable_card, values, evidence=None, evidence_card=None, state_names={})` | `values` must be 2-D. No parents: `(variable_card, 1)`. With parents: `(variable_card, product(evidence_card))`. `cpd.variables == [variable] + evidence`; `cpd.cardinality == [variable_card] + evidence_card`. | `get_values()`, `to_factor()`, `reorder_parents(new_order)`, `get_random`, `get_uniform`, `to_dataframe`, `get_value`. |
| `LinearGaussianCPD` | `LinearGaussianCPD(variable, beta, std, evidence=[])` | `beta[0]` is the intercept; `beta[1:]` align to `evidence` in order. Use `len(beta) == len(evidence) + 1`. | `copy()`, `get_random(...)`; model APIs handle add/get/check. |
| `FunctionalCPD` | `FunctionalCPD(variable, fn, parents=[], vectorized=False)` | `fn` is callable and returns a Pyro distribution. `parents` names must match graph parents. Requires `pyro-ppl`; practical model use also requires torch backend. | `sample(n_samples, parent_sample)`. Optional, not core-minimum verified. |
| `DiscreteFactor` | `DiscreteFactor(variables, cardinality, values, state_names={})` | `len(cardinality) == len(variables)` and `len(values) == product(cardinality)`. Values are reshaped to the cardinality tuple. | `scope()`, `get_cardinality`, `get_value`, `set_value`, factor algebra. |
| `NoisyORCPD` | `NoisyORCPD(variable, prob_values, evidence)` | Binary child and binary parents. One activation probability per evidence variable; values must be in `[0, 1]`. | Inherits `TabularCPD` behavior and can be added to a discrete BN. |
| `JointProbabilityDistribution` | `JointProbabilityDistribution(variables, cardinality, values)` | Full joint table over discrete variables. | Factor-like `get_value`, `sample`, and independence utilities. |

### Tabular CPD column order

For `TabularCPD("Y", 2, values, evidence=["A", "B"], evidence_card=[2, 3])`, `values` must have shape `(2, 6)`. Columns enumerate parent-state combinations in the evidence order, with the last evidence variable varying fastest:

| Column | `A` | `B` |
|---:|---:|---:|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 2 | 0 | 2 |
| 3 | 1 | 0 |
| 4 | 1 | 1 |
| 5 | 1 | 2 |

Every column must sum to 1 for a discrete BN to pass `check_model()`. Internally `cpd.values` is reshaped to `(variable_card, *evidence_card)`, while `cpd.get_values()` returns the 2-D conditional table. Use `cpd.variables[1:]` to see the stored evidence order. `cpd.get_evidence()` returns pgmpy's internal evidence order and can appear reversed from construction order, so do not use it to reconstruct a user-facing values table unless you verify the order.

### State names and cardinalities

- If `state_names` is omitted, pgmpy assigns numeric states `0..cardinality-1` for every variable in a factor/CPD.
- If `state_names` is provided for a BN CPD, include every variable in that CPD: the child plus all evidence variables.
- Parent CPDs and child CPDs must use the same cardinality and the same state-name list for shared variables.
- Evidence values used later in inference must match the state-name convention. If a variable has string state names, pass the string label rather than numeric `0`/`1`.

## Model validation semantics

| Model | `check_model()` validates | Does not validate |
|---|---|---|
| `DiscreteBayesianNetwork` | One CPD per node; CPD variables in graph; CPD evidence set equals parents; CPD state names cover variables; CPD columns sum to 1; parent-child cardinality and state names match. | Whether the structure was learned well; downstream inference correctness if evidence labels are wrong. |
| `LinearGaussianBayesianNetwork` | CPD evidence sets match graph parents. | Discrete cardinality; broad statistical fit quality; all possible beta-length misuse. Check coefficient length yourself. |
| `FunctionalBayesianNetwork` | CPD parents match graph parents. | Torch/Pyro installation beyond constructor import checks; quality or runtime stability of arbitrary CPD functions. |
| `DynamicBayesianNetwork` | Time-slice CPDs are `TabularCPD`, variables exist, parent/evidence sets match, and conditional probabilities sum to 1. | DBN structure learning; long simulation/inference behavior. |
| `DiscreteMarkovNetwork` | Factors exist for variables, cardinality consistency, and factor scopes agree with graph adjacency. | Normalization unless explicitly needed. |
| `FactorGraph` | Bipartite factor/variable node structure, factors associated with factor nodes, full variable coverage, cardinality consistency. | Message-passing convergence or inference behavior. |
| `ClusterGraph` / `JunctionTree` | Clique factors, variable coverage, cardinality consistency; junction tree connectedness. | Whether cliques came from the optimal triangulation. |

## Backend configuration

The default backend is NumPy. The global config object supports:

```python
from pgmpy.global_vars import config

config.get_backend()             # "numpy" or "torch"
config.set_backend("numpy")      # reset to default, no device
config.set_backend("torch", device="cpu")  # requires torch installed
config.set_dtype(None)            # backend default dtype
config.set_show_progress(False)   # useful for automation
```

`config.set_device(...)` is valid only when the backend is torch. `FunctionalBayesianNetwork` raises when the backend is NumPy, and `FunctionalCPD` raises when `pyro-ppl` is missing. Install `pgmpy[torch]` only when functional models are required; it was intentionally omitted from the minimum core environment.
