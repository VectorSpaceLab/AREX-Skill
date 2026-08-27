# Modeling Workflows

## Purpose

Use these recipes to build common pgmpy graph/model/factor objects without reopening pgmpy docs or notebooks. They distill the public quickstart and notebook patterns for discrete BNs, linear Gaussian BNs, CPDs, DBNs, functional BNs, and factor containers into small reusable workflows.

## 1. Decide: graph-only causal roles or full probabilistic model

Use a graph-only class when the user needs structure, roles, separation, or causal-graph manipulation but has no CPDs/probabilities.

```python
from pgmpy.base import DAG, SimpleCausalModel

# Direct graph with roles.
graph = DAG(
    [("U", "X"), ("X", "M"), ("M", "Y"), ("U", "Y")],
    roles={"exposures": "X", "outcomes": "Y"},
)
graph = graph.with_role("adjustment", {"U"})
assert graph.get_role("exposures") == ["X"]

# Standard causal template.
template = SimpleCausalModel(
    exposures="X", outcomes="Y", confounders="U", mediators="M", instruments="Z"
)
```

Choose a full model (`DiscreteBayesianNetwork`, `LinearGaussianBayesianNetwork`, etc.) when any downstream step needs CPDs, `check_model()`, probabilistic inference, simulation, parameter fitting, or save/load. You can still attach causal roles to directed model classes because they inherit role-aware graph behavior.

## 2. Build and validate a discrete Bayesian network

```python
from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import DiscreteBayesianNetwork

model = DiscreteBayesianNetwork([("Smoker", "Cancer"), ("Pollution", "Cancer")])

cpd_smoker = TabularCPD(
    variable="Smoker",
    variable_card=2,
    values=[[0.3], [0.7]],
    state_names={"Smoker": ["no", "yes"]},
)
cpd_pollution = TabularCPD(
    variable="Pollution",
    variable_card=3,
    values=[[0.70], [0.29], [0.01]],
    state_names={"Pollution": ["low", "medium", "high"]},
)
cpd_cancer = TabularCPD(
    variable="Cancer",
    variable_card=2,
    # shape: 2 child states x (2 Smoker states * 3 Pollution states) columns
    values=[
        [0.20, 0.15, 0.03, 0.05, 0.001, 0.02],
        [0.80, 0.85, 0.97, 0.95, 0.999, 0.98],
    ],
    evidence=["Smoker", "Pollution"],
    evidence_card=[2, 3],
    state_names={
        "Smoker": ["no", "yes"],
        "Pollution": ["low", "medium", "high"],
        "Cancer": ["yes", "no"],
    },
)

model.add_cpds(cpd_smoker, cpd_pollution, cpd_cancer)
assert model.check_model() is True
assert model.get_cpds("Cancer").get_values().shape == (2, 6)
```

After this point, route posterior query/simulation to `inference-sampling-and-simulation`, parameter fitting to `learning-structure-and-parameters`, and serialization to `data-io-and-evaluation`.

## 3. Recover from a CPD evidence/cardinality mismatch

When `TabularCPD` construction or `model.check_model()` fails, use this sequence:

```python
node = "Cancer"
cpd = model.get_cpds(node)
parents = list(model.get_parents(node))
stored_evidence_order = cpd.variables[1:]
stored_evidence_card = [int(card) for card in cpd.cardinality[1:]]
print({
    "parents_in_graph": parents,
    "cpd_evidence_order": stored_evidence_order,
    "cpd_evidence_card": stored_evidence_card,
    "cpd_2d_shape": cpd.get_values().shape,
})
```

Then fix the first failing invariant:

