---
name: svi-and-autoguides
description: "Build, train, and debug Pyro SVI, ELBO, autoguide, and optimizer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SVI And Autoguides

Use this sub-skill when the user is building, training, evaluating, or debugging
Pyro stochastic variational inference (SVI): `SVI.step()`, `evaluate_loss()`,
model-guide pairing, ELBO choice, autoguides, Pyro optimizer wrappers, vanilla
PyTorch optimizer loops, minibatching/subsampling, JIT/vectorized particles, or
discrete-enumeration handoffs.

## Route First

- For runnable SVI loop patterns, ELBO selection, minibatching, JIT, evaluation,
  and posterior-prediction handoff, read
  [references/svi-workflows.md](references/svi-workflows.md).
- For autoguide choice, initialization, constraints, `AutoGuideList`,
  `PyroOptim` versus `torch.optim`, local `PyroModule` parameters, and flow guide
  caveats, read
  [references/autoguide-and-optimizer-reference.md](references/autoguide-and-optimizer-reference.md).
- For warnings/errors such as missing or extra guide sites, model-guide shape
  mismatches, invalid `log_prob` shape, NaNs, optimizer state surprises, JIT
  warnings, and discrete-latent enumeration routing, read
  [references/troubleshooting.md](references/troubleshooting.md).
- To confirm the installed package can run a tiny CPU SVI loop using only this
  bundled skill script, run [scripts/minipyro_svi_smoke.py](scripts/minipyro_svi_smoke.py).
  Start with `python scripts/minipyro_svi_smoke.py --help`; the default run is
  intentionally short.

## Best-Fit Tasks

Use this sub-skill for requests like:

- "write an SVI loop for this model and guide";
- "choose between `Trace_ELBO`, `TraceEnum_ELBO`, and `TraceMeanField_ELBO`";
- "replace my hand-written guide with an autoguide";
- "use a PyTorch dataloader/optimizer instead of `pyro.optim.Adam`";
- "make SVI faster with `num_particles`, `vectorize_particles`, or JIT";
- "debug a guide-site mismatch, shape error, NaN loss, or optimizer checkpoint".

## Boundaries And Reroutes

- Basic `pyro.sample`, `pyro.param`, `pyro.plate`, parameter-store lifecycle,
  and `PyroModule` basics: route to `../modeling-basics/`.
- Distribution choice, support constraints, `.to_event()`, and detailed
  batch/event/plate shape algebra: route to `../distributions-and-shapes/`.
- MCMC, NUTS/HMC, `Predictive`, posterior predictive sample shapes, and MCMC
  diagnostics: route to `../mcmc-and-prediction/`.
- Effect-handler composition, `config_enumerate`, `infer_discrete`, enumeration
  dimension allocation, masking/scaling handlers, and reparameterizers: route to
  `../effect-handlers-and-enumeration/`.
- Optional CUDA, funsor, Horovod, Lightning, Graphviz, torchvision, pandas, and
  scanpy workflows are not part of the minimum verified runtime. Treat them as
  optional or unverified unless the active user environment proves otherwise.

## High-Value Checks Before Answering

1. Clear or isolate parameter state (`pyro.clear_param_store()` or
   module-local parameters) before comparing training runs.
2. Ensure model and guide take the same `*args, **kwargs`; pass all SVI data
   through `svi.step(...)` or the ELBO module call.
3. Check every unobserved continuous latent appears in the guide unless it is
   deliberately model-enumerated or otherwise marginalized.
4. For discrete latent variables, do not guess a continuous autoguide. Decide
   whether to enumerate, use `AutoDiscreteParallel`, or reroute enumeration
   mechanics to the sibling enumeration sub-skill.
5. Keep validation enabled while debugging; most useful model/guide and shape
   errors are validation-time checks.
