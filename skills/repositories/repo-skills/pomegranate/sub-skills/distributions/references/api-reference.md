# Distribution API Reference

All distributions use PyTorch tensors internally and accept common pomegranate options such as `inertia`, `frozen`, and `check_data` unless noted. Use 2D data `(n, d)` for fitting and scoring.

## Common methods

| Method | Use |
| --- | --- |
| `fit(X, sample_weight=None)` | Learn parameters in one call. |
| `summarize(X, sample_weight=None)` | Accumulate sufficient statistics for a batch. |
| `from_summaries()` | Update parameters from accumulated statistics and reset caches. |
| `log_probability(X)` | Return one log probability per example. Prefer this over `probability`. |
| `probability(X)` | Return `exp(log_probability(X))` when implemented by the base class. |
| `sample(n)` | Generate `n` examples for distributions that implement sampling. |
| `freeze()` / `unfreeze()` | Toggle model-level parameter updates. |

## Constructor signatures verified from the package

| Class | Signature | Notes |
| --- | --- | --- |
| `Normal` | `Normal(means=None, covs=None, covariance_type='full', min_cov=None, inertia=0.0, frozen=False, check_data=True)` | `covariance_type` may be `'full'`, `'diag'`, or `'sphere'`; `covs` are variances/covariances, not standard deviations. |
| `Exponential` | `Exponential(scales=None, inertia=0.0, frozen=False, check_data=True)` | Positive continuous features. |
| `Gamma` | `Gamma(shapes=None, rates=None, inertia=0.0, tol=0.0001, max_iter=20, frozen=False, check_data=True)` | Positive continuous features; fitting is iterative. |
| `LogNormal` | `LogNormal(means=None, covs=None, covariance_type='full', min_cov=None, inertia=0.0, frozen=False, check_data=True)` | Log-normal family derived from normal-style parameters. |
| `HalfNormal` | `HalfNormal(covs=None, covariance_type='full', min_cov=None, inertia=0.0, frozen=False, check_data=True)` | Nonnegative half-normal style distribution. |
| `StudentT` | `StudentT(dofs, means=None, covs=None, covariance_type='diag', min_cov=None, inertia=0.0, frozen=False, check_data=True)` | Requires degrees of freedom. |
| `Bernoulli` | `Bernoulli(probs=None, inertia=0.0, frozen=False, check_data=True)` | Binary values; inputs should contain 0/1. |
| `Categorical` | `Categorical(probs=None, n_categories=None, pseudocount=0.0, inertia=0.0, frozen=False, check_data=True)` | Integer-coded categories; `probs` use an outer feature dimension such as `[[0.2, 0.8]]`. |
| `ConditionalCategorical` | `ConditionalCategorical(probs=None, n_categories=None, pseudocount=0, inertia=0.0, frozen=False, check_data=True)` | Conditional probability table for parent-conditioned discrete variables. |
| `JointCategorical` | `JointCategorical(probs=None, n_categories=None, pseudocount=0, inertia=0.0, frozen=False, check_data=True)` | Joint probability table used in factor graphs. |
| `DiracDelta` | `DiracDelta(alphas=None, inertia=0.0, frozen=False, check_data=True)` | Degenerate distribution with fixed values. |
| `Poisson` | `Poisson(lambdas=None, inertia=0.0, frozen=False, check_data=True)` | Count data. |
| `Uniform` | `Uniform(mins=None, maxs=None, inertia=0.0, frozen=False, check_data=True)` | Independent intervals with lower and upper bounds. |
| `IndependentComponents` | `IndependentComponents(distributions, check_data=False)` | One distribution per feature; at least two component distributions are required. |
| `ZeroInflated` | `ZeroInflated(distribution, priors=None, max_iter=10, tol=0.1, inertia=0.0, frozen=False, check_data=False, verbose=False)` | Wrapper for excess-zero data. Check exact method availability before treating it like a full scoring distribution. |

## Recipes

### Fit and score a diagonal normal

```python
import torch
from pomegranate.distributions import Normal

X = torch.tensor([[0.0, 1.0], [0.5, 1.2], [1.0, 2.0]], dtype=torch.float32)
model = Normal(covariance_type="diag").fit(X)
logp = model.log_probability(X)
```

### Use categorical probabilities

```python
import torch
from pomegranate.distributions import Categorical

model = Categorical([[0.1, 0.7, 0.2]])
logp = model.log_probability(torch.tensor([[1], [2], [0]]))
```

### Compose heterogeneous independent features

```python
import torch
from pomegranate.distributions import Exponential, IndependentComponents, Normal

model = IndependentComponents([
    Normal([0.0], [1.0], covariance_type="diag"),
    Exponential([2.0]),
])
logp = model.log_probability(torch.tensor([[0.0, 1.0], [1.0, 3.0]]))
```

### Chunked updates

```python
model = Normal(covariance_type="diag")
for X_chunk in chunks:
    model.summarize(X_chunk)
model.from_summaries()
```

## Selection notes

- Prefer `Normal(covariance_type='diag')` when features are conditionally independent and you want stable small-data fitting.
- Use `Normal(covariance_type='full')` only when enough data exists to estimate a covariance matrix.
- Use `ConditionalCategorical` for a child variable conditioned on one or more discrete parent variables, especially in Bayesian networks and Markov chains.
- Use `JointCategorical` for factor-graph factors rather than ordinary categorical marginals.
- Use `IndependentComponents` when each feature has a different distribution family.
