# Distribution Catalog For Pyro 1.9.1

Use `import pyro.distributions as dist` for both PyTorch distributions and
Pyro-specific distributions. Pyro re-exports most `torch.distributions` classes
and adds Pyro behavior such as callable distributions, `.shape(sample_shape)`,
`.to_event()`, `.expand_by()`, `.mask()`, `score_parts()`, and validation helpers.

## Reliable Selection Process

1. **Choose the support first.** Is the random variable real, positive,
   integer-valued, categorical, simplex-valued, vector-valued, matrix-valued,
   sequential, or a constrained combinatorial object?
2. **Choose event rank second.** A scalar `Normal` has `event_shape == ()`; a
   vector `MultivariateNormal` or `Normal(...).to_event(1)` has event rank 1;
   HMM observations usually have event rank 2 because time is part of the event.
3. **Only then add batch/plate dimensions.** Parameter batch dimensions should
   broadcast to the independent dimensions represented by `pyro.plate`.
4. **Turn on validation while debugging.** `pyro.enable_validation(True)` catches
   invalid parameters, invalid observations, and many shape mistakes early.

## Common Distribution Choices

| Need | Prefer | Notes |
|---|---|---|
| Real scalar with light tails | `dist.Normal(loc, scale)` | Signature verified as `Normal(loc, scale, validate_args=None)`. `scale > 0`; scalar event. |
| Real scalar with heavy tails | `dist.StudentT`, `dist.Cauchy`, `dist.Stable`, `dist.SoftLaplace`, `dist.AsymmetricLaplace` | `Stable.log_prob()` is expensive; see stable gotchas below. |
| Positive scalar | `dist.LogNormal`, `dist.Gamma`, `dist.Exponential`, `dist.Weibull`, `dist.HalfNormal`, `dist.HalfCauchy`, `dist.Pareto`, `dist.InverseGamma` | Use `constraints.positive` for learnable scales/rates. |
| Unit interval / proportions | `dist.Beta`, `dist.Kumaraswamy`, `dist.ContinuousBernoulli`, `dist.AffineBeta` | Use logits/probs APIs carefully; validate ranges. |
| Binary data | `dist.Bernoulli(probs=...)` or `dist.Bernoulli(logits=...)` | Observations should be 0/1 tensors broadcastable to batch shape. |
| Category index | `dist.Categorical(probs=None, logits=None, validate_args=None)` | Values are integer class indices; event shape is scalar. |
| One-hot category | `dist.OneHotCategorical`, relaxed/straight-through variants | Event shape is `(num_categories,)`; log_prob removes that event dim. |
| Counts | `dist.Poisson`, `dist.NegativeBinomial`, `dist.Binomial`, `dist.BetaBinomial`, `dist.GammaPoisson` | Observations must be nonnegative integers within support. |
| Zero-inflated counts | `dist.ZeroInflatedPoisson`, `dist.ZeroInflatedNegativeBinomial` | Use exactly one of `gate` or `gate_logits`; scalar event. |
| Simplex probabilities | `dist.Dirichlet`, `dist.LogisticNormal` | Event shape is the simplex length. |
| Multinomial counts | `dist.Multinomial`, `dist.DirichletMultinomial` | Event shape is number of categories. |
| Independent vector of scalars | `dist.Normal(loc, scale).to_event(1)` | Often better than many scalar sites when dimensions are dependent or are one datum. |
| Correlated vector | `dist.MultivariateNormal`, `dist.LowRankMultivariateNormal`, `dist.MultivariateStudentT` | Prefer `scale_tril`/Cholesky when possible. |
| Correlation matrix prior | `dist.LKJCholesky(dim, concentration)` or `dist.LKJ(dim, concentration)` | `LKJCholesky` returns Cholesky factors; `LKJ` returns full correlation matrices. |
| Mixture model | `dist.MixtureSameFamily`, `dist.MaskedMixture`, `dist.MixtureOfDiagNormals`, `dist.GaussianScaleMixture` | Check component event shapes and mixture/component batch alignment. |
| HMM or linear dynamical sequence | `dist.DiscreteHMM`, `dist.GaussianHMM`, `dist.GammaGaussianHMM`, `dist.GaussianMRF`, `dist.LinearHMM` | Time is part of `event_shape`; see HMM section. |
| Matching / assignment | `dist.OneOneMatching`, `dist.OneTwoMatching` | No batching; exact algorithms are expensive; SciPy is needed for `.mode()`. |
| Deterministic value | `dist.Delta(v, log_density=0.0, event_dim=0)` | Common in guides or deterministic wrappers; set event_dim deliberately. |
| Missing-by-NaN Gaussian observations | `dist.NanMaskedNormal`, `dist.NanMaskedMultivariateNormal` | Useful when NaNs should be marginalized/ignored in Gaussian likelihoods. |

## Verified Constructor Signatures To Trust

These signatures were checked from the installed Pyro 1.9.1 package surface:

