---
name: contrib-and-domain-workflows
description: "Navigate Pyro contrib modules, domain examples, optional
  integrations, and safe skip policies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Contrib And Domain Workflows

Use this sub-skill when a Pyro task is about `pyro.contrib`, domain-focused
examples/tutorial patterns, `pyro.generic` or MiniPyro backends, or optional
integrations such as Funsor, Horovod, Lightning, Graphviz rendering,
torchvision, pandas, scanpy, scikit-learn, or zuko.

This guidance targets the `pyro-ppl` 1.9.1 package family imported as `pyro`.
It is self-contained: do not require an external repository checkout, examples,
tutorial notebooks, or tests at runtime.

## Route First

- To choose among contributed modules, understand maturity/stability, identify
  best-fit tasks, and hand off to core Pyro sub-skills, read
  [references/contrib-module-map.md](references/contrib-module-map.md).
- For domain workflow patterns in forecasting, Gaussian processes,
  epidemiology, tracking, HMM/RSA/capture-recapture, scANVI, VAEs, CEVAE, AIR,
  DMM, MuE, and MiniPyro/generic backends, read
  [references/domain-workflows.md](references/domain-workflows.md).
- For optional extras, install/skip policy, Funsor, Horovod, Lightning,
  Graphviz rendering, zuko, CUDA flags, and data/plotting dependencies, read
  [references/optional-integrations.md](references/optional-integrations.md).
- For failures involving optional imports, downloads, plotting, GPU flags, long
  training, contributed-module stability, or domain data shape issues, read
  [references/troubleshooting.md](references/troubleshooting.md).

No local script is bundled for this sub-skill. Optional-extra diagnostics are
owned by the root Pyro skill's environment check rather than by a
contrib-specific script.

## Best-Fit Tasks

Use this sub-skill for requests like:

- "Should I use `pyro.contrib.forecast`, `pyro.contrib.timeseries`, a core SVI
  model, or an HMM distribution for this time series?"
- "What does `pyro.contrib.gp` provide, and what dependencies do the GP examples
  need?"
- "Can this environment run `pyro.contrib.funsor`, Horovod, Lightning, Graphviz
  rendering, scANVI, or zuko flows?"
- "Adapt a domain example pattern safely without downloading data or running a
  long tutorial."
- "Use MiniPyro or `pyro.generic` for backend-agnostic didactic code."
- "Decide whether to skip, ask for data, ask for GPU, or ask to install extras."

## Mandatory Safety Gates

1. Treat all `pyro.contrib` APIs as less stable than core Pyro. The package
   states that contributed code is in various stages of development and does not
   guarantee backwards compatibility.
2. Do not claim optional extras are available unless the active user environment
   proves them. Funsor, Graphviz, Horovod, Lightning, torchvision, pandas,
   scanpy, and similar extras should be treated as optional until probed.
3. Prefer tiny synthetic or mock data when explaining domain examples. Do not
   require a future agent to run external examples, notebooks, or download
   public datasets merely to answer a modeling question.
4. Ask before long training, broad extra installation, network downloads, or GPU
   use. If the task can be answered with distilled module behavior and a tiny
   mock pattern, do that first.
5. If a question is really about core primitives, shapes, SVI, MCMC, or poutine,
   reroute to the sibling sub-skill instead of duplicating core mechanics here.

## Reroute Boundaries

- Basic `pyro.sample`, `pyro.param`, `pyro.plate`, parameter-store lifecycle,
  `PyroModule`, and `pyro.render_model` basics: route to
  `../modeling-basics/`.
- Distribution choice, HMM distribution shapes, support constraints,
  `.to_event()`, `GaussianHMM`, `LinearHMM`, and `log_prob` shape errors: route
  to `../distributions-and-shapes/`.
- SVI loops, ELBO choice, autoguides, Pyro/PyTorch optimizer mechanics, and
  minibatching: route to `../svi-and-autoguides/`.
- HMC/NUTS/MCMC, posterior predictive sampling, and diagnostics: route to
  `../mcmc-and-prediction/`.
- Poutine handler ordering, trace/replay/condition/block, discrete enumeration,
  `TraceEnum_ELBO`, `infer_discrete`, Funsor-backed enumeration mechanics, and
  reparameterizers: route to `../effect-handlers-and-enumeration/`.

## Fast Triage

| User asks about | Start here | Then hand off when needed |
|---|---|---|
| Time-series forecasting with future samples | `pyro.contrib.forecast` in the module map | SVI/MCMC or distribution-shape siblings for inference mechanics |
| Gaussian-process regression/classification/GPLVM | `pyro.contrib.gp` in the module map | SVI/MCMC sibling for training choices; shapes sibling for kernel tensor issues |
| SIR/SEIR/regional epidemic model | Epidemiology domain notes | MCMC/SVI sibling for fit settings; optional integration notes for CUDA/plotting |
| Object tracking or EKF | Tracking domain notes | Distribution-shape sibling for likelihood shapes |
| Discrete HMM, capture-recapture, RSA | HMM/RSA/capture-recapture domain notes | Enumeration/effect-handler sibling |
| scANVI, VAEs, AIR, DMM, CEVAE | Domain notes plus optional integration policy | SVI/autoguide sibling for training-loop fixes |
| `pyro.contrib.funsor` import error | Optional integrations and troubleshooting | Enumeration sibling for non-Funsor fallback |
| Graphviz/rendering failure | Optional integrations and troubleshooting | Modeling-basics for `pyro.render_model` usage |
