# Modeling Primitives

This reference covers basic stochastic functions and global modeling controls in
Pyro 1.9.1. For detailed distribution choice or shape algebra, route to
`../../distributions-and-shapes/SKILL.md`. For inference loops, route to
`../../svi-and-autoguides/SKILL.md` or `../../mcmc-and-prediction/SKILL.md`.
For poutine composition, route to
`../../effect-handlers-and-enumeration/SKILL.md`.

## Minimal imports and skeletons

```python
import torch
import pyro
import pyro.distributions as dist
from torch.distributions import constraints
```

A Pyro model or guide is an ordinary Python callable. `pyro.sample` statements
name random variables; `pyro.param` statements name learnable deterministic
state; `obs=` marks observed data.

```python
def model(data):
    loc = pyro.sample("loc", dist.Normal(0.0, 10.0))
    scale = pyro.sample("scale", dist.LogNormal(0.0, 1.0))
    with pyro.plate("data", data.shape[0]):
        pyro.sample("obs", dist.Normal(loc, scale), obs=data)


def guide(data):
    loc_q = pyro.param("loc_q", torch.tensor(0.0))
    scale_q = pyro.param("scale_q", torch.tensor(1.0),
                         constraint=constraints.positive)
    pyro.sample("loc", dist.Normal(loc_q, scale_q))
```

Before a fresh training run, repeated notebook cell, or unit test:

```python
pyro.clear_param_store()
pyro.set_rng_seed(0)
pyro.enable_validation(True)
```

## Core primitive signatures and intent

| Primitive | Verified call shape | Use it for | Notes |
|---|---|---|---|
| `pyro.sample` | `pyro.sample(name, fn, *args, obs=None, obs_mask=None, infer=None, **kwargs)` | Random variables, observations, latent variables, and poutine-visible stochastic sites. | `fn` is usually a distribution object such as `dist.Normal(...)`. `obs` conditions a site. `obs_mask` splits observed and missing entries. |
| `pyro.param` | `pyro.param(name, init_tensor=None, constraint=constraints.real, event_dim=None)` | Learnable deterministic state in the global parameter store. | The initializer is used only the first time a name is registered. Use constraints for positive/simplex/etc. |
| `pyro.deterministic` | `pyro.deterministic(name, value, event_dim=None)` | Recording derived tensors in traces and predictive outputs. | Implemented as a masked `Delta` sample site. It does not change model density. |
| `pyro.factor` | `pyro.factor(name, log_factor, *, has_rsample=None)` | Adding an arbitrary log-density term. | In guides, specify `has_rsample=True` or `False`; in models this is usually inferred/defaulted. |
| `pyro.plate` | `pyro.plate(name, size=None, subsample_size=None, subsample=None, dim=None, use_cuda=None, device=None)` | Declaring conditional independence and optional minibatch subsampling. | `dim` must be negative if given. `use_cuda` is deprecated; prefer `device`. |
| `pyro.subsample` | `pyro.subsample(data, event_dim)` | Letting enclosing plates subsample tensors automatically. | `event_dim` is the number of rightmost non-batch dimensions. |
| `pyro.plate_stack` | `pyro.plate_stack(prefix, sizes, rightmost_dim=-1)` | Creating a contiguous stack of independent plate dimensions. | Creates plate names like `prefix_0`, `prefix_1`, ... from right to left. |

Deprecated names still exist but should not be used in new code:
`pyro.iarange` and `pyro.irange` are deprecated in favor of `pyro.plate`; the
old `pyro.random_module` is deprecated in favor of `PyroModule` and
`PyroSample`.

## Site naming rules

- Within a single execution trace, every non-param sample site must have a
  unique name. Two `pyro.sample("x", ...)` calls in one model execution raise a
  duplicate-site error under tracing/inference.
- A `pyro.param("x", ...)` and a `pyro.sample("x", ...)` cannot share the same
  trace name in one execution.
- Across a model and guide, latent sample sites should share names so inference
  algorithms can pair them. Do not create guide sites for observed-only model
  sites unless a method explicitly asks for them.
- Use loop indices in sequential code (`f"x_{i}"`) or vectorize with one named
  site inside a `plate`; do not repeatedly execute the same sample name inside a
  Python loop unless it is intentionally outside the traced region.
- `obs_mask` creates auxiliary sites named `<name>_observed` and
  `<name>_unobserved`, then records the original `<name>` as deterministic.
  Guides for masked observations may need to address the `<name>_unobserved`
  latent site.

## Observations and missingness

Observed sites are just sample sites with a fixed value:

```python
def model(x, y=None):
    weight = pyro.sample("weight", dist.Normal(0.0, 1.0))
    loc = weight * x
    with pyro.plate("data", x.shape[0]):
        pyro.sample("y", dist.Normal(loc, 1.0), obs=y)
```

Important behavior:

- Calling `pyro.sample(..., obs=value)` outside any inference/handler context
  returns `value` and emits a runtime warning that you are trying to observe a
  value outside inference. This is expected for a bare model call; use inference
  algorithms or poutine tracing when the observation is meant to contribute log
  probability.
- `obs` should be broadcastable to the distribution's full value shape
  (`batch_shape + event_shape`). If this fails, inspect shapes before changing
  inference code.
