---
name: effect-handlers-and-enumeration
description: "Use Pyro poutine effect handlers, traces, discrete enumeration,
  reparameterizers, and inference-tied tensor ops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Effect Handlers And Enumeration

Use this sub-skill when the task involves Pyro's poutine stack, trace/replay/
condition/block/scale/mask/seed/substitute/reparam handlers, discrete latent
variable enumeration, posterior decoding with `infer_discrete`, `TraceEnum_ELBO`
or Tensor Monte Carlo setup, reparameterizers, or inference-adjacent `pyro.ops`
utilities such as `Vindex`, plated `einsum`, HMM contraction helpers, and stats.

This guidance targets the `pyro-ppl` 1.9.1 API family imported as `pyro`. It is
self-contained; do not rely on the source checkout, original notebooks, or
example scripts at runtime.

## Route First

- For poutine handler semantics, handler ordering, trace node inspection,
  condition/replay posterior workflows, and masking/scaling compositions, read
  [references/effect-handler-workflows.md](references/effect-handler-workflows.md).
- For `TraceEnum_ELBO`, `config_enumerate`, `infer_discrete`,
  `max_plate_nesting`, `first_available_dim`, TMC/funsor caveats,
  reparameterizer config patterns, and selected `pyro.ops` utilities, read
  [references/enumeration-and-reparameterization.md](references/enumeration-and-reparameterization.md).
- For recovery steps after duplicate names, enum dimension allocation failures,
  missing `funsor`, JIT warnings, trace shape errors, handler order surprises,
  or reparameterizer failures, read [references/troubleshooting.md](references/troubleshooting.md).
- To confirm that the active package can run a tiny CPU enumeration plus trace
  workflow without the original checkout, run
  [scripts/enumeration_trace_smoke.py](scripts/enumeration_trace_smoke.py).
  Start with `python scripts/enumeration_trace_smoke.py --help`; defaults are
  intentionally short and deterministic.

## Best-Fit Tasks

Use this sub-skill for requests like:

- "trace this model and inspect sample/param sites, log probabilities, masks,
  scales, or `cond_indep_stack`";
- "condition the model on posterior samples, replay a guide trace through a
  model, or trace deterministic return sites";
- "hide sites from an autoguide with `poutine.block` or expose only selected
  sample/param sites";
- "scale or mask part of a likelihood, minibatch objective, prior term, or
  ragged time-series likelihood";
- "enumerate a discrete latent variable, use `TraceEnum_ELBO`, compute MAP or
  sampled discrete states with `infer_discrete`, or debug enum dimensions";
- "apply `AutoReparam`, `LocScaleReparam`, `TransformReparam`, `StableReparam`,
  `LinearHMMReparam`, `SplitReparam`, `NeuTraReparam`, or related config";
- "use `Vindex`, plated `pyro.ops.contract.einsum`, HMM Gaussian contractions,
  or `pyro.ops.stats` diagnostics where they support inference code".

## Boundaries And Reroutes

- Beginner model authoring, `pyro.sample`/`pyro.param` introductions,
  parameter-store lifecycle, `pyro.plate` basics, validation, RNG, or
  `PyroModule`: route to `../modeling-basics/`.
- Distribution selection, support constraints, `.to_event()`, batch/event shape
  algebra, HMM distribution constructors, and generic shape debugging: route to
  `../distributions-and-shapes/`.
- Ordinary SVI loops, autoguide choice, ELBO choice outside enumeration,
  optimizer wrappers, or PyTorch optimizer loops: route to
  `../svi-and-autoguides/` after the enumeration/handler contract is clear.
- HMC/NUTS/MCMC loops, initialization strategies, MCMC diagnostics, and
  `Predictive`: route to `../mcmc-and-prediction/`, using this sub-skill only
  for conditioning/replay/reparameterizer details.
- Domain-specific contributed examples, `pyro.contrib.funsor` workflows,
  Horovod/Lightning/Graphviz/torchvision/pandas/scanpy extras, and long HMM
  demos: route to `../contrib-and-domain-workflows/`. Treat them as optional or
  unverified unless the active user environment proves support.

## High-Value Checks Before Answering

1. Confirm whether the user needs a handler composition, a traced diagnostic, a
   discrete enumeration algorithm, or a reparameterization. These look similar
   in code but have different ordering and shape rules.
2. For poutine composition, reason from the execution stack: handlers process
   messages from the innermost wrapper first and postprocess from the outermost
   wrapper first. If values are unexpectedly overwritten, inspect handler order.
3. For traces, call `trace.compute_log_prob()` before reading per-site
   `log_prob`; use `trace.format_shapes()` in every shape/debug answer.
4. For enumeration, set `max_plate_nesting` to the number of nested vectorized
   plates around enumerated/observed sites, then allocate enum dimensions to the
   left with `first_available_dim = -1 - max_plate_nesting`.
5. For model-side enumeration, use only `infer={"enumerate": "parallel"}`;
   model-side sequential enumeration is not implemented. Guide-side sequential
   enumeration is supported but can multiply execution count.
6. For indexed parameters under enumerated variables, prefer
   `pyro.ops.indexing.Vindex` or broadcasting-safe tensor code; do not branch on
   a parallel-enumerated tensor value.
7. Treat `funsor`, CUDA, Horovod, Lightning, Graphviz, torchvision, pandas, and
   scanpy as optional/unverified in the minimum environment unless the current
   runtime explicitly imports them.
