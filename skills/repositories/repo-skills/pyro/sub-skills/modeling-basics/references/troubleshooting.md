# Troubleshooting Modeling Basics

Use this matrix for basic Pyro model authoring failures. If diagnosis depends
mainly on distribution batch/event algebra, route to
`../../distributions-and-shapes/SKILL.md`. If it occurs inside an inference
algorithm after the model and guide are already well-formed, route to the
inference sub-skills.

## Fast triage checklist

1. Call `pyro.clear_param_store()` and `pyro.set_rng_seed(seed)` before
   reproducing a stale or flaky issue.
2. Enable checks while debugging: `pyro.enable_validation(True)`.
3. Run one traced model call with tiny inputs:
   ```python
   tr = pyro.poutine.trace(model).get_trace(*args, **kwargs)
   tr.compute_log_prob()
   print(tr.format_shapes())
   ```
4. Check whether the failing name is a sample site, param site, plate name, or
   PyroModule attribute.
5. If Graphviz/model rendering fails before your model runs, diagnose optional
   rendering dependencies rather than model logic.

## Duplicate sample, param, or plate names

Symptoms:

- `RuntimeError: Multiple sample sites named 'x'`
- `RuntimeError: x is already in the trace as a param`
- `ValueError: duplicate plate 'data'`
- Model/guide warnings about unexpected or missing sample sites during SVI.

Likely causes:

- Reusing `pyro.sample("x", ...)` twice in one model or guide execution.
- A Python loop calls the same sample-site name every iteration.
- A `pyro.param("x", ...)` shares a name with `pyro.sample("x", ...)` in the
  same trace.
- Nested or reused plates accidentally have the same `name`.
- Multiple `PyroModule` instances with the same root/nested names are executed
  in one trace without being placed under one root module.

Fixes:

```python
# Bad: duplicate site inside a loop.
for i in range(N):
    pyro.sample("z", dist.Normal(0, 1))

# OK for sequential sites.
for i in range(N):
    pyro.sample(f"z_{i}", dist.Normal(0, 1))

# Better for independent vectorized sites.
with pyro.plate("items", N):
    pyro.sample("z", dist.Normal(0, 1))
```

Use distinct namespaces for params and samples, e.g. `loc_q` for guide
parameters and `loc` for the latent sample. Put related modules under one root
`PyroModule` so names become `encoder.weight`, `decoder.weight`, etc.

## Observation warning outside inference

Symptom:

- `RuntimeWarning: trying to observe a value outside of inference at <name>`
  when calling a model directly.

Meaning:

`pyro.sample(name, dist, obs=value)` outside poutine/inference returns the
observed value and warns because no inference object is consuming the log
probability.

Fixes:

- If you only wanted to generate synthetic data, call the model with `obs=None`
  or omit the observed argument.
- If you wanted to inspect log probability or shapes, trace it:
  ```python
  tr = pyro.poutine.trace(model).get_trace(data)
  tr.compute_log_prob()
  print(tr.format_shapes())
  ```
- If you wanted training or posterior inference, route to SVI/MCMC sub-skills.

## `obs_mask` or observed data shape errors

Symptoms:

- `ValueError: Invalid obs_mask shape ... should be broadcastable to batch_shape`
- `ValueError` or `RuntimeError` mentioning mismatched tensor sizes at an
  observed site.
- `trace.format_shapes()` shows `value` shape incompatible with `dist` shape.

Likely causes:

- `obs_mask` was shaped like event dimensions instead of batch dimensions.
- Observed `data` was not indexed when using a subsampled plate.
- A scalar/vector distribution was used where an event distribution was needed,
  or vice versa.
- A plate `dim` conflicts with the tensor dimension Pyro is trying to allocate.

Basic fixes:

```python
# Multivariate event shape is (2,), batch/plate shape is (N,).
data = torch.randn(N, 2)
mask = torch.ones(N, dtype=torch.bool)
with pyro.plate("data", N):
    pyro.sample("y", dist.MultivariateNormal(torch.zeros(2), torch.eye(2)),
                obs=data, obs_mask=mask)
```

For minibatches:

```python
with pyro.plate("data", len(data), subsample_size=batch_size) as ind:
    pyro.sample("obs", dist.Normal(loc[ind], scale), obs=data[ind])
```

If `format_shapes()` shows that the distribution's `batch_shape`/`event_shape`
contract is the real issue, reroute to the distributions-and-shapes sub-skill.

## Parameter-store leakage across reruns

Symptoms:

- Changing an initializer does not change a parameter value.
- Re-running a notebook cell starts from an old learned value.
- A new `PyroModule` unexpectedly has parameters from a deleted module.
- Unit tests pass alone but fail after other Pyro tests.

Cause:

The global ParamStore persists by name. `pyro.param("x", init)` uses `init` only
when `x` is first created. `PyroModule` synchronizes attributes with the same
store unless `module_local_params` is enabled.

Fixes:

```python
# Fresh independent experiment or test.
pyro.clear_param_store()
pyro.set_rng_seed(0)
```

For multiple models in one Python process:

```python
store = pyro.get_param_store()
with store.scope() as state1:
    train_model_1()
with store.scope() as state2:
    train_model_2()
```

For module-style models that do not need standalone global `pyro.param` calls:

