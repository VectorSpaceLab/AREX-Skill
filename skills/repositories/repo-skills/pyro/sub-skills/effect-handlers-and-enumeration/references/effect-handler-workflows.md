# Effect Handler Workflows

This reference covers practical poutine composition for Pyro 1.9.1. It assumes
basic Pyro model syntax is already understood; route primitive/model basics to
`../../modeling-basics/SKILL.md` and shape-only questions to
`../../distributions-and-shapes/SKILL.md`.

## Core Handler API Map

| Handler | Signature pattern | Primary use | Notes |
|---|---|---|---|
| `poutine.trace(fn=None, graph_type=None, param_only=None)` | `poutine.trace(model).get_trace(*args, **kwargs)` or `with poutine.trace() as tr:` | Record Pyro primitive sites and inspect values/log probs. | `graph_type` is `"flat"` by default; `"dense"` adds dependency edges from `cond_indep_stack`. `param_only=True` records only params. |
| `poutine.condition(fn, data)` | `data` is a `dict[name, tensor]` or a `Trace` | Turn named sample sites into observed sites with supplied values. | For sample sites only. A conditioned latent appears with `is_observed=True`. |
| `poutine.replay(fn=None, trace=None, params=None)` | `poutine.replay(model, trace=guide_trace)` | Reuse sampled values from a trace; optionally replay constrained param values. | Does not overwrite observed sites in the target model. Trace entries must be sampled, not observed, at replayed sample names. |
| `poutine.block(...)` | `hide`, `expose`, `hide_types`, `expose_types`, `hide_fn`, `expose_fn` | Hide sites from outer handlers, autoguides, traces, or inference algorithms. | Default blocks everything. `expose=[...]` hides all except named sites. Observed sample sites can be matched as type `"observe"`. |
| `poutine.scale(fn, scale)` | positive float or tensor | Multiply score/log-prob contribution of all enclosed sample/observe sites. | Use for minibatch scaling, KL annealing, or prior weights. Use `mask` instead of nonpositive scales. |
| `poutine.mask(fn, mask)` | bool or `torch.bool` tensor | Elementwise include/exclude log-prob terms. | Masks combine by logical AND. Tensor masks must broadcast to batch/log-prob shape, not event dimensions. |
| `poutine.seed(fn, rng_seed)` | integer seed | Run a stochastic function with deterministic RNG state, then restore prior state. | Different from global `pyro.set_rng_seed()`, which mutates global RNG state. |
| `poutine.substitute(fn, data)` | `dict[param_name, constrained_tensor]` | Replace `pyro.param` values without writing the param store. | Substitutes params, not sample sites. For sample values use `condition` or `replay`. |
| `poutine.reparam(fn, config)` | `dict[site_name, Reparam]` or callable returning a reparam/`None` | Rewrite sample sites into auxiliary sites plus deterministic transforms. | Some reparameterizers need function args/kwargs; use as a decorator/wrapper rather than an inner context in those cases. |
| `poutine.infer_config(fn, config_fn)` | `config_fn(site) -> dict` | Add/modify site `infer` metadata. | `config_enumerate()` is a common wrapper built from this pattern. |
| `poutine.enum(fn=None, first_available_dim=None)` | negative `first_available_dim` | Parallel-enumerate sample sites marked with `infer={"enumerate": "parallel"}`. | Mostly used internally by `TraceEnum_ELBO`/`infer_discrete`; useful for shape diagnostics. |
| `poutine.markov(fn/iterable, history=1, keep=False, dim=None, name=None)` | usually `for t in pyro.markov(range(T)):` | Mark time-local dependency scope for enumeration dimension reuse. | Vectorized `dim`/`name` options are not implemented in the standard backend. |

## Handler Ordering Model

Pyro handlers are `Messenger`s on a stack. When a primitive such as
`pyro.sample()` executes:

1. `_process_message` runs from the innermost wrapper/context outward.
2. Pyro performs the default action if no handler already supplied a value.
3. `_postprocess_message` runs from the outermost wrapper/context inward.

A useful rule of thumb: `outer(inner(model))` lets the inner handler see the raw
site first, and the outer handler see the processed result first during
postprocessing. Therefore order matters whenever handlers overwrite values,
change visibility, or record traces.

