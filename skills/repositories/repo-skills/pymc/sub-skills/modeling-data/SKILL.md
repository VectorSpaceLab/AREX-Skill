---
name: modeling-data
description: "Build, mutate, inspect, and transform PyMC models with Model
  contexts, data containers, dimensions, logp/debug tools, and do/observe
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyMC modeling-data

Use this sub-skill when a task needs a PyMC model graph to be built, mutated, inspected, or conditionally transformed before inference. It covers `pm.Model`, named variables, observed data, `coords`/`dims`, `pm.Data`, `pm.set_data`, `pm.Deterministic`, `pm.Potential`, initial points, practical logp/debug helpers, graph visualization, `pm.do`, `pm.observe`, and the experimental `pymc.dims` surface.

## Read or run these bundled resources

- Read [references/modeling-and-data-workflows.md](references/modeling-and-data-workflows.md) for context-managed model construction, data updates, dimensions, prediction-data resizing, logp/debug inspection, graph visualization, `pm.do`, `pm.observe`, or `pymc.dims` routing.
- Read [references/api-reference.md](references/api-reference.md) for verified signatures, parameter meanings, and model-method call patterns.
- Read [references/troubleshooting.md](references/troubleshooting.md) for shape/coordinate errors, invalid observed data, duplicate names, missing-value imputation, transform/value-variable confusion, or Graphviz issues.
- Run [scripts/model_data_smoke.py](scripts/model_data_smoke.py) for a tiny CPU-only check covering model creation, logp, `pm.Data`, `pm.set_data`, `pm.do`, `pm.observe`, and optional posterior-predictive shape changes.

## Route here

- Creating a model with `with pm.Model(...) as model:` or object-style `model=...` registration.
- Inspecting `model.named_vars`, `model.free_RVs`, `model.observed_RVs`, `model.data_vars`, `model.deterministics`, `model.coords`, and `model.named_vars_to_dims`.
- Adding observed data and understanding missing-data/imputation caveats.
- Using `coords`, `dims`, `pm.Data`, `model.set_data`, and `pm.set_data` for reusable models and prediction-data resizing.
- Recording derived quantities or log-probability factors with `pm.Deterministic` and `pm.Potential`.
- Evaluating initial points, compiled logp functions, simple compiled expressions, `model.debug`, and `model.to_graphviz`.
- Transforming models with `pm.do` interventions or `pm.observe` conditioning.

## Route elsewhere

- Distribution catalogs, `.dist()` component distributions, custom distributions, custom logp/logcdf, support-point, and distribution transform internals: use `../distributions-logprob/SKILL.md`.
- MCMC configuration, prior/posterior predictive execution, DataTree group interpretation, convergence diagnostics, and output backends: use `../inference-predictive/SKILL.md`.
- Gaussian processes, ODE models, variational inference, and minibatches as an inference strategy: use `../advanced-workflows/SKILL.md`.

## Operating guardrails

1. Prefer a context manager and keep variable creation inside it unless you explicitly pass `model=model`.
2. Treat regular `coords`/`dims` as shape and output-label metadata, not xarray-style label alignment.
3. Use `pm.Data` for inputs you plan to replace; `pm.set_data` can change values and shape but not rank, and coordinate lengths must stay synchronized.
4. Use `model.initial_point()` as the safest starting point for compiled logp checks because it uses value-variable names, including transformed names such as `sigma_log__`.
5. `pm.do` and `pm.observe` return new models. Do not assume the original model was mutated.
