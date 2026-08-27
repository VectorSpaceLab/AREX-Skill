---
name: modeling-basics
description: "Author and debug basic Pyro models, primitives, parameter state,
  validation, seeds, plates, and PyroModule parameters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Modeling Basics for Pyro

Use this sub-skill when a task asks you to author or debug a basic Pyro program:
stochastic functions, `pyro.sample`, `pyro.param`, observed data, `pyro.plate`,
subsampling, parameter-store lifecycle, validation settings, RNG seeding,
`PyroModule`, `PyroParam`, `PyroSample`, or `pyro.render_model` prerequisites.

This guidance targets the `pyro-ppl` 1.9.1 package family imported as `pyro`.
It is self-contained for runtime use.

## Route first

- For primitive usage, model/guide skeletons, observations, `obs_mask`, plates,
  validation, seeds, site names, and rendering prerequisites, read
  [references/modeling-primitives.md](references/modeling-primitives.md).
- For `pyro.param`, `ParamStoreDict`, constraints, save/load state,
  `pyro.module`, `PyroModule`, `PyroParam`, `PyroSample`, and
  `module_local_params`, read
  [references/modules-and-parameters.md](references/modules-and-parameters.md).
- For warnings and failures such as duplicate sample names, observation warnings,
  parameter leakage, plate shape mismatches, missing Graphviz, or confusing
  validation toggles, read
  [references/troubleshooting.md](references/troubleshooting.md).

## Reroute boundaries

- Deep distribution choice, event/batch/sample shape algebra, transforms, and
  support constraints: `../distributions-and-shapes/SKILL.md`.
- SVI training loops, ELBO choice, autoguides, and optimizer recipes:
  `../svi-and-autoguides/SKILL.md`.
- HMC/NUTS/MCMC, posterior predictive, and prediction APIs:
  `../mcmc-and-prediction/SKILL.md`.
- Poutine handler composition, trace/replay/condition/block, enumeration,
  reparameterizers, and `max_plate_nesting`: `../effect-handlers-and-enumeration/SKILL.md`.

## Basic operating rules

1. Start repeated experiments, unit tests, and independent training runs with
   `pyro.clear_param_store()` unless you intentionally want to reuse existing
   parameters.
2. Keep validation on while developing: `pyro.enable_validation(True)`. Use
   `with pyro.validation_enabled(False): ...` only around mature hot paths.
3. Seed reproducible snippets with `pyro.set_rng_seed(seed)` before generating
   synthetic data or initializing parameters.
4. Give every sample site a unique name within a single execution trace. Model
   and guide latent sites should share names; observed model sites usually have
   no guide site.
5. Use `pyro.plate` only for conditionally independent batch dimensions. If the
   error is mainly about `batch_shape`, `event_shape`, `.to_event()`, or
   `log_prob` shape, reroute to the shapes sub-skill.
6. Prefer `PyroModule` / `PyroParam` / `PyroSample` for module-style models.
   Use old `pyro.module(name, nn_module, update_module_params=False)` mainly
   for registering an ordinary `torch.nn.Module` with the global parameter
   store.

## Entry points to recognize

- `pyro.sample(name, fn, *args, obs=None, obs_mask=None, infer=None, **kwargs)`
- `pyro.param(name, init_tensor=None, constraint=constraints.real, event_dim=None)`
- `pyro.plate(name, size=None, subsample_size=None, subsample=None, dim=None, use_cuda=None, device=None)`
- `pyro.module(name, nn_module, update_module_params=False)`
- `PyroModule(name="")`, `PyroParam(init_value=None, constraint=constraints.real, event_dim=None)`, `PyroSample(prior)`
- `pyro.settings.get()`, `pyro.settings.set(...)`, `pyro.settings.context(...)`
- `pyro.enable_validation(...)`, `pyro.validation_enabled(...)`, `pyro.set_rng_seed(...)`
