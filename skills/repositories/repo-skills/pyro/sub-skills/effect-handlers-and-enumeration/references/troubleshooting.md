# Troubleshooting Effect Handlers And Enumeration

Use this reference when Pyro poutine composition, trace inspection, enumeration,
reparameterization, or inference-adjacent tensor utilities fail. Keep validation
enabled while debugging unless the issue is a known mature hot path.

```python
import pyro
pyro.enable_validation(True)
```

## Fast Diagnostic Baseline

Before changing a model, collect a trace shape report:

```python
import pyro.poutine as poutine

trace = poutine.trace(model).get_trace(*args, **kwargs)
try:
    trace.compute_log_prob()
finally:
    print(trace.format_shapes())
    for name, site in trace.nodes.items():
        if site["type"] == "sample":
            print(name, {
                "observed": site["is_observed"],
                "value": tuple(site["value"].shape),
                "scale": site["scale"],
                "mask": site["mask"],
                "infer": dict(site["infer"]),
                "plates": [(f.name, f.dim, f.size) for f in site["cond_indep_stack"]],
            })
```

For enumeration-specific shape debugging, trace the enumerated model:

```python
enum_model = poutine.enum(model, first_available_dim=-1 - max_plate_nesting)
trace = poutine.trace(enum_model).get_trace(*args, **kwargs)
trace.compute_log_prob()
print(trace.format_shapes())
for name, site in trace.iter_stochastic_nodes():
    print(name, site["infer"].get("_enumerate_dim"), tuple(site["value"].shape))
```

## Symptom Matrix

