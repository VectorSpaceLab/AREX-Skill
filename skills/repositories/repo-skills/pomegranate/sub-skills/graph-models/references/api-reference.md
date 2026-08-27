# Graph Models API Reference

This reference covers `BayesianNetwork` and `FactorGraph` in pomegranate v1.x.

## Constructors verified from the package

```python
BayesianNetwork(
    distributions=None,
    edges=None,
    structure=None,
    algorithm=None,
    include_parents=None,
    exclude_parents=None,
    max_parents=None,
    pseudocount=0.0,
    max_iter=20,
    tol=1e-6,
    inertia=0.0,
    frozen=False,
    check_data=True,
    verbose=False,
)

FactorGraph(
    factors=None,
    marginals=None,
    edges=None,
    max_iter=20,
    tol=1e-6,
    inertia=0.0,
    frozen=False,
    check_data=True,
    verbose=False,
)
```

## BayesianNetwork essentials

A Bayesian network models directed dependencies between categorical variables.

- `distributions`: `Categorical` root distributions and `ConditionalCategorical` child distributions.
- `edges`: list of `(parent_distribution, child_distribution)` pairs.
- `structure`: tuple of parent-index tuples, for example `((), (0,), (), (0, 2))`.
- `algorithm`: structure-learning algorithm; supported source paths include `'chow-liu'` and `'exact'` for categorical data.
- `include_parents`, `exclude_parents`, `max_parents`, and `pseudocount` constrain structure learning.

Common methods:

| Method | Use |
| --- | --- |
| `add_distribution(distribution)` / `add_distributions(distributions)` | Add categorical node distributions. |
| `add_edge(parent, child)` / `add_edges(edges)` | Add directed parent-child edges. |
| `fit(X, sample_weight=None)` | Fit parameters, and optionally learn structure when `algorithm` is set. |
| `log_probability(X)` | Score complete integer-coded examples. |
| `predict(masked_X)` | Fill missing discrete variables with most likely values. |
| `predict_proba(masked_X)` | Return per-variable posterior categorical distributions as a list of tensors. |
| `predict_log_proba(masked_X)` | Log posterior version of `predict_proba`. |
| `sample(n)` | Sample complete rows from the network. |

### Manual graph example

```python
import torch
from pomegranate.distributions import Categorical, ConditionalCategorical
from pomegranate.bayesian_network import BayesianNetwork

guest = Categorical([[1/3, 1/3, 1/3]])
prize = Categorical([[1/3, 1/3, 1/3]])
monty = ConditionalCategorical([[[
    [0.0, 0.5, 0.5], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0],
], [
    [0.0, 0.0, 1.0], [0.5, 0.0, 0.5], [1.0, 0.0, 0.0],
], [
    [0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.5, 0.5, 0.0],
]]])
model = BayesianNetwork([guest, prize, monty], [(guest, monty), (prize, monty)])

X = torch.tensor([[0, 1, -1]])
masked = torch.masked.MaskedTensor(X, mask=X >= 0)
completed = model.predict(masked)
```

### Structure learning example

```python
import torch
from pomegranate.bayesian_network import BayesianNetwork

X = torch.tensor([[0, 1, 0], [1, 1, 0], [1, 0, 1], [0, 0, 1]])
model = BayesianNetwork(algorithm="chow-liu", pseudocount=1.0)
model.fit(X)
print(model.structure)
```

Use `'exact'` only for small enough variable counts because exact Bayesian-network structure learning grows quickly with feature count.

## FactorGraph essentials

A `FactorGraph` is a bipartite graph between marginal distributions and factor distributions.

- Marginals must be initialized `Categorical` distributions.
- Factors must be `Categorical` or `JointCategorical` distributions.
- Each edge is `(marginal, factor)`.
- For multivariate factors, edge order should match the factor dimensions.

```python
import torch
from pomegranate.distributions import Categorical, JointCategorical
from pomegranate.factor_graph import FactorGraph

m1 = Categorical([[0.5, 0.5]])
m2 = Categorical([[0.5, 0.5]])
f = JointCategorical([[0.45, 0.05], [0.10, 0.40]])
graph = FactorGraph([f], [m1, m2], [(m1, f), (m2, f)])

X = torch.tensor([[0, -1]])
masked = torch.masked.MaskedTensor(X, mask=X >= 0)
completed = graph.predict(masked)
```

## Inference return shapes

`predict` returns a completed tensor with the same `(n, d)` shape as the input. `predict_proba` and `predict_log_proba` return a list, one tensor per variable, because each variable can have a different number of categories.
