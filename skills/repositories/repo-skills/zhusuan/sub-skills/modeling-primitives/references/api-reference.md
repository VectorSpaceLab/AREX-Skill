# Modeling primitives API reference

This reference collects the exact ZhuSuan entry points that matter when you are
building or inspecting Bayesian networks.

## Core classes and decorators

```python
BayesianNet(observed=None)
meta_bayesian_net(scope=None, reuse_variables=False)
MetaBayesianNet.observe(**kwargs)
```

## Common distribution helpers

```python
bn.normal(name, mean=0.0, _sentinel=None, std=None, logstd=None,
          group_ndims=0, n_samples=None, is_reparameterized=True,
          check_numerics=False, **kwargs)
bn.bernoulli(name, logits, n_samples=None, group_ndims=0,
             dtype=tf.int32, **kwargs)
bn.categorical(name, logits, n_samples=None, group_ndims=0,
               dtype=tf.int32, **kwargs)
bn.uniform(name, minval=0.0, maxval=1.0, n_samples=None,
           group_ndims=0, is_reparameterized=True, check_numerics=False,
           **kwargs)
```

The other distribution helpers follow the same `BayesianNet.<distribution>`
pattern as the concrete classes in `zhusuan.distributions`.

## Network inspection helpers

```python
bn.get(name_or_names)
bn.cond_log_prob(name_or_names)
bn.log_joint()
bn.query(name_or_names, outputs=False, local_log_prob=False)
```

## Practical notes

- `group_ndims` controls how many trailing batch axes are treated as a single
  event.
- Observation tensors must broadcast to the distribution's batch and value
  shapes.
- `query()` is a legacy convenience; prefer `get()` and `cond_log_prob()` in
  new code.
- `StochasticTensor` keeps tensor-like behavior through its `bn` and `dist`
  aliases.