```python
pyro.settings.set(module_local_params=True)
# or: with pyro.settings.context(module_local_params=True): ...
```

If deleting a global-mode `PyroModule` and replacing it with another module of
the same names, either call `pyro.clear_param_store()` or use
`pyro.nn.module.clear(module)` before deletion.

## PyroModule local/global parameter confusion

Symptoms:

- `pyro.get_param_store().keys()` is empty even though a `PyroModule` trained.
- A second autoguide/model with the same names starts from the first one's
  parameters.
- `NotImplementedError: Support for global pyro.param statements in PyroModules
  with local param mode enabled is not yet implemented.`

Causes and fixes:

- With `module_local_params=True`, inspect module state with
  `model.named_parameters()` or `model.named_pyro_params()`; do not expect the
  ParamStore to hold module params.
- With global params, same-named modules intentionally synchronize through the
  ParamStore. Clear/scope the store or give modules different root names.
- Do not put standalone `pyro.param(...)` statements inside a `PyroModule`
  `forward()` when local params are enabled. Convert them to `PyroParam`
  attributes, ordinary `torch.nn.Parameter`s, or disable local params for that
  workflow.

## Plate shape mismatches

Symptoms:

- Errors mention plate sizes, negative dims, or a tensor having an unexpected
  size at a negative dimension.
- `trace.format_shapes()` shows a sample site under a plate with missing or
  extra batch dimensions.

Basic causes:

- Forgetting to index observed data or covariates by the plate's subsample
  indices.
- Using `pyro.plate("data")` without a size in code that later needs explicit
  subsampling or rendering clarity.
- Reusing the same `dim` for nested plates.
- Treating an event dimension as a plate/batch dimension.

Fixes:

```python
# Manual dim allocation for two independent axes.
rows = pyro.plate("rows", R, dim=-2)
cols = pyro.plate("cols", C, dim=-1)
with rows, cols:
    pyro.sample("x", dist.Normal(0, 1))  # batch shape should include R,C
```

When subsampling, make every data/covariate tensor follow the same indices or
use `pyro.subsample(data, event_dim=...)`. If the site needs `.to_event()` or an
`Independent` distribution, use the shapes sub-skill.

## Validation toggle surprises

Symptoms:

- A model raises support/shape errors during development but not in a faster
  run.
- A JIT variant hides validation messages.
- `pyro.settings.get("validate_poutine")` or related aliases do not match
  expectations.

Facts:

- `pyro.enable_validation(True/False)` toggles Pyro distribution, inference,
  and poutine validation together.
- Default validation follows Python `__debug__`: normally on, disabled in
  optimized Python mode.
- Some JIT inference paths temporarily disable validation during compilation.
- `pyro.settings.context(...)` restores old setting values after the context.

Fixes:

```python
pyro.enable_validation(True)
with pyro.validation_enabled(True):
    tr = pyro.poutine.trace(model).get_trace(*args, **kwargs)
    tr.compute_log_prob()
```

Prefer non-JIT inference while debugging model correctness. Use
`pyro.settings.get()` to inspect all registered setting aliases after importing
relevant Pyro modules.

## Missing Graphviz for `pyro.render_model`

Symptoms:

- ImportError says Pyro wants to use Graphviz and `pip install graphviz` is
  needed.
- Rendering returns a Python object but saving/viewing an image fails on the
  host.

Cause:

`pyro.render_model` uses the optional Python `graphviz` package; file rendering
can also need Graphviz system executables. These optional dependencies are not
part of a minimum Pyro environment.

Fixes:

- If rendering is optional, skip it and use `pyro.poutine.trace(...).get_trace()`
  plus `trace.format_shapes()` for textual debugging.
- If rendering is required, install/enable the optional Graphviz Python package
  and ensure the host has Graphviz binaries for image output.
- Keep render inputs tiny; rendering executes the model.

## `pyro.factor` in guides complains about gradients

Symptom:

- An inference error or warning indicates a guide `factor` needs `has_rsample`.

Fix:

In models, `pyro.factor("name", log_factor)` is usually enough. In guides,
state whether the factor came from a fully reparameterized differentiable path:

```python
pyro.factor("jacobian", log_abs_det_jacobian, has_rsample=True)
pyro.factor("score_term", score_like_term, has_rsample=False)
```

If the factor is part of an advanced inference or reparameterization workflow,
route to SVI/autoguide or effect-handler guidance.

## Quick symptom-to-owner map

| Symptom | First owner |
|---|---|
| Bare observed model call emits RuntimeWarning | This sub-skill: observations. |
| Duplicate sample/plate names | This sub-skill: naming and plates. |
| Parameter values persist across reruns | This sub-skill: ParamStore lifecycle. |
| `obs_mask` not broadcastable to batch shape | This sub-skill for mask basics; shapes sub-skill for deeper event/batch repair. |
| `invalid log_prob shape`, `.to_event`, support constraints | `../../distributions-and-shapes/SKILL.md`. |
| Missing guide site, model/guide mismatch under SVI | `../../svi-and-autoguides/SKILL.md`, after checking names here. |
| NUTS fails on discrete sites or invalid init | `../../mcmc-and-prediction/SKILL.md` plus effect-handler reroute if enumeration/marginalization is needed. |
| Need condition/replay/block/trace handler ordering | `../../effect-handlers-and-enumeration/SKILL.md`. |
