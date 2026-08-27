# Shapes And Plates In Pyro Distributions

Pyro follows PyTorch distribution shape semantics and adds `pyro.plate` checks at
sample sites. Most shape bugs are solved by deciding which rightmost dimensions
are **event** dimensions and which left dimensions are independent **batch/plate**
dimensions.

## Core Shape Equation

For any Pyro/PyTorch-style distribution `d`:

```python
x = d.sample(sample_shape)
assert x.shape == sample_shape + d.batch_shape + d.event_shape
assert d.shape(sample_shape) == sample_shape + d.batch_shape + d.event_shape
assert d.log_prob(x).shape == sample_shape + d.batch_shape
```

Terminology:

- `sample_shape`: iid samples requested from `.sample()` or `.rsample()`.
  These are not model plates; they are extra leading iid draws.
- `batch_shape`: independent, non-identical parameterizations of the same
  distribution class. In a `pyro.sample` site, non-event batch dimensions should
  be matched by `pyro.plate` contexts unless intentionally reinterpreted.
- `event_shape`: dimensions of one dependent draw. `log_prob()` sums/reduces
  these rightmost dimensions.

Quick examples:

```python
import torch
import pyro.distributions as dist

# Three-by-two independent scalar Normals.
d = dist.Normal(torch.zeros(3, 2), torch.ones(3, 2))
assert d.batch_shape == (3, 2)
assert d.event_shape == ()
assert d.sample().shape == (3, 2)
assert d.log_prob(torch.zeros(3, 2)).shape == (3, 2)

# Three independent length-two vector Normals.
d = dist.Normal(torch.zeros(3, 2), torch.ones(3, 2)).to_event(1)
assert d.batch_shape == (3,)
assert d.event_shape == (2,)
assert d.sample().shape == (3, 2)
assert d.log_prob(torch.zeros(3, 2)).shape == (3,)

# Five iid draws from the same distribution.
x = d.sample((5,))
assert x.shape == (5, 3, 2)
assert d.log_prob(x).shape == (5, 3)
```

## `.expand()`, `.expand_by()`, `.to_event()`, And `Independent`

Use these operations before choosing `plate` fixes:

| Operation | Effect | When to use |
|---|---|---|
| `d.expand(batch_shape)` | Expands the distribution's batch dimensions to exactly `batch_shape` where broadcasting permits. | You know the target independent/batch shape. |
| `d.expand_by(sample_shape)` | Adds dimensions on the left of `batch_shape`; Pyro's replacement for the old `reshape(sample_shape=...)` behavior. | You need an expanded distribution object rather than just calling `.sample(sample_shape)`. |
| `d.to_event(n)` | Reinterprets the `n` rightmost batch dims as event dims. `n=None` means all current batch dims. | A tensor dimension is part of one dependent datum, not conditionally independent. |
| `dist.Independent(base_dist, n)` | Equivalent idea to `.to_event(n)` for PyTorch distributions. | Useful when writing generic code; in Pyro prefer `.to_event(n)`. |
| `d.mask(mask)` | Masks log_prob/score terms by a boolean mask broadcastable to `batch_shape`. | Missing observations, padded batches, time masks. |

`to_event()` is safe but may discard independence information that SVI or
parallel enumeration could use. When a dimension is truly conditionally
independent and can be plated, prefer `pyro.plate`; when in doubt while
repairing a model, it is conservative to treat a dimension as event/dependent.

## How `pyro.plate` Interacts With Distributions

`pyro.plate(name, size, dim=None)` declares one conditionally independent batch
dimension. The `dim` argument is negative and indexes from the right. If `dim` is
omitted, Pyro chooses the rightmost available batch dimension outside enclosing
plates.

Reliable patterns:

```python
# N scalar observations.
with pyro.plate("data", N, dim=-1):
    pyro.sample("obs", dist.Normal(loc, scale), obs=y)  # loc, scale, y shape [N]

# N observations, each a D-dimensional dependent vector.
with pyro.plate("data", N, dim=-1):
    pyro.sample("obs", dist.Normal(loc, scale).to_event(1), obs=y)  # [N, D]

# Two independent axes. Explicit dims avoid collisions.
rows = pyro.plate("rows", R, dim=-2)
cols = pyro.plate("cols", C, dim=-1)
with rows, cols:
    pyro.sample("x", dist.Bernoulli(logits=logits), obs=x)  # [R, C]
```

