# Workflow Map

This page gives the quickest path into the four user-facing CausalNex workflows. Read the matching sub-skill for deeper API notes and the bundled smoke script when you want a quick end-to-end check.

## 1. Learn causal structure

Read `sub-skills/structure-learning/SKILL.md` when you want to infer a DAG from data or wrap NOTEARS in sklearn-style estimators.

```python
import pandas as pd
from causalnex.structure.notears import from_pandas

X = pd.DataFrame({"a": [0, 1, 0, 1], "b": [1, 1, 0, 0], "c": [0, 1, 1, 0]})
sm = from_pandas(X, w_threshold=0.05)
```

Use `from_numpy` for arrays, `from_pandas_dynamic` for lagged time series, and `DAGClassifier` / `DAGRegressor` when you want a sklearn-style wrapper around the learned graph.

## 2. Fit and query a Bayesian network

Read `sub-skills/bayesian-networks/SKILL.md` when the graph is already known and you want CPDs, inference, interventions, metrics, or latent-variable EM.

```python
from causalnex.network import BayesianNetwork
from causalnex.inference import InferenceEngine

bn = BayesianNetwork(sm).fit_node_states_and_cpds(data)
ie = InferenceEngine(bn)
print(ie.query({"a": 1})["c"])
```

Use `roc_auc` and `classification_report` for evaluation, `plot_structure` for visualization, and `BayesianNetworkClassifier` for a sklearn-style BN classifier.

## 3. Discretize numeric features

Read `sub-skills/discretization/SKILL.md` when continuous data must be bucketed before Bayesian-network fitting or when you want supervised splitters.

```python
import numpy as np
from causalnex.discretiser import Discretiser

d = Discretiser(method="quantile", num_buckets=4)
print(d.fit_transform(np.array([1, 2, 3, 4, 5, 6])))
```

Use `DecisionTreeSupervisedDiscretiserMethod` for sklearn tree splits and `MDLPSupervisedDiscretiserMethod` when the optional MDLP dependency is available.

## 4. Generate synthetic causal data

Read `sub-skills/synthetic-data/SKILL.md` when you need random DAGs, tabular samples, dynamic time-series samples, or feature-mapping helpers.

```python
from causalnex.structure.data_generators import generate_structure, sem_generator

sm = generate_structure(num_nodes=4, degree=2)
df = sem_generator(sm, schema={0: "binary", 1: "continuous"}, n_samples=100)
```

Use `generate_structure_dynamic` and `generate_dataframe_dynamic` for dynamic Bayesian-network data, `DynamicDataTransformer` for lagged matrices, and `VariableFeatureMapper` for categorical expansion.

## Choosing between workflows

- If you are learning edges from data, start in structure learning.
- If you already have a DAG and need CPDs or causal queries, start in Bayesian networks.
- If a BN classifier or supervised discretizer fails, read discretization first, then return to Bayesian networks.
- If you need benchmarks, fixtures, or dynamic toy data, start in synthetic data and feed the result into the other sub-skills.
