# Sequence Models API Reference

This reference covers `MarkovChain`, `DenseHMM`, and `SparseHMM`.

## Constructor signatures verified from the package

```python
MarkovChain(distributions=None, k=None, n_categories=None, inertia=0.0, frozen=False, check_data=True)

DenseHMM(
    distributions=None,
    edges=None,
    starts=None,
    ends=None,
    init='random',
    max_iter=1000,
    tol=0.1,
    sample_length=None,
    return_sample_paths=False,
    inertia=0.0,
    frozen=False,
    check_data=True,
    random_state=None,
    verbose=False,
)

SparseHMM(
    distributions=None,
    edges=None,
    starts=None,
    ends=None,
    init='random',
    max_iter=1000,
    tol=0.1,
    sample_length=None,
    return_sample_paths=False,
    inertia=0.0,
    frozen=False,
    check_data=True,
    random_state=None,
    verbose=False,
)
```

## Sequence shapes

| Model | Typical data shape | Notes |
| --- | --- | --- |
| `MarkovChain` | `(n, length, d)` integer categories | Observed categorical sequence distribution. |
| `DenseHMM` / `SparseHMM` scoring | `(n, length, d)` | Emission distributions determine the feature dtype/range. |
| HMM fitting with variable lengths | list of 2D sequence tensors, or list of 3D grouped tensors | Pomegranate groups equal-length sequences internally for batched operations. |
| HMM priors | same leading shape as sequence data, final dimension `n_states` | Rows should be valid probabilities. |

## MarkovChain workflow

A `MarkovChain` models observed categorical sequences using an initial `Categorical` and one or more `ConditionalCategorical` distributions.

```python
import torch
from pomegranate.distributions import Categorical, ConditionalCategorical
from pomegranate.markov_chain import MarkovChain

initial = Categorical([[0.4, 0.6]])
transition = ConditionalCategorical([[[0.7, 0.3], [0.2, 0.8]]])
model = MarkovChain([initial, transition])
X = torch.tensor([[[0], [1], [1]], [[1], [0], [0]]])
logp = model.log_probability(X)
```

Use `MarkovChain(k=...)` when you want pomegranate to initialize the categorical/conditional distributions during fitting.

## DenseHMM workflow

Use a dense matrix when transitions are naturally dense or matrix operations should be efficient.

```python
import torch
from pomegranate.distributions import Exponential
from pomegranate.hmm import DenseHMM

states = [Exponential([1.0]), Exponential([2.5])]
edges = [[0.7, 0.2], [0.3, 0.6]]
starts = [0.6, 0.4]
ends = [0.1, 0.1]
model = DenseHMM(states, edges=edges, starts=starts, ends=ends)
X = torch.tensor([[[0.5], [1.0], [1.5]]], dtype=torch.float32)
logp = model.log_probability(X)
states = model.predict(X)
```

## SparseHMM workflow

Use sparse edges when most state-to-state transitions are impossible.

```python
from pomegranate.distributions import Exponential
from pomegranate.hmm import SparseHMM

s1 = Exponential([1.0])
s2 = Exponential([2.5])
edges = [[s1, s1, 0.7], [s1, s2, 0.2], [s2, s1, 0.3], [s2, s2, 0.6]]
model = SparseHMM([s1, s2], edges=edges, starts=[0.6, 0.4], ends=[0.1, 0.1])
```

Sparse edge entries are distribution objects, not state names or numeric indices.

## HMM inference methods

| Method | Use |
| --- | --- |
| `log_probability(X, priors=None)` | Sequence log likelihood. |
| `probability(X, priors=None)` | Sequence probability. |
| `predict(X, priors=None)` | Most likely state per timestep by posterior marginals. |
| `predict_proba(X, priors=None)` | Posterior state probabilities per timestep. |
| `predict_log_proba(X, priors=None)` | Log posterior state probabilities. |
| `viterbi(X=None, emissions=None, priors=None)` | Best path dynamic-programming decode. |
| `fit(X, sample_weight=None, priors=None)` | Baum-Welch/EM fitting, including variable-length handling. |
| `summarize(X, sample_weight=None, emissions=None, priors=None)` | Accumulate sufficient statistics for a batch. |
| `from_summaries()` | Update transitions/emissions from accumulated statistics. |

## Prior-guided sequence learning

HMM priors should be probabilities over hidden states at each timestep. Use one-hot rows for hard labels and soft rows for prior beliefs. Priors must be shaped consistently with the sequence batch and number of states.

```python
priors = torch.full((1, 3, 2), 0.5)
priors[0, 0] = torch.tensor([1.0, 0.0])
post = model.predict_proba(X, priors=priors)
```
