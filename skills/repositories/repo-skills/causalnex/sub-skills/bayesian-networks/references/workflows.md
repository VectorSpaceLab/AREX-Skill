# Bayesian Network Workflows

## 1. Fit a BN and query marginals

```python
import pandas as pd
from causalnex.network import BayesianNetwork
from causalnex.inference import InferenceEngine
from causalnex.structure import StructureModel

sm = StructureModel([("a", "c"), ("b", "c")])
data = pd.DataFrame({"a": [0, 0, 1, 1], "b": [0, 1, 0, 1], "c": [0, 0, 1, 1]})

bn = BayesianNetwork(sm).fit_node_states_and_cpds(data)
ie = InferenceEngine(bn)
print(ie.query({"a": 1})["c"])
```

Use `fit_node_states_and_cpds` when you have clean discrete data and want the shortest path to inference.

## 2. Predict and score a BN classifier

```python
from causalnex.network.sklearn import BayesianNetworkClassifier

edge_list = [("a", "c"), ("b", "c")]
clf = BayesianNetworkClassifier(edge_list, discretiser_alg={}, discretiser_kwargs={})
```

Use this wrapper when you want a sklearn-style classifier with discrete BN predictions. If your features are continuous, discretize them first.

## 3. Evaluate and plot

```python
from causalnex.evaluation import classification_report, roc_auc
from causalnex.plots import plot_structure

roc_points, auc = roc_auc(bn, data, "c")
report = classification_report(bn, data, "c")
viz = plot_structure(sm)
```

Use `roc_auc` for ranking quality and `classification_report` for per-class precision/recall/F1.

## 4. Intervene with do-calculus

```python
ie.do_intervention("a", 1)
print(ie.query()["c"])
ie.reset_do("a")
```

Use `do_intervention` when you want to reason about interventions rather than passive observations.

## 5. Run latent-variable EM

```python
from causalnex.estimator import EMSingleLatentVariable

em = EMSingleLatentVariable(sm=sm, data=data_with_nan_latent, lv_name="z", node_states=node_states)
em.run(n_runs=20, stopping_delta=0.01)
```

Use this path when a single latent variable is missing from part of the data and you want CPDs for the Markov blanket of that variable.

## Common workflow checks

- Build the DAG first, then fit node states, then fit CPDs, then query.
- Keep the data discrete for BN fitting and inference.
- If the model needs `MDLPSupervisedDiscretiserMethod`, install the optional discretizer package first.
- Prefer `InMemory` or tiny fixture data when you are only validating wiring.