| Symptom / message | Likely cause | Recovery |
|---|---|---|
| `RuntimeError: Multiple sample sites named 'x'` | The same sample site name was executed twice in one trace. Common causes: loop without indexed names, reusing a stochastic helper twice, or missing `pyro.plate`/scope discipline. | Make names unique in dynamic loops, e.g. `f"x_{t}"`; use `pyro.plate` for independent vectorized copies instead of repeated scalar names; if a contrib/autoname helper is involved, inspect generated names. |
| `x is already in the trace as a param` or sample/param name conflict | A `pyro.param` and `pyro.sample` share a name in the same trace. | Rename params and sample sites. Keep guide params like `x_loc`, `x_scale` distinct from latent `x`. |
| Duplicate `plate` name or `collide at dim=` | Two active vectorized plates share a name or negative dim. | Give plates unique names; assign explicit dims from the right, e.g. outer data `dim=-1`, group `dim=-2`, then move one left if collision message suggests `dim=-3`. |
| `invalid log_prob shape` after adding handlers | A hidden plate, `mask`, `.to_event()`, or observed value changed batch/event interpretation. | Print `trace.format_shapes()` at the failing site; route pure distribution/event-shape fixes to `../../distributions-and-shapes/SKILL.md`; ensure every non-event batch dim is in a vectorized plate or intentionally converted with `.to_event()`. |
| Mask error: expected BoolTensor or mask shape mismatch | `poutine.mask()` received non-bool data or a mask including event dims. | Convert to `mask.bool()`; shape the mask to broadcast to `log_prob` batch shape only. Use distribution `.mask()` only when you understand event dims; otherwise prefer poutine mask around the likelihood. |
| `Expected scale > 0` | `poutine.scale()` got zero/negative/non-finite scale. | Use a positive scalar/tensor for weights; use `poutine.mask(mask=False)` to remove terms. For minibatches, scale by `full_size / batch_size`. |
| `Expected all enumerated sample sites to share a common poutine.scale` | Model-side enumeration has dependent enumerated terms under different scales, which breaks the enum contraction assumptions. | Move scaling outside the whole enumerated dependency component, use a common scalar scale for all dependent enum sites, or replace elementwise inclusion with `poutine.mask`. |
| `TraceEnum_ELBO found no sample sites configured for enumeration` or `infer_discrete found no sample sites...` | No site has `infer["enumerate"]` after wrappers run. | Add `infer={"enumerate": "parallel"}` at target discrete sites or wrap the model/guide with `config_enumerate(...)`; set `strict_enumeration_warning=False` only if no enumeration is intentional. |
| `model-side sequential enumeration is not implemented` | A model sample site used `infer={"enumerate": "sequential"}` with `TraceEnum_ELBO`. | Use model-side `parallel`, move the site into the guide with sequential enumeration, or rewrite dynamic control flow to be tensorized. |
| Assertion or error around `first_available_dim` | `infer_discrete` or `poutine.enum` received `None` or a non-negative dim in a context that needs finite negative enum dims. | Set `max_plate_nesting` explicitly and use `first_available_dim = -1 - max_plate_nesting`. For one data plate use `-2`; for two nested vectorized plates use `-3`. |
| `max_plate_nesting must be set to a finite value for parallel enumeration` | Parallel enumeration tried to allocate dims while plate nesting was left as infinity/automatic. | Pass a finite `TraceEnum_ELBO(max_plate_nesting=N)` or `infer_discrete(..., first_available_dim=-1-N)`. Count vectorized plates that can enclose enumerated/dependent sites. |
| Enum `value` has unexpected extra singleton dimensions | Parallel enumeration adds a support dimension to the left of plates and singleton dims for broadcasting. | Do not squeeze blindly. Use `Vindex` for parameter indexing and inspect `trace.format_shapes()` to understand support vs plate dims. |
| `Expected tree-structured plate nesting` | Enumerated dependencies induce a non-tree plate structure, e.g. a diamond dependency across plates. | Re-express the model to reduce treewidth, move some variables to a guide, use sequential enumeration for small cases, or accept approximate inference/TMC if appropriate. |
| `Vindex`/indexing gives wrong shapes under enumeration | Ordinary advanced indexing collapsed/broadcast dimensions differently from Pyro's enum semantics. | Replace `tensor[z]`/multi-index advanced indexing with `Vindex(tensor)[z]` or `Vindex(tensor)[..., z, :]` as appropriate; print shapes before and after indexing. |
| `infer_discrete` returns values but trace scores look wrong | This is expected: inferred model trace log probabilities are not meaningful. | Use `infer_discrete` for decoded values or `_RETURN`; use `TraceEnum_ELBO`/conditioned traces for scoring comparisons. |
| `temperature must be 0 (map) or 1 (sample)` | `infer_discrete` currently supports only MAP and posterior sampling. | Use `temperature=0` for Viterbi/MAP or `temperature=1` for sampling. |
| `No module named 'funsor'` or `pyro.contrib.funsor` import fails | Optional `funsor` extra is not installed. It is not part of the minimum verified environment. | Use ordinary Pyro enumeration when possible. If the user's task truly requires funsor, ask to install/verify the optional extra and route domain-specific funsor workflows to `../../contrib-and-domain-workflows/SKILL.md`. |
| `poutine.collapse` fails at import or with Funsor conversion errors | `poutine.collapse` is experimental and requires `funsor`; code inside collapse must accept Funsor values rather than ordinary tensors. | Avoid collapse unless the active env proves funsor support and the model is built for it. If plates appear inside collapse, manually declare finite `max_plate_nesting`. |
| JIT warning about converting tensor to Python boolean/index or iterating over tensor | JIT sees dynamic Python control flow or tensor-to-Python conversion. | First verify non-JIT. Use `JitTraceEnum_ELBO` only for static structure; pass tensor data through args and non-tensor compile keys through kwargs. Use `pyro.util.ignore_jit_warnings()` only when static-shape assumptions are deliberately valid. |
| `jit support not yet added for TraceTMC_ELBO` or missing `JitTraceTMC_ELBO` | Standard 1.9.1 TMC workflow does not expose a JIT TMC ELBO. | Use non-JIT `TraceTMC_ELBO`, exact `TraceEnum_ELBO`, or an active optional backend that explicitly proves JIT TMC support. |
| Reparameterizer introduces unexpected auxiliary sites | `poutine.reparam` rewrites one site into auxiliary sample sites plus deterministic transformation. | Trace before/after, list stochastic nodes, and update guide/block/return-site names to account for auxiliary sites. Do not assume the original sample site remains the only latent. |
| Reparameterizer warning about initialization not commuting | Init/condition/replay supplied a value that the reparameterizer cannot preserve exactly. | Prefer applying reparam consistently before constructing guides/MCMC kernels; inspect values in a trace; use reparam-specific initialization or accept default fallback only after checking shapes. |
| `Stable.log_prob` unavailable or fails in inference | Some stable distributions need auxiliary reparameterizers for likelihood-based algorithms. | For latent stable sites use `LatentStableReparam`; for observed symmetric/arbitrary stable likelihoods use the corresponding `SymmetricStableReparam` or `StableReparam` pattern and verify with a trace. |
| `NeuTraReparam` / `StructuredReparam` complains about guide/static structure | Multi-site reparameterizer requires a trained compatible guide and static latent structure. | Train the required guide first, keep all sites sharing one reparam instance, and reroute SVI guide training details to `../../svi-and-autoguides/SKILL.md`. |
| `substitute` warning says supplied param names were unused | Keys in `data` do not match user-level param names encountered by `pyro.param`. | Run `poutine.trace(fn, param_only=True)` and inspect `trace.param_nodes`; use user param names, not unconstrained/internal names. |
| `replay` says site must be sampled in trace | Replaying a target sample site against an observed or non-sample trace entry. | Replay only unobserved sample sites from a guide/posterior trace. Use `condition()` for observed values. |
| `block` hides too much or too little | Default `poutine.block()` hides everything from outer handlers; `hide`, `expose`, and type filters have different defaults. | Prefer `expose=[...]` for autoguide construction over a short whitelist. Trace with and without block and compare `trace.nodes`. |