Common ordering consequences:

- `poutine.trace(poutine.condition(model, data)).get_trace(...)` records the
  conditioned value and `is_observed=True` at the named sample sites.
- `poutine.condition(poutine.trace(model), data)` is rarely the intended shape;
  prefer tracing the already-conditioned model.
- `poutine.trace(poutine.replay(model, trace=guide_trace)).get_trace(...)`
  records model sites after latent values have been reused from the guide trace.
- `poutine.block(model, hide=["z"])` hides `z` from outer handlers. Thus
  `poutine.trace(poutine.block(model, hide=["z"]))` omits `z`, while a trace
  inside the block can still record it.
- When two `condition()` or `substitute()` handlers target the same name, the
  handler closer to the model generally gets first chance to set the value, but
  outer handlers can still overwrite in stacked compositions. Trace the result
  if ordering is ambiguous.
- Reparameterizers interact with initialization, condition, and replay. If an
  initialization value or observation is unexpectedly replaced, trace both the
  original and reparameterized model and inspect auxiliary site names.

## Trace Inspection Checklist

Basic trace pattern:

```python
import torch
import pyro
import pyro.distributions as dist
import pyro.poutine as poutine


def model(data):
    loc = pyro.sample("loc", dist.Normal(data.new_tensor(0.0), data.new_tensor(1.0)))
    with pyro.plate("data", data.size(0), dim=-1):
        pyro.sample("obs", dist.Normal(loc, data.new_tensor(1.0)), obs=data)
    return loc

trace = poutine.trace(model).get_trace(torch.zeros(4))
trace.compute_log_prob()
print(trace.format_shapes())
for name, site in trace.nodes.items():
    if site["type"] == "sample":
        print(name, {
            "observed": site["is_observed"],
            "value_shape": tuple(site["value"].shape),
            "log_prob_shape": tuple(site["log_prob"].shape),
            "scale": site["scale"],
            "mask": site["mask"],
            "infer": dict(site["infer"]),
            "plates": [(f.name, f.dim, f.size) for f in site["cond_indep_stack"]],
        })
```

Important trace facts:

- `trace.nodes` is an ordered mapping containing `_INPUT`, primitive sites, and
  `_RETURN` for `TraceHandler.get_trace()` runs.
- Sample-site dictionaries include `type`, `name`, `fn`, `value`, `is_observed`,
  `args`, `kwargs`, `infer`, `scale`, `mask`, `cond_indep_stack`, and after
  `compute_log_prob()`, `unscaled_log_prob`, `log_prob`, and `log_prob_sum`.
- `trace.log_prob_sum()` computes a scalar joint log probability and caches it.
  It applies site `scale` and `mask`.
- `trace.compute_log_prob()` computes per-site tensors; use this before reading
  `site["log_prob"]`.
- `trace.compute_score_parts()` is for ELBO internals and score-function terms;
  use it when building custom inference code rather than ordinary diagnostics.
- `trace.param_nodes`, `trace.stochastic_nodes`, `trace.observation_nodes`,
  `trace.reparameterized_nodes`, and `trace.nonreparam_stochastic_nodes` are
  useful summaries.
- `trace.format_shapes()` is the fastest way to explain batch/event/log-prob
  failures. Include it in any troubleshooting answer involving plates,
  enumeration, masking, or observations.
- `graph_type="dense"` records dependency edges between sample sites based on
  plate independence. It is useful for visualization and dependency debugging,
  but most inference code uses flat traces.

## Common Compositions

### Compute a conditioned log joint

```python
def log_joint(model, data_by_site, *args, **kwargs):
    conditioned = poutine.condition(model, data=data_by_site)
    trace = poutine.trace(conditioned).get_trace(*args, **kwargs)
    return trace.log_prob_sum()
```

Use this when comparing alternative latent assignments, checking a likelihood,
or reproducing the log-joint behavior used in inference.

### Replay a guide/posterior trace through a model

```python
guide_trace = poutine.trace(guide).get_trace(data)
model_trace = poutine.trace(poutine.replay(model, trace=guide_trace)).get_trace(data)
model_trace.compute_log_prob()
print(model_trace.format_shapes())
```

