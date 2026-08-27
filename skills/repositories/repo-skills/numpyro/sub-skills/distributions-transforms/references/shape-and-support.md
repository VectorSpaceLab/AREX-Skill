# Shape and support guide

The fastest way to debug NumPyro distribution issues is to separate three shape roles:

```text
sample value shape = sample_shape + batch_shape + event_shape
log_prob shape     = sample_shape + batch_shape
```

- `sample_shape`: iid draws requested at call time.
- `batch_shape`: independent, possibly non-identical distributions created by parameter broadcasting.
- `event_shape`: one dependent value whose dimensions are summed/consumed by `log_prob`.

This guide discusses distribution objects only. If a mismatch appears inside a NumPyro model with `plate` or `numpyro.sample`, route model-site placement and plate dimensions to `../modeling-primitives/` after applying the distribution-object checks below.

## Shape inspection workflow

```python
from jax import random
import jax.numpy as jnp
import numpyro.distributions as dist

key = random.key(0)
d = dist.Normal(jnp.zeros(3), jnp.ones(3))
print("batch", d.batch_shape, "event", d.event_shape)
value = d.sample(key, sample_shape=(5,))
print("value", value.shape, "log_prob", d.log_prob(value).shape)
```

Expected output pattern:

```text
batch (3,) event ()
value (5, 3) log_prob (5, 3)
```

If those three facts do not match the mental model, fix the distribution object before placing it in a model or inference algorithm.

## Batch versus event decisions

| You want | Keep as batch? | Use `to_event`/`Independent`? | Result |
|---|---:|---:|---|
| Three separate scalar observations, each independently scored. | Yes | No | `log_prob` keeps a rightmost dimension of length 3. |
| One length-3 diagonal-vector event. | No | Yes, `to_event(1)` | `log_prob` sums the rightmost length-3 batch dim and returns one scalar per sample. |
| A matrix-valued event, e.g. a Cholesky factor. | Usually no | Yes; or use a native matrix-event distribution/transform | `event_shape` contains the matrix dimensions. |
| A plate/model observation axis. | Usually yes at distribution level | Only if each observation is itself vector/matrix-valued | Handle plate semantics in `../modeling-primitives/`. |

Example:

```python
base = dist.Normal(jnp.zeros((4, 3)), 1.0)
assert base.batch_shape == (4, 3)
assert base.event_shape == ()

# Four independent length-3 events.
vector_event = base.to_event(1)
assert vector_event.batch_shape == (4,)
assert vector_event.event_shape == (3,)

x = jnp.zeros((4, 3))
assert base.log_prob(x).shape == (4, 3)
assert vector_event.log_prob(x).shape == (4,)
```

## `to_event` and `Independent`

`d.to_event(k)` is equivalent to `dist.Independent(d, k)` for positive `k`.

Rules:

1. `k` reinterprets the **rightmost** `k` batch dimensions.
2. `k` must be `<= len(d.batch_shape)`.
3. Reinterpreting changes the shape of `log_prob`, not the shape of samples.
4. `to_event(None)` reinterprets all current batch dimensions.
5. `to_event(0)` returns the original distribution.

Example:

```python
base = dist.Normal(jnp.zeros((2, 3)), jnp.ones((2, 3)))
all_event = base.to_event()
last_dim_event = base.to_event(1)

assert all_event.batch_shape == ()
assert all_event.event_shape == (2, 3)
assert last_dim_event.batch_shape == (2,)
assert last_dim_event.event_shape == (3,)
```

Nearest fixes for common event mistakes:

| Symptom | Likely cause | Nearest fix |
|---|---|---|
| `log_prob` has one extra trailing dimension. | A vector that should be one event is still a batch dim. | Add `.to_event(1)` to the distribution after broadcasting parameters. |
| `ValueError: reinterpreted_batch_ndims <= len(base_distribution.batch_shape)` | Asked `to_event(k)` for more dims than exist. | Expand or construct parameters with the needed batch dims first, or lower `k`. |
| `log_prob` is scalar but you expected one value per observation. | An observation axis was reinterpreted as an event dim. | Remove or reduce `.to_event(k)`; keep observation axes as batch/plate axes. |
| Transform says base shape is too small for transform domain. | Transform domain has event dims but base distribution is scalar-event. | Use `.expand(...).to_event(k)` or choose a scalar transform. |

## `expand`, `expand_by`, and parameter broadcasting

Parameter tensors determine `batch_shape` through broadcasting. `expand` can only add or broadcast batch dimensions; it does not create event dims.

```python
scalar = dist.Beta(2.0, 5.0)
expanded = scalar.expand((4,))
assert expanded.batch_shape == (4,)
assert expanded.event_shape == ()

batched = dist.Normal(jnp.zeros((2, 1)), jnp.ones((1, 3)))
assert batched.batch_shape == (2, 3)
```

Use `expand_by(sample_shape)` when you want to add leading batch dimensions to an already-batched distribution object:

```python
d = dist.Normal(jnp.zeros(3), 1.0)
assert d.expand_by((5,)).batch_shape == (5, 3)
```

## Masking batch positions