- `obs_mask` is a boolean mask broadcastable to the distribution's
  `batch_shape`, not to the event dimensions. For example, with a three-row
  plate and a two-dimensional multivariate event, masks such as scalar `True`,
  shape `(1,)`, or shape `(3,)` can be valid; a mask shaped like the event
  dimension is usually wrong.

A masked-observation pattern:

```python
def model(data, observed_mask):
    # data shape: (N, 2); observed_mask shape: () or (N,)
    with pyro.plate("data", data.shape[0]):
        pyro.sample(
            "y",
            dist.MultivariateNormal(torch.zeros(2), torch.eye(2)),
            obs=data,
            obs_mask=observed_mask,
        )
```

## Plates and subsampling

Use a plate to state that items along a batch axis are conditionally
independent:

```python
with pyro.plate("data", len(data)):
    pyro.sample("obs", dist.Normal(loc, scale), obs=data)
```

For minibatches, either index manually using the plate's returned indices:

```python
with pyro.plate("data", len(data), subsample_size=batch_size) as ind:
    batch = data[ind]
    pyro.sample("obs", dist.Normal(loc[ind], scale), obs=batch)
```

or let Pyro subsample a tensor whose left dimensions are batch dimensions:

```python
with pyro.plate("data", len(data), subsample_size=batch_size):
    batch = pyro.subsample(data, event_dim=0)
    pyro.sample("obs", dist.Normal(loc, scale), obs=batch)
```

Guidelines:

- Only use `plate` when the computation inside is conditionally independent
  across the plate index. Do not use it merely to silence a shape error.
- If specifying `dim`, use a negative index such as `dim=-1` or `dim=-2`.
  Nested plates need distinct negative dimensions. Manual `dim` choices are
  useful when model and guide must align plate dimensions exactly.
- With `subsample_size`, Pyro scales log likelihood terms by
  `full_size / batch_size` inside the plate.
- For multidimensional independent axes, use `plate_stack` or nested plates.
  If the problem is allocating event dims versus plate dims, route to the shapes
  sub-skill.

## Validation, settings, and RNG

### Validation

`pyro.enable_validation(is_validate=True)` toggles validation in Pyro
distributions, inference, and poutine. Defaults follow Python's `__debug__`
mode: validation is normally on, but optimized Python mode disables it.
Validation is temporarily disabled during JIT compilation for inference
algorithms that support JIT, so develop/debug with non-JIT variants first.

Use a context manager for temporary overrides:

```python
with pyro.validation_enabled(True):
    # run a small shape/support/debug pass
    model(data)
```

### Settings registry

`pyro.settings` manages global settings by alias:

```python
all_settings = pyro.settings.get()
assert isinstance(all_settings, dict)

old = pyro.settings.get("validate_poutine")
with pyro.settings.context(validate_poutine=True):
    pass
assert pyro.settings.get("validate_poutine") == old
```

Common aliases available after the relevant modules are imported include:

- `validate_distributions_pyro`
- `validate_distributions_torch`
- `validate_poutine`
- `validate_infer`
- `module_local_params`
- `cholesky_relative_jitter`
- `binomial_approx_sample_thresh`
- `binomial_approx_log_prob_tol`

Use `pyro.settings.context(...)` rather than permanent `set(...)` when testing a
single scenario. Validators may raise `AssertionError` for invalid values.

### RNG seeding

`pyro.set_rng_seed(seed)` seeds PyTorch, Python's `random`, and NumPy RNGs. Use
it before synthetic data generation and before initialization-sensitive tests.
It does not by itself clear learned parameters; combine it with
`pyro.clear_param_store()` for independent repeated runs.

## Inspecting traces and basic shapes

For quick debugging, trace a model rather than running a full inference loop:

```python
tr = pyro.poutine.trace(model).get_trace(data)
tr.compute_log_prob()          # optional; triggers log_prob shape checks
print(tr.format_shapes())      # summarizes param/sample/log_prob shapes
```

A trace shape table is often enough to decide whether the error belongs here or
in the distributions-and-shapes sub-skill. Basic interpretation:

- `Param Sites` show constrained parameter values returned to user code.
- Each `Sample Sites` block shows distribution batch/event shape, observed or
  sampled value shape, and `log_prob` batch shape if computed.
- A mismatch at a site named inside a `plate` often means the data, mask,
  distribution batch shape, or `.to_event()` usage disagrees with plate intent.

## Rendering a model

`pyro.render_model(model, model_args=None, model_kwargs=None, filename=None,
render_distributions=False, render_params=False, render_deterministic=False)`
returns a Graphviz `Digraph` or saves an image when `filename` is given.

Prerequisites and caveats:

- The Python `graphviz` package is optional. If it is missing, Pyro raises an
  ImportError explaining that `graphviz` must be installed. Rendering to an
  image may also need the system Graphviz binaries available on the host.
- Rendering executes the model under tracing. Keep arguments tiny and avoid
  rendering long stochastic training loops.
- `render_params=True` includes parameter nodes; `render_deterministic=True`
  includes deterministic sites.
- If rendering constrained `PyroParam` sites, `module_local_params` can be used
  either way in Pyro's tests, but missing Graphviz remains an optional-dependency
  issue rather than a model bug.
