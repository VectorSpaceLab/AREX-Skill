# SVI Troubleshooting

Use this matrix when SVI fails, warns, produces NaNs, or trains suspiciously.
Most issues are easier to diagnose with validation enabled and a very small
fixture.

## First Response Checklist

1. Reduce to one batch and a few SVI steps.
2. Call `pyro.clear_param_store()` before the run unless intentionally resuming.
3. Enable validation while debugging: `pyro.enable_validation(True)`.
4. Run model and guide through one ELBO call before the long loop.
5. Check every loss and important parameter with `torch.isfinite(...)`.
6. If using JIT or vectorized particles, reproduce the issue without them first.

## Model/Guide Site Mismatches

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Found vars in model but not guide: {...}` | An unobserved model latent has no guide site. | Add a guide sample site with the same name, use an autoguide that covers it, or intentionally enumerate/marginalize the site and switch to enumeration-aware guidance. |
| `Found non-auxiliary vars in guide but not model` | Guide samples a site not present in the model. | Rename/remove the guide site, block guide parts correctly, or mark a genuine auxiliary guide sample with `infer={"is_auxiliary": True}`. |
| `Model and guide event_dims disagree at site ...` | Same sample-site name but different event dimensions. | Match `.to_event(...)` / `Independent` structure in model and guide; route detailed shape algebra to `../distributions-and-shapes/`. |
| `Model and guide shapes disagree at site ...` | Parameter shape, plate size, broadcasting, or event shape differs. | Print model and guide traces, compare `fn.batch_shape`, `fn.event_shape`, and observed/value shapes; fix plates or parameter shapes. |
| `Multiple sample sites named ...` | Duplicate site name within model or guide, often inside a loop without unique names. | Make names unique or wrap repeated iid structure in `pyro.plate`. |

Quick trace inspection pattern:

```python
import pyro.poutine as poutine

guide_trace = poutine.trace(guide).get_trace(*args, **kwargs)
model_trace = poutine.trace(poutine.replay(model, guide_trace)).get_trace(*args, **kwargs)
model_trace.compute_log_prob()
guide_trace.compute_log_prob()
print(model_trace.format_shapes())
print(guide_trace.format_shapes())
```

## Invalid `log_prob` Shape

Typical message:

```text
at site "...", invalid log_prob shape
Expected ..., actual ...
Try one of the following fixes:
- enclose the batched tensor in a with pyro.plate(...): context
- .to_event(...) the distribution being sampled
- .permute() data dimensions
```

Recovery order:

1. Identify whether the tensor dimension is independent batch structure or part
   of one multivariate event.
2. If independent observations, wrap the site in a correctly sized `pyro.plate`.
3. If dependent event dimensions, add `.to_event(k)` to the distribution.
4. If data dimensions are merely ordered differently, permute/reshape data to
   match model expectations.
5. For nested plates, set explicit negative `dim` values to avoid collisions.
6. For enumeration or vectorized particles, set `max_plate_nesting` explicitly.

Route detailed shape reasoning to `../distributions-and-shapes/`.

## NaN Or Infinite Loss

| Cause | Diagnostic | Fix |
|---|---|---|
| Learning rate too high | Loss finite at step 0 then explodes. | Lower `lr`, use `ClippedAdam`, pass `clip_args`, or manually clip gradients. |
| Invalid distribution parameters | Validation error or NaN in prior/guide parameters. | Add constraints to `pyro.param`; transform positive/simplex/cholesky params correctly. |
| Bad initialization | First ELBO call is NaN/inf or support transform fails. | Use `init_to_feasible`, explicit `init_to_value`, or smaller `init_scale`. |
| Heavy-tailed or extreme observations | Large log probabilities, unstable scale params. | Normalize data, use robust priors, clamp unconstrained params cautiously, or anneal difficult factors. |
| Zero/negative scale in a custom guide | Distribution constructor or validation error. | Use `constraint=constraints.positive`, `softplus`, or an autoguide. |
| Plate subsampling scale mistake | Loss magnitude changes wildly with batch size. | Confirm `plate` full size and minibatch size; avoid double-scaling with both `plate` and manual scaling. |

Useful guards:

```python
loss = svi.step(*args, **kwargs)
if not torch.isfinite(torch.as_tensor(loss)):
    raise RuntimeError(f"non-finite SVI loss: {loss}")