1. **CPD variable or evidence not in graph**: add the missing node/edge first or correct the CPD variable/evidence spelling.
2. **Parent/evidence mismatch**: recreate the CPD with evidence set equal to `model.get_parents(node)`. Order can differ for `check_model()`, but keep the values table aligned to the evidence order you pass.
3. **Wrong table width**: recompute `product(evidence_card)`. For evidence cards `[2, 3]`, the child CPD needs six columns.
4. **Wrong parent order but correct numbers**: use `cpd.reorder_parents(new_order=[...], inplace=False)` to inspect the reordered values, or recreate the CPD so the code is easier to audit.
5. **Columns not summing to 1**: normalize each column of `cpd.get_values()` or correct the probabilities, then recreate the CPD.
6. **State-name/cardinality mismatch**: make each parent CPD and every child CPD use the exact same `state_names[parent]` list and cardinality.

## 4. Build a linear Gaussian Bayesian network

Use a linear Gaussian model when variables are continuous and each child is normally distributed with a linear mean function of its parents.

```python
from pgmpy.factors.continuous import LinearGaussianCPD
from pgmpy.models import LinearGaussianBayesianNetwork

model = LinearGaussianBayesianNetwork([("Healthy", "Happy"), ("Wealthy", "Happy")])

cpd_healthy = LinearGaussianCPD("Healthy", beta=[4.0], std=2.0)
cpd_wealthy = LinearGaussianCPD("Wealthy", beta=[2.0], std=3.0)
cpd_happy = LinearGaussianCPD(
    "Happy",
    beta=[1.0, 3.0, 2.0],  # intercept + coefficients for Healthy, Wealthy
    std=5.0,
    evidence=["Healthy", "Wealthy"],
)

model.add_cpds(cpd_healthy, cpd_wealthy, cpd_happy)
assert len(cpd_happy.beta) == len(cpd_happy.evidence) + 1
assert model.check_model() is True
```

Do not use `TabularCPD` or `get_cardinality()` for continuous linear Gaussian variables. Fitting `LinearGaussianCPD`s from data belongs in `learning-structure-and-parameters`.

## 5. Build a dynamic Bayesian network skeleton and CPDs

Dynamic BN nodes are `(variable_name, time_slice)` tuples. Define the first slice and transition slice with tuple-valued CPDs.

```python
from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import DynamicBayesianNetwork as DBN

dbn = DBN()
dbn.add_edges_from([(("Weather", 0), ("Umbrella", 0)), (("Weather", 0), ("Weather", 1))])

cpd_weather_0 = TabularCPD(("Weather", 0), 2, [[0.7], [0.3]])
cpd_umbrella_0 = TabularCPD(
    ("Umbrella", 0),
    2,
    [[0.9, 0.2], [0.1, 0.8]],
    evidence=[("Weather", 0)],
    evidence_card=[2],
)
cpd_weather_1 = TabularCPD(
    ("Weather", 1),
    2,
    [[0.8, 0.4], [0.2, 0.6]],
    evidence=[("Weather", 0)],
    evidence_card=[2],
)

dbn.add_cpds(cpd_weather_0, cpd_umbrella_0, cpd_weather_1)
assert dbn.check_model() is True
```

If you expect mirrored intra-slice CPDs across slices, call `initialize_initial_state()` only after structure and required CPDs are present, then re-run `check_model()`. DBN structure learning and inference have separate owners.

## 6. Use factors, Markov networks, factor graphs, and junction trees

### Discrete factor and Markov network

```python
import numpy as np
from pgmpy.factors.discrete import DiscreteFactor
from pgmpy.models import DiscreteMarkovNetwork

model = DiscreteMarkovNetwork([("A", "B"), ("B", "C")])
phi_ab = DiscreteFactor(["A", "B"], [2, 2], [30, 5, 1, 10])
phi_bc = DiscreteFactor(["B", "C"], [2, 2], np.ones(4))
model.add_factors(phi_ab, phi_bc)
assert model.check_model() is True
```

### Factor graph

A `FactorGraph` must contain both variable nodes and factor nodes. Connect every factor node to all variables in its scope.

```python
from pgmpy.models import FactorGraph

fg = FactorGraph()
fg.add_nodes_from(["A", "B", "C", phi_ab, phi_bc])
fg.add_factors(phi_ab, phi_bc)
fg.add_edges_from([("A", phi_ab), ("B", phi_ab), ("B", phi_bc), ("C", phi_bc)])
assert fg.check_model() is True
```

