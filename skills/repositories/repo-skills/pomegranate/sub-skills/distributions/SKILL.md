---
name: distributions
description: "Guides pomegranate distribution workflows, including Normal,
  Categorical, ConditionalCategorical, IndependentComponents, probability
  scoring, sampling, fitting, weights, missing values, and distribution
  composition."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# distributions

## Use this sub-skill when

Use this sub-skill for pomegranate's base distribution family and distribution-level workflows: instantiate a distribution from parameters, fit parameters from samples, compute probabilities, sample new values, use sample weights, freeze or update parameters, combine heterogeneous feature distributions, or prepare distributions as components for mixtures, classifiers, HMMs, Markov chains, Bayesian networks, or factor graphs.

## Start here

Typical imports:

```python
from pomegranate.distributions import Normal, Categorical, Exponential
from pomegranate.distributions import ConditionalCategorical, JointCategorical
from pomegranate.distributions import IndependentComponents, ZeroInflated
```

Read [references/api-reference.md](references/api-reference.md) for constructor signatures, shape expectations, and class selection. Run [scripts/smoke_distributions.py](scripts/smoke_distributions.py) after installing the package if you need a tiny API sanity check.

## Core workflow

1. **Choose the distribution by data type.** Continuous positive data often uses `Exponential`, `Gamma`, or `LogNormal`; general continuous data often uses `Normal`; binary/count/categorical data uses `Bernoulli`, `Poisson`, `Categorical`, `ConditionalCategorical`, or `JointCategorical`.
2. **Initialize directly or learn from data.** Pass parameters when known, or instantiate without parameters and call `fit(X)`.
3. **Keep shapes explicit.** Use `(n, d)` for ordinary distributions. Categorical graph/sequence distributions use integer-coded categories.
4. **Score with log probabilities first.** Prefer `log_probability(X)` for numerical stability; use `probability(X)` only when actual probabilities are needed.
5. **Use `summarize` + `from_summaries` for chunks.** This is the out-of-core path shared with larger pomegranate models.
6. **Compose heterogeneous columns with `IndependentComponents`.** Use one initialized or trainable univariate distribution per feature when a single multivariate family is inappropriate.

## Cross-cutting behavior

- Read [../../references/feature-guide.md](../../references/feature-guide.md) for `torch.masked.MaskedTensor`, sample weights, inertia, frozen parameters, GPU, mixed precision, out-of-core updates, and `torch.compile`.
- Read [references/troubleshooting.md](references/troubleshooting.md) when input ranges, shapes, category indexing, covariance settings, masked tensors, or `ZeroInflated` behavior is confusing.
- To use distributions inside composite models, route to [../mixtures-and-classifiers/SKILL.md](../mixtures-and-classifiers/SKILL.md), [../graph-models/SKILL.md](../graph-models/SKILL.md), or [../sequence-models/SKILL.md](../sequence-models/SKILL.md) after creating the component distributions.

## Important guardrails

- Pomegranate distributions represent the probability of full examples, not independent per-feature log probabilities unless the chosen distribution's semantics say so.
- Do not use pre-v1 names such as `NormalDistribution`; use `Normal` and the current distribution class names.
- Do not assume all distribution wrappers implement every base method. `ZeroInflated` is useful for fitting excess-zero data but should be checked for the exact scoring/sampling method a task needs.
- Keep model/device and tensor/device aligned before using CUDA.