Plate debugging rules:

1. All dimensions left of `event_shape` in a sample site's `log_prob` must be
   accounted for by plates, enumeration dims, or iid/sample dims managed by an
   inference algorithm.
2. Use explicit `dim` values for nested or reused plates; dim collisions produce
   errors suggesting `Try setting dim arg in other plates`.
3. Always provide `size` for vectorized plates when relying on Pyro automatic
   broadcasting.
4. If using automatic subsampling, index data/parameters with the yielded
   subsample indices or call `pyro.subsample(data, event_dim=...)`.
5. Enumeration-specific plate budgets (`max_plate_nesting`, enum dims,
   `config_enumerate`) belong in the enumeration sub-skill, but shape errors may
   still mention them.

## Observation Shape Debugging

For `pyro.sample(name, fn, obs=obs)`, the observation should be broadcastable to:

```python
fn.batch_shape + fn.event_shape
```

For `obs_mask`, the mask should be broadcastable to `fn.batch_shape`; Pyro then
reshapes it with singleton event dimensions internally.

Minimal diagnostic snippet:

```python
fn = dist.Normal(loc, scale).to_event(event_ndims)
print("batch", fn.batch_shape, "event", fn.event_shape)
print("expected obs broadcast", fn.batch_shape + fn.event_shape)
print("actual obs", tuple(obs.shape))
print("sample", tuple(fn.sample().shape))
print("log_prob", tuple(fn.log_prob(obs).shape))
```

If the model uses handlers or inference, trace it and compute log probabilities:

```python
from pyro import poutine

tr = poutine.trace(model).get_trace(*args, **kwargs)
tr.compute_log_prob()
print(tr.format_shapes())
```

`format_shapes()` reports each sample site's distribution shape, value shape,
and computed `log_prob` shape. Align shapes as:

```text
enum/sample dims | plate/batch dims | event dims
```

Dimensions to the right of the boundary are consumed by `log_prob()`; dimensions
left of the boundary remain in `log_prob` and must be legal plate/enum/sample
batch dimensions.

## Common Shape Recipes

### Vector Observations In A Data Plate

For `y.shape == (N, D)`:

```python
loc = torch.zeros(N, D)
scale = torch.ones(N, D)
with pyro.plate("data", N, dim=-1):
    pyro.sample("y", dist.Normal(loc, scale).to_event(1), obs=y)
```

Without `.to_event(1)`, Pyro sees two batch dimensions `(N, D)` but only one
plate; the usual error is `invalid log_prob shape`.

### Matrix Observations In A Data Plate

For `images.shape == (N, H, W)` where pixels in an image are one dependent
observation:

```python
with pyro.plate("data", N, dim=-1):
    pyro.sample("image", dist.Bernoulli(logits=logits).to_event(2), obs=images)
```

If pixels are conditionally independent and you need Pyro to exploit that
independence, use explicit nested plates instead of `.to_event(2)`.

### Categorical Vs One-Hot Categorical

```python
# Class index observation; obs shape [N].
with pyro.plate("data", N, dim=-1):
    pyro.sample("label", dist.Categorical(logits=logits), obs=class_index)

# One-hot observation; obs shape [N, K].
with pyro.plate("data", N, dim=-1):
    pyro.sample("label", dist.OneHotCategorical(logits=logits), obs=one_hot)
```

`Categorical(logits)` consumes the rightmost category parameter dimension as
part of the distribution parameterization; its event shape is empty. Its values
are integer class indices. `OneHotCategorical` has event shape `(K,)`.

### Zero-Inflated Count Plate

```python
rate = torch.ones(N)
gate_logits = torch.zeros(N)
fn = dist.ZeroInflatedPoisson(rate, gate_logits=gate_logits)
assert fn.batch_shape == (N,)
assert fn.event_shape == ()
with pyro.plate("data", N, dim=-1):
    pyro.sample("counts", fn, obs=counts)
```

For `ZeroInflatedNegativeBinomial`, ensure `total_count`, `probs`/`logits`, and
`gate`/`gate_logits` broadcast to the intended `batch_shape`.

### Mixture Shapes

For `MixtureSameFamily`:

```python
K, D = 3, 2
mix = dist.Categorical(logits=torch.zeros(K))
components = dist.Normal(torch.zeros(K, D), torch.ones(K, D)).to_event(1)
fn = dist.MixtureSameFamily(mix, components)
assert fn.batch_shape == ()
assert fn.event_shape == (D,)
```