for name, value in pyro.get_param_store().items():
    if not torch.isfinite(value).all():
        raise RuntimeError(f"non-finite parameter {name}")
```

## Optimizer And Parameter State Problems

| Symptom | Cause | Recovery |
|---|---|---|
| Repeated experiments influence each other | Global parameter store retains old params by name. | Call `pyro.clear_param_store()` before each independent run. |
| PyTorch optimizer sees no parameters | Autoguide/PyroParams are lazy. | Run one batch through the ELBO module before constructing `torch.optim`. |
| Resumed training ignores optimizer momentum | Optimizer state was not saved/loaded with parameters. | Save/load both parameter store and `PyroOptim` state; load before params are encountered. |
| Two `PyroModule` models share parameters unexpectedly | Global parameter-store names overlap. | Use `pyro.settings.set(module_local_params=True)` and the ELBO module pattern when possible. |
| Per-parameter learning rate callable not used as expected | Callable receives normalized parameter names. | Log received names once, then match suffixes or exact normalized names. |

## JIT And Vectorized Particle Issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| JIT tracer warnings | Tensor-to-Python branching, dynamic shapes, or non-tensor inputs in positional args. | Debug non-JIT; pass tensors via `*args`, non-tensors via `**kwargs`; set `ignore_jit_warnings=True` only after validating equivalence. |
| JIT recompiles repeatedly | Non-tensor kwargs or changing callable identity differ across calls. | Stabilize kwargs and model/guide objects; avoid dynamic Python configuration in the hot loop. |
| Different JIT and non-JIT losses | Dynamic structure or unsupported tracing pattern. | Use non-JIT or refactor to static structure. |
| `plate stack overflow` | `max_plate_nesting` too small for nested plates/enumeration/particle plate. | Increase `max_plate_nesting`; count nested vectorized plates plus vectorized particles/enumeration needs. |
| Shape error only with `vectorize_particles=True` | Particle plate dimension collides with user plate or dynamic structure. | Set explicit plate dims and `max_plate_nesting`, or disable vectorized particles. |

## Enumeration Handoff

Discrete latent variables are a common SVI failure point.

- `Trace_ELBO` warns if it finds enumerated guide sites; use `TraceEnum_ELBO`
  for enumerated sites.
- `TraceEnum_ELBO` warns if no sites are configured for enumeration and
  `strict_enumeration_warning=True`; use `Trace_ELBO` if enumeration was not
  intended.
- Model-side sequential enumeration is not implemented. Prefer parallel
  enumeration or guide-side enumeration.
- `TraceEnum_ELBO.compute_marginals()` and `.sample_posterior()` have additional
  restrictions such as `num_particles == 1` and no guide enumeration for those
  helpers.
- Enumeration requires careful plate nesting and dimension allocation. Route
  detailed `config_enumerate`, `infer_discrete`, `max_plate_nesting`, and enum
  dimension debugging to `../effect-handlers-and-enumeration/`.

Decision rule:

1. If the latent is continuous: use a continuous autoguide or custom continuous
   guide.
2. If the latent is discrete and small enough to sum out: configure enumeration
   and use `TraceEnum_ELBO`.
3. If discrete and part of a mixed guide: compose blocked guide parts with
   `AutoGuideList`, often continuous autoguide plus `AutoDiscreteParallel` for
   supported discrete sites.
4. If discrete and too large for exact enumeration: state the approximation
   explicitly and consider custom relaxed or amortized guides.

## When To Reroute

- Shape catalog, `.to_event()`, supports, constraints, and distribution families:
  `../distributions-and-shapes/`.
- Primitive model authoring, parameter store basics, `PyroModule` basics, and
  validation settings: `../modeling-basics/`.
- Enumeration mechanics and effect-handler debugging: `../effect-handlers-and-enumeration/`.
- Posterior predictive sampling and return-site shape debugging:
  `../mcmc-and-prediction/`.
