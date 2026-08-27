# Modeling concepts for ZhuSuan

ZhuSuan's core modeling abstraction is a directed graphical model built with
`BayesianNet` and `MetaBayesianNet`.

## Core shape rule

A distribution input usually has shape `batch_shape + input_shape`.
Generated samples have shape `([n_samples] + ) batch_shape + value_shape`.
When `group_ndims > 0`, the last `group_ndims` dimensions of `batch_shape` are
scored together as one event.

Practical consequences:

- `n_samples=None` means one sample without a leading sample axis.
- `group_ndims=1` is common for vector-valued latent variables or weight
  matrices that should be scored as a single event.
- Observation tensors must broadcast to `batch_shape + value_shape`.

## Typical modeling flow

1. Create a `BayesianNet()`.
2. Add latent variables with distribution helpers such as
   `bn.normal(...)`, `bn.bernoulli(...)`, or `bn.dirichlet(...)`.
3. Build deterministic TensorFlow calculations from those stochastic tensors.
4. Add observed variables with the matching helper and an observation map.
5. Inspect with `get`, `cond_log_prob`, or `log_joint`.

## Reusable model pattern

Use the decorator form when you need to re-run the same graph with different
observations:

```python
@zs.meta_bayesian_net(scope='model', reuse_variables=True)
def build_model(...):
    bn = zs.BayesianNet()
    ...
    return bn
```

Then call:

```python
model = build_model(...)
bn = model.observe(x=x_obs, z=z_obs)
```

## Useful model inspection calls

- `bn.get('name')` for a node
- `bn.get(['name1', 'name2'])` for several nodes
- `bn.cond_log_prob('name')` for a single stochastic node
- `bn.log_joint()` for the full model score
- `bn.query('name', outputs=True, local_log_prob=True)` only when preserving
  older tuple-based code

## Common gotchas

- Node names must be unique inside a `BayesianNet`.
- An observation with the wrong dtype or shape fails early.
- `BayesianNet` context-manager usage exists for legacy compatibility, but the
  decorator-based `meta_bayesian_net` workflow is the modern path.
- `StochasticTensor.distribution` and `.net` are deprecated aliases; prefer
  `.dist` and `.bn`.