`d.mask(mask)` creates a `MaskedDistribution` whose `log_prob` returns zero where the mask is false. The mask must broadcast to `d.batch_shape`.

```python
d = dist.Normal(jnp.zeros(4), 1.0)
mask = jnp.array([True, False, True, False])
value = jnp.zeros(4)
masked_lp = d.mask(mask).log_prob(value)
assert masked_lp.shape == (4,)
assert masked_lp[1] == 0.0
```

Notes:

- `mask=True` returns the original distribution.
- `mask=False` skips scoring and returns zeros with the appropriate batch shape.
- This is distribution-level masking. Handler-level masking in a model is owned by `../modeling-primitives/`.

## Constraints and validation

A `Constraint` object represents a valid region. Distributions expose `d.support`; parameter validity is encoded in `d.arg_constraints`.

```python
from numpyro.distributions import constraints
from numpyro.distributions.distribution import validation_enabled

beta = dist.Beta(2.0, 5.0, validate_args=True)
value = jnp.array([0.2, 0.7])
assert jnp.all(beta.support.check(value))

with validation_enabled(True):
    assert jnp.all(jnp.isfinite(beta.log_prob(value)))
```

Important validation behavior:

- `validate_args=True` checks constructor parameters when possible.
- `validation_enabled(True)` temporarily enables global distribution validation.
- Validation checks are most useful in eager debugging; they do not reliably take effect under JAX `jit` or `vmap`.
- `log_prob` on out-of-support values may warn, return `-inf`, or return non-finite values depending on the distribution and value.

## Common constraints

| Constraint | Meaning | Typical transform from unconstrained space |
|---|---|---|
| `constraints.real` | Any real scalar. | `IdentityTransform` through `biject_to`. |
| `constraints.positive`, `constraints.nonnegative` | Positive/nonnegative scalar. | `ExpTransform` for the registered bijector; `SoftplusTransform` for softplus-positive support. |
| `constraints.unit_interval` | Values in `[0, 1]`. | `SigmoidTransform`. |
| `constraints.interval(low, high)` | Bounded interval. | `SigmoidTransform` followed by `AffineTransform`. |
| `constraints.greater_than(a)` / `less_than(a)` | One-sided bound. | `ExpTransform` plus affine shift/sign. |
| `constraints.simplex` | Positive vector summing to 1. | `StickBreakingTransform`; input length `K-1`, output length `K`. |
| `constraints.real_vector`, `constraints.real_matrix` | Real vector/matrix event. | `IndependentTransform` around the base scalar transform. |
| `constraints.lower_cholesky` | Lower triangular matrix with positive diagonal. | `LowerCholeskyTransform`; input vector length `D(D+1)/2`, output `D x D`. |
| `constraints.corr_cholesky` | Cholesky factor of a correlation matrix. | `CorrCholeskyTransform`; input vector length `D(D-1)/2`, output `D x D`. |
| `constraints.corr_matrix` | Correlation matrix. | `CorrCholeskyTransform` composed with inverse Cholesky matrix transform. |
| `constraints.ordered_vector` | Strictly ordered vector. | `OrderedTransform`. |
| `constraints.zero_sum(k)` | Array whose last `k` dims sum to zero. | `ZeroSumTransform(k)`. |
| `constraints.nonnegative_integer`, `integer_interval`, `boolean` | Discrete constraints. | Do not use continuous bijectors for discrete latent enumeration; route inference semantics to MCMC/SVI skills. |

## Support validation pattern

Use this pattern before blaming an inference algorithm:

```python
def assert_distribution_value_is_valid(d, value):
    value = jnp.asarray(value)
    support_ok = d.support.check(value)
    if not bool(jnp.all(support_ok)):
        raise ValueError(f"value outside support: {support_ok}")
    lp = d.log_prob(value)
    if not bool(jnp.all(jnp.isfinite(lp))):
        raise ValueError(f"non-finite log_prob: {lp}")
    return lp
```

For distributions with vector or matrix events, `support.check(value)` returns a boolean array with event dimensions consumed, mirroring `log_prob` shape.

## Difficult case: plate/to_event/Independent shape mismatch

When a user reports a mismatch involving `plate`, `to_event`, or `Independent`, handle it in two passes:

1. **Distribution-object pass in this sub-skill**
   - Print `batch_shape`, `event_shape`, and `d.log_prob(example_value).shape` outside any model.
   - Decide which rightmost dimensions are one event and apply `.to_event(k)` only to those dimensions.
   - Confirm `d.shape(sample_shape)` equals the expected sample/value shape.
   - Run a finite `log_prob` check on a synthetic in-support value.
2. **Model-site pass in `../modeling-primitives/`**
   - Only after the distribution object is correct, place observation axes in `plate`.
   - If `plate` dimensions collide or broadcast unexpectedly, debug handler/model shape semantics there.

Nearest fix heuristic:

```text
extra rightmost log_prob dim -> add to_event(1)
missing per-observation log_prob dim -> remove/reduce to_event
constructor batch shape too small -> expand or broadcast parameters before to_event
model plate collision -> route to modeling-primitives
```
