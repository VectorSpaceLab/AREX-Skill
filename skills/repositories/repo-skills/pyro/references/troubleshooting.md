# Pyro Troubleshooting

## Purpose

Use this root troubleshooting reference for cross-cutting install/import,
optional dependency, backend, validation, and workflow-routing failures. For
workflow-specific recovery, follow the sub-skill links in each row.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'pyro'` | `pyro-ppl` is not installed in the active Python environment, or a different interpreter is running the code. | Install with `pip install pyro-ppl` in the environment that runs the task. Re-run `python -c "import pyro; print(pyro.__version__)"`. |
| User installed `pyro` but import still fails or imports the wrong project | The PyPI distribution for this library is `pyro-ppl`; `pyro` may refer to a different package depending on environment history. | Install/upgrade `pyro-ppl`; check `python -m pip show pyro-ppl` and `python -c "import pyro; print(pyro.__version__)"`. |
| `pyroapi` import fails | Runtime dependency `pyro-api` is missing or environment is inconsistent. | Reinstall `pyro-ppl` or install `pyro-api>=0.1.1`, then run `python -m pip check`. |
| `torch` import fails or Pyro complains about PyTorch | Pyro requires PyTorch (`torch>=2.0` in this snapshot). | Install a PyTorch build compatible with the user's Python, OS, and desired CPU/CUDA backend before reinstalling Pyro. |
| `python -m pip check` reports broken requirements | Mixed package managers, incompatible torch/numpy, or partially upgraded environment. | Prefer a fresh environment. Install PyTorch first, then `pyro-ppl`, then only the optional extras actually needed. |
| `pyro.render_model` or `render_model` complains about Graphviz | Optional Python `graphviz` package or system Graphviz executable is missing. | Install `graphviz` Python package and, if rendering files, the system Graphviz binary. If only model code is needed, skip rendering. |

Safe diagnostic: run `scripts/check_pyro_environment.py --smoke` from this skill
tree in the user's active Python environment. It reports core package versions,
CUDA visibility, optional modules, and a tiny SVI smoke test without downloads.

## Optional Dependency and Backend Policy

Pyro core workflows are ordinary Python/PyTorch API workflows. Optional
surfaces should be verified before use:

| Optional surface | Needed for | Recovery / skip policy |
|---|---|---|
| CUDA-enabled PyTorch | GPU variants of examples/tests and user models on CUDA tensors. | Install a CUDA-compatible PyTorch build, then verify `torch.cuda.is_available()` and a tiny tensor allocation. CPU success does not prove CUDA behavior. |
| `funsor[torch]` | `pyro.contrib.funsor`, `poutine.collapse`, named-dimension/funsor enumeration examples. | Install Pyro's pinned funsor extra when the task truly requires it; otherwise use ordinary `TraceEnum_ELBO`/`infer_discrete`. |
| `horovod[pytorch]` and MPI runtime | Distributed Horovod optimizer workflows. | Use the non-Horovod PyTorch/Pyro optimizer pattern unless distributed training is explicitly required and verified. |
| `lightning` | Lightning integration example. | Install only when the user asks for Lightning. Core SVI does not require it. |
| `torchvision`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `wget`, `scanpy` | Many examples/tutorials, plotting, datasets, scANVI, CVAE/VAE/vision examples. | Avoid installing all extras by default. Prefer synthetic tensors or mock data for quick Pyro logic checks. |
| System Graphviz | Rendering graph images, not basic modeling. | Treat as optional visualization support. |

## Validation, Numerical, and State Failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Duplicate sample-site name error | The same stochastic function called `pyro.sample` twice with the same name in one execution trace. | Rename sites, add indexed names in loops, or use `pyro.plate` for vectorized repeated exchangeable sites. See `sub-skills/modeling-basics/references/troubleshooting.md`. |
| Parameters unexpectedly persist across runs | Pyro's global parameter store was not cleared or a reused name points to old state. | Call `pyro.clear_param_store()` before a fresh experiment, or use `module_local_params=True` with `PyroModule` when appropriate. |
| `invalid log_prob shape` | A batch dimension is not covered by a `plate`, an event dimension is missing `.to_event()`, or a mask/obs shape is wrong. | Trace the model and print `format_shapes()`, then route to `sub-skills/distributions-and-shapes/SKILL.md`. |
| `NaN`/`inf` losses or gradients | Invalid distribution parameters, unstable optimizer step, bad scale/support, poor initialization, or too-large learning rate. | Enable validation, reduce learning rate, check constraints, inspect `warn_if_nan` warnings, and route SVI details to `sub-skills/svi-and-autoguides/SKILL.md`. |
| MCMC divergences, invalid initial params, or max tree depth | Geometry, support constraints, poor initialization, or a discrete latent site in a gradient-based sampler. | Route to `sub-skills/mcmc-and-prediction/SKILL.md`; for discrete sites route to `sub-skills/effect-handlers-and-enumeration/SKILL.md`. |
| Enumeration dimension or `max_plate_nesting` errors | Parallel-enumerated sites need enum dims to the left of vectorized plates. | Route to `sub-skills/effect-handlers-and-enumeration/SKILL.md`; set finite `max_plate_nesting` and inspect trace shapes. |

## First Response Pattern for User Failures

1. Ask for the Pyro version, PyTorch version, CPU/CUDA backend, and the shortest
   failing model/guide snippet if not already provided.
2. If import/backend uncertainty exists, ask the user to run
   `scripts/check_pyro_environment.py --smoke --json` in their environment.
3. For runtime model errors, enable validation and capture
   `poutine.trace(model).get_trace(...).format_shapes()`.
4. Route to the narrowest sub-skill:
   - modeling primitives/state: `sub-skills/modeling-basics/SKILL.md`;
   - distributions/shapes/support: `sub-skills/distributions-and-shapes/SKILL.md`;
   - SVI/autoguides/optimizers: `sub-skills/svi-and-autoguides/SKILL.md`;
   - MCMC/predictive: `sub-skills/mcmc-and-prediction/SKILL.md`;
   - handlers/enumeration/reparameterizers: `sub-skills/effect-handlers-and-enumeration/SKILL.md`;
   - contrib/domain/optional extras: `sub-skills/contrib-and-domain-workflows/SKILL.md`.
5. Avoid long training or downloads as a diagnostic. Use tiny synthetic tensors
   or bundled smoke scripts first.