### Cluster graph and junction tree

```python
from pgmpy.models import ClusterGraph, JunctionTree

cluster = ClusterGraph()
cluster.add_nodes_from([("A", "B"), ("B", "C")])
cluster.add_edge(("A", "B"), ("B", "C"))  # non-empty sepset: B
cluster.add_factors(phi_ab, phi_bc)
assert cluster.check_model() is True

jt = JunctionTree()
jt.add_nodes_from([("A", "B"), ("B", "C")])
jt.add_edge(("A", "B"), ("B", "C"))
jt.add_factors(phi_ab, phi_bc)
assert jt.check_model() is True
```

For junction trees, adding an edge that creates a cycle is invalid, and the tree must be fully connected.

## 7. Use NoisyOR for binary noisy-cause CPDs

`NoisyORCPD` is a compact binary-child/binary-parent CPD. It is useful when each parent independently activates the child with a given probability.

```python
from pgmpy.factors.discrete import NoisyORCPD, TabularCPD
from pgmpy.models import DiscreteBayesianNetwork

model = DiscreteBayesianNetwork([("AlarmCause", "Alarm")])
cpd_cause = TabularCPD(
    "AlarmCause", 2, [[0.2], [0.8]], state_names={"AlarmCause": ["True", "False"]}
)
cpd_alarm = NoisyORCPD("Alarm", prob_values=[0.8], evidence=["AlarmCause"])
model.add_cpds(cpd_cause, cpd_alarm)
assert model.check_model() is True
```

The generated state names for `NoisyORCPD` are `"True"` and `"False"`; keep parent CPDs aligned to those labels.

## 8. Optional functional Bayesian networks

Functional BNs are for arbitrary distributions and nonlinear parent relationships, but they are optional because they require torch and Pyro.

```python
import importlib.util

if importlib.util.find_spec("torch") and importlib.util.find_spec("pyro"):
    from pgmpy.global_vars import config
    config.set_backend("torch", device="cpu")

    import pyro.distributions as dist
    from pgmpy.factors.hybrid import FunctionalCPD
    from pgmpy.models import FunctionalBayesianNetwork

    model = FunctionalBayesianNetwork([("x1", "x2")])
    model.add_cpds(
        FunctionalCPD("x1", fn=lambda _: dist.Normal(0.0, 1.0)),
        FunctionalCPD("x2", fn=lambda p: dist.Normal(1.0 + 0.8 * p["x1"], 1.0), parents=["x1"]),
    )
    assert model.check_model() is True

    config.set_backend("numpy")
else:
    print("Install pgmpy[torch] and set pgmpy backend to torch before using FunctionalBayesianNetwork.")
```

Common functional CPD variants from pgmpy's examples include Gaussian chains, mixture models with Bernoulli/Normal nodes, vectorized CPDs for speed, SVI parameter learning, and MCMC inference. This sub-skill covers construction and validation only; learning and inference for functional BNs route to their sibling workflows.

## 9. Run the bundled smoke check

Use the local smoke helper when a task starts with an unknown environment:

```bash
python path/to/check_modeling_smoke.py --help
python path/to/check_modeling_smoke.py
```

A passing run proves that the installed package can import core modeling classes, build CPD tables, validate `check_model()`, and run a tiny exact query. It does not prove optional torch/Pyro functionality unless those packages are reported as importable.

## Distilled source-artifact coverage

| Source recipe family distilled | Runtime replacement in this sub-skill |
|---|---|
| Creating a discrete BN manually and inspecting CPDs | Sections 2-3 plus `scripts/check_modeling_smoke.py`. |
| Defining tabular CPDs and parent-cardinality tables | CPD shape rules in `model-and-factor-api.md` and Sections 2-3. |
| Creating a linear Gaussian BN and `LinearGaussianCPD`s | Section 4. |
| Dynamic BN construction with tuple time-slice nodes | Section 5. |
| Functional Bayesian network tutorial | Section 8 with optional torch/Pyro preflight; no optional dependency is required for core skill use. |
