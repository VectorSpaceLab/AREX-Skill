# Pyro API Cheatsheet

## Purpose

Use this root reference as a quick map from user intent to the Pyro API surface
and the owning sub-skill. It is intentionally compact; read the linked
sub-skill references for runnable recipes, shape details, and troubleshooting.

## Package Identity

- Distribution name: `pyro-ppl`.
- Import name: `pyro`.
- Runtime dependency family: PyTorch plus `numpy`, `opt_einsum`, `pyro-api`, and
  `tqdm`.
- Optional examples/integrations may require extras such as `extras`, `funsor`,
  `horovod`, or `lightning`; see [troubleshooting.md](troubleshooting.md) and
  `sub-skills/contrib-and-domain-workflows/references/optional-integrations.md`.
- This snapshot has no console-script entry points; Pyro workflows are Python
  API workflows.

## Core Imports

```python
import torch
import pyro
import pyro.distributions as dist
import pyro.poutine as poutine
from pyro.infer import SVI, Trace_ELBO, TraceEnum_ELBO, MCMC, NUTS, Predictive
from pyro.optim import Adam
from pyro.infer.autoguide import AutoNormal, AutoDiagonalNormal
```

Minimal health check:

```python
import pyro, torch
print(pyro.__version__)
print(torch.__version__, torch.cuda.is_available())
```

For a fuller safe diagnostic, run `scripts/check_pyro_environment.py` from this
skill tree.

## Route by Task

| User intent | Start here | High-value API names |
|---|---|---|
| Write a basic stochastic function, observe data, use `plate`, seed, clear state, or debug param leakage | `sub-skills/modeling-basics/SKILL.md` | `pyro.sample`, `pyro.param`, `pyro.deterministic`, `pyro.factor`, `pyro.plate`, `pyro.clear_param_store`, `pyro.set_rng_seed`, `pyro.enable_validation` |
| Use `PyroModule`, `PyroParam`, `PyroSample`, or module-local parameters | `sub-skills/modeling-basics/SKILL.md` | `pyro.nn.PyroModule`, `PyroParam`, `PyroSample`, `pyro.settings.set(module_local_params=True)` |
| Choose a likelihood/prior distribution or fix event/batch/log-prob shapes | `sub-skills/distributions-and-shapes/SKILL.md` | `pyro.distributions`, `.to_event()`, `dist.Independent`, constraints, transforms, `Trace.format_shapes()` |
| Train with variational inference | `sub-skills/svi-and-autoguides/SKILL.md` | `SVI`, `Trace_ELBO`, `TraceMeanField_ELBO`, `TraceGraph_ELBO`, `TraceEnum_ELBO`, `JitTrace_ELBO`, `AutoNormal`, `AutoGuideList`, `PyroOptim`, `Adam` |
| Use ordinary PyTorch optimizers or dataloaders with Pyro losses | `sub-skills/svi-and-autoguides/SKILL.md` | `Trace_ELBO()(model, guide)`, `loss_fn.parameters()`, `torch.optim.Adam` |
| Run HMC/NUTS or posterior diagnostics | `sub-skills/mcmc-and-prediction/SKILL.md` | `NUTS`, `HMC`, `MCMC`, `MCMC.run`, `get_samples`, `summary`, `diagnostics` |
| Draw prior or posterior predictive samples | `sub-skills/mcmc-and-prediction/SKILL.md` | `Predictive`, `WeighedPredictive`, `MHResampler`, `return_sites`, posterior sample dictionaries |
| Inspect/compose effect handlers | `sub-skills/effect-handlers-and-enumeration/SKILL.md` | `poutine.trace`, `condition`, `replay`, `block`, `scale`, `mask`, `seed`, `substitute`, `reparam` |
| Marginalize or decode discrete latent variables | `sub-skills/effect-handlers-and-enumeration/SKILL.md` | `config_enumerate`, `TraceEnum_ELBO`, `infer_discrete`, `poutine.enum`, `Vindex`, `pyro.markov` |
| Use contributed modules or domain tutorials | `sub-skills/contrib-and-domain-workflows/SKILL.md` | `pyro.contrib.forecast`, `gp`, `epidemiology`, `tracking`, `easyguide`, `minipyro`, `funsor`, `cevae`, `mue`, `zuko` |

## Verified Signature Highlights

These signatures were inspected from an installed Pyro 1.9.1-family package.
Use them to avoid guessing argument names:

```text
pyro.sample(name, fn, *args, obs=None, obs_mask=None, infer=None, **kwargs)
pyro.param(name, init_tensor=None, constraint=Real(), event_dim=None)
pyro.plate(name, size=None, subsample_size=None, subsample=None, dim=None, use_cuda=None, device=None)
pyro.module(name, nn_module, update_module_params=False)
SVI(model, guide, optim, loss, loss_and_grads=None, num_samples=0, num_steps=0, **kwargs)
Trace_ELBO(num_particles=1, max_plate_nesting=inf, vectorize_particles=False, ...)
TraceEnum_ELBO(num_particles=1, max_plate_nesting=inf, vectorize_particles=False, ...)
MCMC(kernel, num_samples, warmup_steps=None, initial_params=None, num_chains=1, ...)
NUTS(model=None, potential_fn=None, step_size=1, adapt_step_size=True, target_accept_prob=0.8, max_tree_depth=10, ...)
HMC(model=None, potential_fn=None, step_size=1, trajectory_length=None, num_steps=None, target_accept_prob=0.8, ...)
Predictive(model, posterior_samples=None, guide=None, num_samples=None, return_sites=(), parallel=False)
config_enumerate(guide=None, default="parallel", expand=False, num_samples=None, tmc="diagonal")
infer_discrete(fn=None, first_available_dim=None, temperature=1, strict_enumeration_warning=True)
```

## Package-Use Checklist

Before giving a Pyro answer:

1. Identify whether the user is asking about model syntax, distributions/shapes,
   SVI, MCMC/prediction, effect handlers/enumeration, or contrib/domain code.
2. Enable validation while debugging: `pyro.enable_validation(True)`.
3. Clear global parameter state between independent experiments:
   `pyro.clear_param_store()`.
4. For shape issues, trace and print `trace.format_shapes()` before proposing a
   fix.
5. For optional integrations, verify imports in the user's environment before
   claiming support.
6. For CUDA questions, distinguish "GPU is visible" from "this Pyro workflow has
   been verified on CUDA"; CPU checks do not prove CUDA device behavior.