```python
dist.Normal(loc, scale, validate_args=None)
dist.Categorical(probs=None, logits=None, validate_args=None)
dist.ZeroInflatedPoisson(rate, *, gate=None, gate_logits=None, validate_args=None)
dist.ZeroInflatedNegativeBinomial(total_count, *, probs=None, logits=None,
                                  gate=None, gate_logits=None, validate_args=None)
dist.ZeroInflatedDistribution(base_dist, *, gate=None, gate_logits=None,
                              validate_args=None)
dist.DiscreteHMM(initial_logits, transition_logits, observation_dist,
                 validate_args=None, duration=None)
dist.GaussianHMM(initial_dist, transition_matrix, transition_dist,
                 observation_matrix, observation_dist,
                 validate_args=None, duration=None)
dist.Stable(stability, skew, scale=1.0, loc=0.0, coords="S0",
            validate_args=None)
dist.LKJ(dim, concentration=1.0, validate_args=None)
dist.OneOneMatching(logits, *, bp_iters=None, validate_args=None)
dist.OneTwoMatching(logits, *, bp_iters=None, validate_args=None)
```

## Pyro-Specific Families And Gotchas

### Zero-Inflated Counts

- `ZeroInflatedPoisson(rate, gate=...)` adds extra zeros to a Poisson count.
- `ZeroInflatedNegativeBinomial(total_count, probs=... or logits=..., gate=...)`
  adds extra zeros to an overdispersed count model.
- `gate` is the probability of the extra-zero Bernoulli. `gate_logits` is its
  logit. Specify exactly one.
- `gate`/`gate_logits` and the base distribution parameters broadcast to a common
  `batch_shape`; `event_shape` remains empty.
- Generic `ZeroInflatedDistribution(base_dist, ...)` requires an empty
  `base_dist.event_shape`; do not pass a multivariate base distribution unless
  you wrap a different model yourself.

Example:

```python
N = counts.shape[0]
rate = pyro.param("rate", torch.ones(N), constraint=dist.constraints.positive)
gate_logits = pyro.param("gate_logits", torch.zeros(N))
with pyro.plate("data", N, dim=-1):
    pyro.sample("obs", dist.ZeroInflatedPoisson(rate, gate_logits=gate_logits),
                obs=counts)
```

### HMM Distributions

Pyro's HMM distributions represent an entire observed sequence as one event.
Their `event_shape` includes time on the left.

- `DiscreteHMM` has discrete latent states and arbitrary observation
  distribution. It fuses the sequence into one distribution and can be much
  faster than manually enumerating one site per time step.
- `GaussianHMM` has Gaussian initial/process/observation factors and implements
  differentiable `log_prob()`, `rsample()`, `filter()`, `rsample_posterior()`,
  `prefix_condition()`, and `conjugate_update()`.
- `GammaGaussianHMM` is a Student-t-like scale-mixture Gaussian HMM.
- `GaussianMRF` scores temporal Gaussian Markov random fields.
- `LinearHMM` supports reparameterized sampling for broader transition and
  observation distributions, including `StudentT` or `Stable`, but
  `LinearHMM.log_prob()` is not implemented.
- `IndependentHMM(base_dist)` treats a batch of independent univariate HMMs as
  one multivariate HMM event.

HMM checks:

- Time belongs in the distribution's event shape, not in an enclosing `plate`.
- Homogeneous HMM parameters can have a time length of 1; pass `duration=T` when
  sampling or when you need a fixed event length.
- For `DiscreteHMM`, `observation_dist.batch_shape` must end in latent
  `state_dim`; it may also include time immediately before state.
- For `GaussianHMM`, `initial_dist.event_shape == (hidden_dim,)`,
  `transition_dist.event_shape == (hidden_dim,)`, and
  `observation_dist.event_shape == (obs_dim,)`.

### Stable Distributions

`dist.Stable(stability, skew, scale=1.0, loc=0.0, coords="S0")` is useful for
heavy-tailed noise and stable processes.

- `stability` is in `(0, 2]`; `skew` is in `[-1, 1]`; `scale > 0`.
- Default `coords="S0"` is Nolan's continuous parameterization and is usually
  better for inference geometry.
- `coords="S"` matches SciPy-style parameterization but is discontinuous at
  `stability == 1`; avoid it for gradient-based inference unless compatibility
  is more important than geometry.
- `Stable.has_rsample` is true, but `Stable.log_prob()` uses numerical
  integration and can be slow. For inference decisions, route to the SVI/MCMC
  and reparameterization sub-skills.
- `StableWithLogProb` is like `Stable` but prevents automatic/minimal stable
  reparameterization strategies from replacing it.
- Mean is undefined/NaN when `stability <= 1`; variance is infinite when
  `stability < 2`.

### LKJ And Correlation Matrices

- Prefer `dist.LKJCholesky(dim, concentration)` when building covariance
  matrices because `MultivariateNormal(..., scale_tril=...)` consumes Cholesky
  factors directly.
- `dist.LKJ(dim, concentration)` transforms a Cholesky LKJ sample into a full
  correlation matrix and has support `constraints.corr_matrix`.