Use this to inspect the model log probability at guide-proposed latent values.
For SVI internals, Pyro's ELBO classes do a more careful version of this and
also validate model-guide matching.

### Condition a model on posterior samples and keep deterministic return values

If posterior samples are in a dictionary such as `{"z": tensor(...), "loc": ...}`:

```python
posterior_conditioned = poutine.condition(model, data=posterior_sample)
trace = poutine.trace(posterior_conditioned).get_trace(data)
result = trace.nodes["_RETURN"]["value"]
print(trace.format_shapes())
```

If deterministic quantities are created with `pyro.deterministic(...)`, they are
recorded as sample-like sites in traces. If they are ordinary Python return
values, inspect `_RETURN`. If using `Predictive`, route prediction-specific
sample-shape handling to `../../mcmc-and-prediction/SKILL.md`.

### Hide sites from an autoguide or trace

```python
from pyro.infer.autoguide import AutoDiagonalNormal

# Guide only continuous global sites; hide local/discrete sites.
guide_model = poutine.block(model, expose=["global_loc", "global_scale"])
guide = AutoDiagonalNormal(guide_model)

# Trace everything except a noisy auxiliary site.
trace = poutine.trace(poutine.block(model, hide=["aux_noise"])).get_trace(data)
```

Use `expose=[...]` when the allowed list is short and safety-critical. Use
`hide=[...]` when excluding a small number of auxiliary or observed sites.
For observed sample sites, `hide_types=["observe"]` can hide all observes from
an outer handler.

### Scale a minibatch or anneal a likelihood/prior

```python
# Mini-batch likelihood scaling.
with poutine.scale(scale=full_size / batch_size):
    with pyro.plate("data", full_size, subsample=batch, dim=-1):
        pyro.sample("obs", dist.Normal(loc[batch], scale), obs=y[batch])

# KL/likelihood annealing around selected terms.
with poutine.scale(scale=beta):
    pyro.sample("latent_prior", prior_dist)
```

`scale` must be strictly positive. If a term should be excluded, use
`poutine.mask(mask=False)` or a bool tensor mask instead.

### Mask ragged or optional likelihood terms

```python
mask = lengths.unsqueeze(-1) > torch.arange(max_time, device=lengths.device)
with pyro.plate("series", num_series, dim=-2):
    with pyro.plate("time", max_time, dim=-1):
        with poutine.mask(mask=mask):
            pyro.sample("obs", dist.Normal(mean, noise), obs=data)
```

The mask applies to log-prob batch dimensions. It must not include event
dimensions. Nested masks combine by logical AND.

### Substitute parameter values for a sensitivity check

```python
params = {"scale_q": torch.tensor(0.5)}  # constrained param value
trace = poutine.trace(poutine.substitute(guide, data=params)).get_trace(data)
```

Use `substitute()` for params. Use `condition()` or `replay()` for sample-site
values. If validation warns that supplied param names were unused, inspect the
actual param names in `poutine.trace(fn, param_only=True)`.

### Apply reparameterization before inference

```python
from pyro.infer.reparam import LocScaleReparam

reparam_model = poutine.reparam(model, config={"theta": LocScaleReparam(centered=0.0)})
trace = poutine.trace(reparam_model).get_trace(data)
print(trace.format_shapes())  # inspect original and auxiliary site names
```

Use the same reparameterized model consistently for SVI, MCMC, or tracing. Do
not apply reparameterization only in a diagnostic trace and then forget it in the
actual inference object.

## Deterministic Debugging Flow

When a poutine composition behaves unexpectedly:

1. Enable validation while debugging: `pyro.enable_validation(True)`.
2. Seed the exact run: `pyro.set_rng_seed(seed)` or `poutine.seed(model, seed)`.
3. Trace the unwrapped model and print `format_shapes()`.
4. Trace each additional handler one at a time in the intended order.
5. For each changed site, compare `value`, `is_observed`, `scale`, `mask`,
   `infer`, and `cond_indep_stack`.
6. If `block` is involved, verify whether the handler you care about is inside
   or outside the block.
7. If enumeration or reparameterization is involved, inspect auxiliary site
   names and enum dimensions in `site["infer"]` after the corresponding handler
   has run.
