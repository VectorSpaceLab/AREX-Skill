---
name: graph-models
description: "Guides pomegranate BayesianNetwork and FactorGraph workflows,
  including categorical graph construction, structure learning, factor-graph
  inference, masked missing-value prediction, and graph troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# graph-models

## Use this sub-skill when

Use this sub-skill for directed categorical Bayesian networks, direct factor-graph inference, categorical structure learning, and discrete missing-value inference with `torch.masked.MaskedTensor`. It covers `BayesianNetwork`, `FactorGraph`, `Categorical`, `ConditionalCategorical`, and `JointCategorical` interactions.

## Start here

Typical imports:

```python
from pomegranate.distributions import Categorical, ConditionalCategorical, JointCategorical
from pomegranate.bayesian_network import BayesianNetwork
from pomegranate.factor_graph import FactorGraph
```

Read [references/api-reference.md](references/api-reference.md) for constructors, edge semantics, structure learning, and inference examples. Run [scripts/smoke_graph_models.py](scripts/smoke_graph_models.py) for a self-contained Monty Hall Bayesian-network check and a tiny factor-graph check.

## Core workflow

1. **Encode discrete variables as integer categories.** Bayesian networks and factor graphs are categorical/discrete in this implementation.
2. **Choose manual structure or learned structure.** For known graphs, pass distributions and edges. For data-driven categorical structure learning, pass `structure` or `algorithm='chow-liu'`/`'exact'` and call `fit`.
3. **Use the right distribution type.** Root Bayesian-network nodes use `Categorical`; child nodes with parents use `ConditionalCategorical`; factor-graph factors use `Categorical` or `JointCategorical`.
4. **Run inference with masks.** `predict`, `predict_proba`, and `predict_log_proba` infer missing variables from `torch.masked.MaskedTensor` where `mask=True` means observed.
5. **Interpret approximate inference carefully.** Factor-graph/sum-product inference is exact for tree-like structures and approximate for loopy graphs.

## Route elsewhere when

- The task is ordinary distribution fitting or scoring: read [../distributions/SKILL.md](../distributions/SKILL.md).
- The task is a supervised Bayes classifier, not a graphical model: read [../mixtures-and-classifiers/SKILL.md](../mixtures-and-classifiers/SKILL.md).
- The task is a Markov chain or HMM sequence model: read [../sequence-models/SKILL.md](../sequence-models/SKILL.md).

## Guardrails

- Edges are distribution-object pairs, not string node names.
- Do not use legacy `State`, `Node`, or `bake`; v1.x uses direct distribution objects.
- `BayesianNetwork` currently expects `Categorical` and `ConditionalCategorical` node distributions.
- `FactorGraph` is bipartite: edges connect marginals to factors, not factor-to-factor or marginal-to-marginal.
- `predict_proba` returns a list of tensors, one per variable, because variables can have different category counts.
- Read [references/troubleshooting.md](references/troubleshooting.md) when edges, masks, category shapes, structure learning, or convergence fail.