- Deprecated `LKJCorrCholesky(d, eta)` exists for compatibility; prefer
  `LKJCholesky(dim, concentration)`.
- To build a covariance Cholesky from marginal scales and an LKJ factor:

```python
theta = pyro.sample("theta", dist.HalfCauchy(torch.ones(dim)))
L_corr = pyro.sample("L_corr", dist.LKJCholesky(dim, concentration=1.0))
L_cov = theta.sqrt().diag_embed() @ L_corr
pyro.sample("obs", dist.MultivariateNormal(torch.zeros(dim), scale_tril=L_cov), obs=y)
```

### Matching And Assignment Distributions

- `OneOneMatching(logits)` models a perfect matching from `N` sources to `N`
  destinations. `logits` must be a 2D `(N, N)` tensor; batching is not supported.
- `OneTwoMatching(logits)` models a matching from `2*N` sources to `N`
  destinations. `logits` must be 2D `(2*N, N)`; batching is not supported.
- With `bp_iters=None`, exact enumeration, `log_prob()`, and sampling are
  available but become expensive quickly.
- With `bp_iters=<positive int>`, `log_partition_function` and `log_prob()` use a
  Bethe/Sinkhorn-style approximation, but `.sample()` is not implemented.
- `.mode()` calls SciPy's `linear_sum_assignment`; if SciPy is unavailable, use
  exact enumeration only for tiny problems or install SciPy in the user's active
  environment.
- Sample values are integer tensors with event shape `(N,)` for one-one and
  `(2*N,)` for one-two; validation warns about invalid event shape, out-of-bounds
  values, or non-matching assignments.

### Mixtures

- `torch`/Pyro `MixtureSameFamily(mixture_distribution, component_distribution)`
  is the usual general-purpose mixture. The mixture distribution is normally a
  `Categorical`; component batch rightmost dim indexes mixture components.
- `MaskedMixture(mask, component0, component1)` chooses between two components by
  a boolean mask. Both components must have the same `event_shape`; the mask
  broadcasts to the resulting `batch_shape`.
- `MixtureOfDiagNormals(locs, coord_scale, component_logits)` is a pathwise
  differentiable mixture of diagonal multivariate normals. It supports
  multivariate event shape `(D,)`; unbatched parameters are `K x D`, `K x D`, and
  `K` respectively; batched mode adds batch dimensions to the left.
- `GaussianScaleMixture(coord_scale, component_logits, component_scale)` is a
  pathwise differentiable zero-mean diagonal Gaussian scale mixture. It does not
  support dimension `D = 1` and does not support batched parameters.

## Constraints And Transforms

Pyro extends `torch.distributions.constraints` and registers transforms for
Pyro-specific constraints. Useful extra constraints include:

| Constraint | Meaning |
|---|---|
| `dist.constraints.integer` | Any integer value. |
| `dist.constraints.ordered_vector` | Strictly increasing vector along the event dimension. |
| `dist.constraints.positive_ordered_vector` | Positive strictly increasing vector. |
| `dist.constraints.sphere` | Unit Euclidean sphere; event rank 1. |
| `dist.constraints.corr_matrix` | Full correlation matrix; event rank 2. |
| `dist.constraints.softplus_positive` | Positive values with a softplus transform. |
| `dist.constraints.softplus_lower_cholesky` | Lower-Cholesky-style positive diagonal using softplus. |
| `dist.constraints.unit_lower_cholesky` | Lower triangular matrix with ones on the diagonal. |

Typical patterns:

```python
import torch
import pyro
import pyro.distributions as dist
import pyro.distributions.constraints as constraints
import pyro.distributions.transforms as T
from torch.distributions import transform_to, biject_to

scale = pyro.param("scale", torch.tensor(1.0), constraint=constraints.positive)
ordered = transform_to(constraints.ordered_vector)(torch.randn(5))
positive_ordered = transform_to(constraints.positive_ordered_vector)(torch.randn(5))
```

For transformed distributions:

```python
base = dist.Normal(torch.zeros(2), torch.ones(2)).to_event(1)
flow = T.spline_coupling(2, count_bins=16)  # learnable TransformModule
q = dist.TransformedDistribution(base, [flow])
```

If a learnable `TransformModule` is reused across optimizer steps outside normal
Pyro model execution, call `transformed_dist.clear_cache()` after parameter
updates to avoid stale inverse/forward cache values.

## Optional Or Unverified Surfaces

The minimum verified runtime is CPU-focused. Treat these as optional unless the
active user environment proves otherwise:

- CUDA distribution tests and CUDA tensor/device behavior.
- SciPy-backed helper methods such as matching `.mode()` and distribution-testing
  utilities. Core `dist.Stable` sampling and `log_prob()` do not require SciPy,
  but external comparisons and some tests do.
- Funsor-backed HMM/enumeration workflows.
- Horovod, Lightning, Graphviz, torchvision, pandas, scanpy, zuko, and large
  tutorial/domain examples.
