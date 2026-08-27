# Transform workflows

Use transforms when you need to map between unconstrained values and constrained support, build transformed distributions, or validate shape-preserving/shape-changing bijections.

## Imports

```python
from jax import random
import jax.numpy as jnp
import numpyro.distributions as dist
from numpyro.distributions import constraints, transforms
from numpyro.distributions.transforms import biject_to
```

## Choose a transform from support

Prefer the registry when starting from a constraint:

```python
constraint = constraints.positive
transform = biject_to(constraint)
unconstrained = jnp.array(0.0)
positive_value = transform(unconstrained)
assert constraint.check(positive_value)
```

Common mappings:

| Support target | Typical transform |
|---|---|
| real | `IdentityTransform` |
| positive | `ExpTransform` or a softplus-style transform when explicitly chosen |
| unit interval | `SigmoidTransform` |
| interval `[low, high]` | `SigmoidTransform` + `AffineTransform` |
| simplex | `StickBreakingTransform` |
| ordered vector | `OrderedTransform` |
| lower Cholesky | `LowerCholeskyTransform` |
| correlation Cholesky | `CorrCholeskyTransform` |
| zero-sum arrays | `ZeroSumTransform` |

Do not use continuous transforms to handle discrete latent variables. Route discrete enumeration or Gibbs sampling questions to `../svi-autoguides/` or `../mcmc-diagnostics/`.

## Build a `TransformedDistribution`

```python
base = dist.Normal(0.0, 1.0)
lognormal_like = dist.TransformedDistribution(base, transforms.ExpTransform())
y = lognormal_like.sample(random.key(0), sample_shape=(5,))
assert jnp.all(y > 0)
assert jnp.all(jnp.isfinite(lognormal_like.log_prob(y)))
```

For vector events, create the base event shape first:

```python
base_vector = dist.Normal(jnp.zeros(3), 1.0).to_event(1)
shifted = dist.TransformedDistribution(
    base_vector,
    transforms.AffineTransform(loc=jnp.ones(3), scale=2.0),
)
assert shifted.event_shape == (3,)
```

## Compose transforms

`ComposeTransform([t1, t2, ...])` applies transforms in sequence. Match domain/codomain event dimensions.

```python
chain = transforms.ComposeTransform([
    transforms.AffineTransform(loc=1.0, scale=2.0),
    transforms.ExpTransform(),
])
x = jnp.array([-0.5, 0.0, 0.5])
y = chain(x)
assert jnp.allclose(chain.inv(y), x)
```

If a transform changes dimensionality, such as `StickBreakingTransform` or Cholesky transforms, the input and output shapes will differ. Always check a round trip on a tiny tensor before using the transform inside an inference workflow.

## Validate round-trip and log-det

```python
def assert_transform_ok(transform, x):
    y = transform(x)
    x_roundtrip = transform.inv(y)
    if not bool(jnp.allclose(x_roundtrip, x, atol=1e-5, rtol=1e-5)):
        raise ValueError("transform inverse did not round-trip")
    ladj = transform.log_abs_det_jacobian(x, y)
    if not bool(jnp.all(jnp.isfinite(ladj))):
        raise ValueError(f"non-finite log_abs_det_jacobian: {ladj}")
    return y, ladj
```

For orthonormal time transforms such as `HaarTransform` and `DiscreteCosineTransform`, unit-Jacobian behavior is a key sanity check:

```python
x = random.normal(random.key(0), (2, 8))
for transform in [transforms.HaarTransform(), transforms.DiscreteCosineTransform()]:
    y = transform(x)
    assert jnp.allclose(transform.inv(y), x, atol=1e-5)
    assert jnp.allclose(transform.log_abs_det_jacobian(x, y), 0.0, atol=1e-6)
```

## Transform interop with inference

- MCMC and SVI automatically use support transforms for constrained sample and parameter sites.
- Explicit model reparameterization uses `numpyro.handlers.reparam` plus reparameterizer classes such as `TransformReparam` or `LocScaleReparam`; route inference-specific decisions to `../mcmc-diagnostics/` or `../svi-autoguides/`.
- For a transformed latent distribution, `TransformReparam` can expose the base latent variable, often improving geometry.

## Common decision checklist

- [ ] Is the target support continuous? If not, do not choose a continuous bijector.
- [ ] Does the base distribution have the event shape the transform expects?
- [ ] Does `transform.inv(transform(x))` round-trip on a tiny example?
- [ ] Is `log_abs_det_jacobian(x, transform(x))` finite and shaped as expected?
- [ ] Does the transformed distribution return finite `log_prob` for in-support samples?
