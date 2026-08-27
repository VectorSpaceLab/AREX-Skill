# Distribution API reference

This reference covers NumPyro distribution objects as standalone objects. A distribution object can be sampled, scored with `log_prob`, transformed, expanded, masked, or wrapped with `Independent`/`to_event`. It does not cover model sample-site effects; route those to `../modeling-primitives/`.

## Imports used in examples

```python
from jax import random
import jax.numpy as jnp
import numpyro.distributions as dist
from numpyro.distributions import constraints, transforms
from numpyro.distributions.distribution import validation_enabled
```

## Constructor patterns

All constructors below accept array-like JAX/NumPy/scalar parameters. Most accept `validate_args: bool | None = None`; set `validate_args=True` while debugging invalid parameters.

### Common continuous distributions

| Distribution | Typical constructor | Support and notes |
|---|---|---|
| `dist.Normal` | `Normal(loc=0.0, scale=1.0, validate_args=None)` | Real scalar events. `scale` must be positive. Vector `loc`/`scale` creates batch dimensions unless wrapped by `to_event`/`Independent`. |
| `dist.Beta` | `Beta(concentration1, concentration0, validate_args=None)` | Unit interval values. Both concentration parameters must be positive. |
| `dist.Dirichlet` | `Dirichlet(concentration, validate_args=None)` | Simplex event. Last dimension is the simplex event dimension. |
| `dist.Gamma` | `Gamma(concentration, rate, validate_args=None)` | Positive values. Use for rate/scale-like positive latent values. |
| `dist.Exponential` | `Exponential(rate, validate_args=None)` | Positive values. |
| `dist.HalfNormal` | `HalfNormal(scale=1.0, validate_args=None)` | Positive values; equivalent in spirit to folding a zero-mean normal. |
| `dist.HalfCauchy` | `HalfCauchy(scale=1.0, validate_args=None)` | Positive heavy-tailed scale prior. |
| `dist.StudentT` | `StudentT(df, loc=0.0, scale=1.0, validate_args=None)` | Real scalar events; heavier tails than Normal. |
| `dist.MultivariateNormal` | `MultivariateNormal(loc=0.0, covariance_matrix=None, precision_matrix=None, scale_tril=None, validate_args=None)` | Vector event. Provide exactly one covariance representation. `scale_tril` must be lower triangular with positive diagonal. |
| `dist.LowRankMultivariateNormal` | `LowRankMultivariateNormal(loc, cov_factor, cov_diag, validate_args=None)` | Vector event with low-rank plus diagonal covariance. |
| `dist.GaussianRandomWalk` | `GaussianRandomWalk(scale=1.0, num_steps=1, validate_args=None)` | Vector time-series event of length `num_steps`. |
| `dist.TruncatedNormal` | `TruncatedNormal(loc=0.0, scale=1.0, low=None, high=None, validate_args=None)` | Interval-truncated normal. Give at least one finite bound for truncation. |

### Common discrete distributions

| Distribution | Typical constructor | Support and notes |
|---|---|---|
| `dist.Bernoulli` | `Bernoulli(probs=None, logits=None, validate_args=None)` | Boolean/0-1 outcomes. Pass exactly one of `probs` or `logits`. |
| `dist.Binomial` | `Binomial(total_count=1, probs=None, logits=None, validate_args=None)` | Integer counts from `0` to `total_count`. Pass exactly one of `probs` or `logits`. |
| `dist.Categorical` | `Categorical(probs=None, logits=None, validate_args=None)` | Integer category index. Last parameter dimension enumerates categories. |
| `dist.Multinomial` | `Multinomial(total_count=1, probs=None, logits=None, validate_args=None)` | Count vector event. Last parameter dimension enumerates categories. |
| `dist.Poisson` | `Poisson(rate=1.0, validate_args=None)` | Nonnegative integer counts. `rate` must be positive. |
| `dist.NegativeBinomial` | `NegativeBinomial(total_count, probs=None, logits=None, validate_args=None)` | Nonnegative integer counts with overdispersion. |
| `dist.DiscreteUniform` | `DiscreteUniform(low, high, validate_args=None)` | Integer support from `low` through `high`, inclusive. |
| `dist.OrderedLogistic` | `OrderedLogistic(predictor, cutpoints, validate_args=None)` | Ordinal category index. `cutpoints` should be ordered. |

### Point masses, mixtures, and zero inflation

| Pattern | Constructor | Notes |
|---|---|---|
| Point mass | `dist.Delta(v=0.0, log_density=0.0, event_dim=0, validate_args=None)` | `event_dim` says how many rightmost dimensions of `v` are part of one event. `log_prob(value)` is `log_density` where `value == v`, else `-inf`. |
| Same-family mixture | `dist.MixtureSameFamily(mixing_distribution, component_distribution, validate_args=None)` | `mixing_distribution` is a `Categorical`; the last batch dimension of `component_distribution` must equal the number of mixture components. |
| General mixture | `dist.MixtureGeneral(mixing_distribution, component_distributions, support=None, validate_args=None)` | Components are a list. List length must equal mixture size; event shapes must match. If supports differ by type, provide a common `support`. |
| Factory | `dist.Mixture(mixing_distribution, component_distributions, validate_args=None)` | Returns `MixtureSameFamily` for one vectorized distribution, or `MixtureGeneral` for a list. |
| Generic zero inflation | `dist.ZeroInflatedDistribution(base_dist, gate=None, gate_logits=None, validate_args=None)` | `base_dist` must be discrete with scalar events. Pass exactly one of `gate` or `gate_logits`. `gate` is the structural extra-zero probability. |
| Poisson zero inflation | `dist.ZeroInflatedPoisson(gate, rate=1.0, validate_args=None)` | Parameter order is `gate` then `rate`. If `gate=0`, this is Poisson; if `gate=1`, this is `Delta(0)`. |