## Fixing `max_plate_nesting` And Enum Dims

1. Count active vectorized plates that can contain enumerated sites or observed
   sites depending on enumerated values. Ignore sequential Python loops and
   `pyro.markov` itself; count `pyro.plate(..., dim=...)` contexts.
2. Set `TraceEnum_ELBO(max_plate_nesting=N)` for SVI-style enumeration.
3. For standalone posterior decoding, set
   `infer_discrete(..., first_available_dim=-1-N)`.
4. If using manual plate dims, reserve `-1` through `-N` for plates and allow
   enum dims at `-1-N`, `-2-N`, and further left.
5. If the error says two plates collide, fix plate dims before changing enum
   dims.
6. If enum dimensions grow over time in an HMM, wrap the time loop in
   `for t in pyro.markov(range(T)):` and keep state dependencies local.

Example mapping:

| Model shape | Plate dims | `max_plate_nesting` | `first_available_dim` |
|---|---:|---:|---:|
| No vectorized plates | none | `0` | `-1` |
| One data plate | `dim=-1` | `1` | `-2` |
| Data and group plates | `dim=-1`, `dim=-2` | `2` | `-3` |
| Three nested vectorized plates | `dim=-1`, `-2`, `-3` | `3` | `-4` |

## Handler Order Surprise Recipes

### Condition then trace

Correct diagnostic:

```python
conditioned = poutine.condition(model, data={"z": z_value})
trace = poutine.trace(conditioned).get_trace(data)
assert trace.nodes["z"]["is_observed"]
```

If the trace does not show `is_observed=True`, a `block` may be hiding `z` from
the outer trace, or another condition/replay handler is overwriting values.

### Replay guide into model

```python
guide_trace = poutine.trace(guide).get_trace(data)
model_trace = poutine.trace(poutine.replay(model, trace=guide_trace)).get_trace(data)
```

If replay fails, check that the guide trace has an unobserved sample at every
replayed site. Observed model sites are not overwritten by replay.

### Block and autoguides

```python
# Good whitelist for a guide over selected global sites.
guide_model = poutine.block(model, expose=["global_a", "global_b"])
```

If an autoguide includes too many local sites, your block was likely outside the
autoguide construction or used `hide` when `expose` was safer.

### Scale vs mask

Use `scale` for weights and `mask` for inclusion/exclusion. Do not emulate a
mask with scale zero; Pyro validates scale positivity and enumeration has common
scale assumptions.

## Trace Shape Diagnostics To Include In Answers

When explaining a shape error, show or ask the user to produce:

- `trace.format_shapes()`;
- each suspect site's `fn.batch_shape`, `fn.event_shape`, `value.shape`, and
  `log_prob.shape` after `trace.compute_log_prob()`;
- `cond_indep_stack` entries `(name, dim, size)`;
- `site["infer"].get("_enumerate_dim")` for enumerated sites;
- whether `mask` and `scale` are scalar or tensors;
- whether the value is observed via `condition`, original `obs=`, `replay`, or
  `infer_discrete`.

Then route remaining pure distribution/event-shape fixes to
`../../distributions-and-shapes/SKILL.md` and remaining inference-loop fixes to
`../../svi-and-autoguides/SKILL.md` or `../../mcmc-and-prediction/SKILL.md`.

## Optional Dependency Policy

The minimum verified runtime covers CPU Pyro core, poutine, enumeration,
reparameterizers that do not require optional extras, and selected `pyro.ops`.
Do not claim these are available unless the user's environment proves it:

- `funsor` and `pyro.contrib.funsor`;
- CUDA-specific behavior;
- Horovod, Lightning, Graphviz, torchvision, pandas, scanpy;
- long tutorial/example data downloads or plotting stacks.

If an optional dependency is required by the user's target, ask for permission to
prepare or verify that dependency rather than silently rewriting the task as a
core Pyro workflow.