For a batch of `N` mixtures, use mixture logits shape `(N, K)` and component
batch shape `(N, K)` before any event dims. If a component vector dimension is
mistakenly left as batch, `MixtureSameFamily` or downstream `log_prob` will have
surprising shape.

### HMM Observation Shapes

For Pyro HMM distributions, an entire time series is one event. Do not wrap the
time axis in `pyro.plate`.

#### DiscreteHMM

```python
T, S, D = 10, 4, 2
initial_logits = torch.zeros(S)                  # [..., S]
transition_logits = torch.zeros(T, S, S)         # [..., T, S, S]
obs_dist = dist.Normal(torch.zeros(T, S, D), 1).to_event(1)  # batch [T, S], event [D]
hmm = dist.DiscreteHMM(initial_logits, transition_logits, obs_dist)
assert hmm.event_shape == (T, D)

y = torch.zeros(T, D)
assert hmm.log_prob(y).shape == ()
```

Batching `B` independent sequences:

```python
initial_logits = torch.zeros(B, S)
transition_logits = torch.zeros(B, T, S, S)
obs_dist = dist.Categorical(logits=torch.zeros(B, T, S, K))
hmm = dist.DiscreteHMM(initial_logits, transition_logits, obs_dist)
assert hmm.batch_shape == (B,)
assert hmm.event_shape == (T,)
assert hmm.log_prob(torch.zeros(B, T, dtype=torch.long)).shape == (B,)
```

Homogeneous parameters may have time length `1`; `log_prob()` can score longer
observations by inferring duration from data. For sampling or fixed-shape code,
pass `duration=T`.

#### GaussianHMM

```python
T, H, D = 8, 3, 2
initial_dist = dist.MultivariateNormal(torch.zeros(H), torch.eye(H))
transition_matrix = torch.eye(H).expand(T, H, H)
transition_dist = dist.MultivariateNormal(torch.zeros(T, H), torch.eye(H).expand(T, H, H))
observation_matrix = torch.randn(T, H, D)
observation_dist = dist.MultivariateNormal(torch.zeros(T, D), torch.eye(D).expand(T, D, D))
hmm = dist.GaussianHMM(initial_dist, transition_matrix, transition_dist,
                       observation_matrix, observation_dist, duration=T)
assert hmm.event_shape == (T, D)
assert hmm.log_prob(torch.zeros(T, D)).shape == ()
```

The rightmost matrix dimensions are ordered `(old_hidden, new_hidden)` for
`transition_matrix` and `(hidden_dim, obs_dim)` for `observation_matrix`. Batch
and time dimensions broadcast to a common shape; the rightmost time dimension of
that shape becomes the first event dimension.

### Matching Shapes

```python
logits = torch.zeros(4, 4)
fn = dist.OneOneMatching(logits)
assert fn.batch_shape == ()
assert fn.event_shape == (4,)
value = torch.tensor([0, 2, 3, 1])
assert fn.log_prob(value).shape == ()
```

`OneOneMatching` and `OneTwoMatching` do not support batched logits. If you need
many independent matchings, loop outside the distribution or write a custom
batched approximation.

## CPU/CUDA Shape Caveats

- Distribution shapes are backend-independent, but all parameter tensors and
  observations in one site must live on compatible devices.
- Create constants using the same dtype/device as nearby tensors, e.g.
  `options = dict(dtype=y.dtype, device=y.device)` then `torch.zeros(...,
  **options)`.
- Do not mix CPU `torch.arange` indices with CUDA tensors in indexing-heavy HMM,
  mixture, or LKJ code; create indices on `value.device`.
- CUDA support was not part of the minimum verified runtime. Treat CUDA tests as
  optional unless the active environment has a CUDA-capable PyTorch install and
  the user asks for GPU verification.

## Validation Checks To Use Early

```python
import pyro
pyro.enable_validation(True)

# Or target a single distribution while debugging:
fn = dist.Gamma(concentration, rate, validate_args=True)
```

Validation catches:

- parameter values outside `arg_constraints` such as negative scales/rates;
- observations outside support, e.g. non-integer counts or out-of-range category
  indices;
- HMM values with too few dimensions or mismatched duration/event shape;
- some `plate` dim collisions and invalid `log_prob` shapes during inference.

Leave validation on until model shapes are stable; disable only for mature
performance-sensitive runs.