Example mixture:

```python
mix = dist.Categorical(probs=jnp.array([0.25, 0.75]))
components = dist.Normal(loc=jnp.array([-1.0, 1.0]), scale=jnp.array([0.5, 2.0]))
gmm = dist.MixtureSameFamily(mix, components)
value = jnp.array(0.0)
assert jnp.isfinite(gmm.log_prob(value))
```

Example zero-inflation:

```python
zip_dist = dist.ZeroInflatedPoisson(gate=0.2, rate=3.0)
counts = jnp.arange(5)
assert jnp.all(jnp.isfinite(zip_dist.log_prob(counts)))
```

## Core distribution methods and attributes

| API | Use | Shape rule or caveat |
|---|---|---|
| `d.batch_shape` | Parameter batch dimensions. | Independent, possibly non-identical distributions. These dimensions remain in `log_prob` unless reinterpreted as event dims. |
| `d.event_shape` | Dimensions of one dependent event. | These dimensions are consumed by `log_prob`. |
| `d.event_dim` | `len(d.event_shape)`. | Useful when composing transforms. |
| `d.shape(sample_shape=())` | Predict sample shape. | Always `sample_shape + d.batch_shape + d.event_shape`. |
| `d.sample(key, sample_shape=())` | Draw samples. | Requires a JAX PRNG key for random distributions. Shape is `d.shape(sample_shape)`. |
| `d.sample_with_intermediates(key, sample_shape=())` | Draw samples plus reusable intermediates. | Important for `TransformedDistribution` and mixtures; pass intermediates to `log_prob` when available. |
| `d.log_prob(value, intermediates=None)` | Score values. | Returns a shape broadcast from `value.shape` with event dims removed and `d.batch_shape`. Must be finite only for valid support values and valid parameters. |
| `d.support` | Constraint object for valid values. | Use `d.support.check(value)` or `d.support(value)` to preflight values. |
| `d.mean`, `d.variance` | Analytic moments when implemented. | Not every distribution implements every moment. |
| `d.entropy()` | Entropy when implemented. | May raise `NotImplementedError` for some distributions. |
| `d.cdf(value)`, `d.icdf(q)` | Distribution functions when implemented. | Not all distributions implement CDF/ICDF. |
| `d.enumerate_support(expand=True)` | Enumerate discrete support. | Only available when `d.has_enumerate_support` is true. |
| `d.has_rsample`, `d.rsample(key, sample_shape=())` | Reparameterized sampling. | `rsample` raises `NotImplementedError` when unsupported. |

## Reshaping and masking distribution objects

| API | Use | Example |
|---|---|---|
| `d.expand(batch_shape)` | Broadcast an existing distribution to a target batch shape. | `dist.Normal(0, 1).expand((4,))` behaves like four iid standard normals as a batch. |
| `d.expand_by(sample_shape)` | Add leading batch dimensions to an existing batch shape. | `dist.Normal(jnp.zeros(3), 1).expand_by((5,)).batch_shape == (5, 3)`. |
| `d.to_event(k)` | Reinterpret the rightmost `k` batch dims as event dims. | `dist.Normal(jnp.zeros(3), 1).to_event(1)` scores a length-3 diagonal vector as one event. |
| `dist.Independent(base_dist, k)` | Explicit version of `base_dist.to_event(k)`. | Use when code clarity is better than method chaining. |
| `d.mask(mask)` | Zero out log probability for masked batch positions. | `mask` must broadcast to `d.batch_shape`; `mask=False` skips scoring and returns zeros. |

Example difference between batch and event dimensions:

```python
key = random.key(0)
base = dist.Normal(jnp.zeros(3), jnp.ones(3))
assert base.batch_shape == (3,)
assert base.event_shape == ()

x = base.sample(key, sample_shape=(5,))
assert x.shape == (5, 3)
assert base.log_prob(x).shape == (5, 3)

vector_event = base.to_event(1)
assert vector_event.batch_shape == ()
assert vector_event.event_shape == (3,)
assert vector_event.log_prob(x).shape == (5,)
```

## TransformedDistribution and Independent quick patterns

`TransformedDistribution(base_distribution, transforms, validate_args=None)` applies a single `Transform` or list of transforms to a base distribution. If the base distribution is already transformed, NumPyro flattens the transform list.

```python
base = dist.Normal(0.0, 1.0)
positive_dist = dist.TransformedDistribution(base, transforms.ExpTransform())
y = positive_dist.sample(random.key(1), sample_shape=(4,))
assert jnp.all(y > 0)
assert jnp.all(jnp.isfinite(positive_dist.log_prob(y)))
```

For vector events, first make the base distribution event-compatible:

```python
base_vec = dist.Normal(jnp.zeros(3), jnp.ones(3)).to_event(1)
shifted = dist.TransformedDistribution(
    base_vec,
    transforms.AffineTransform(loc=jnp.ones(3), scale=2.0),
)
assert shifted.event_shape == (3,)
```
