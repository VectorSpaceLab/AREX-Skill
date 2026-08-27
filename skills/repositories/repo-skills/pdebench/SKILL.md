---
name: pdebench
description: "Guide PDEBench scientific-machine-learning benchmark workflows for
  PDE dataset preparation, simulation generation, baseline neural operators,
  PINNs, inverse models, metrics, and safe result analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PDEBench

PDEBench is a scientific machine-learning benchmark package covering PDE
simulation data, HDF5 datasets, FNO/U-Net/PINN baselines, inverse methods, and
metrics. Use this skill when a task mentions PDEBench, its PDE names or dataset
files, neural operators for PDEs, `velocity2vorticity`, Hydra PDE generation,
or the benchmark's forward/inverse model configuration.

## Choose a route

- **Dataset files, metadata, visualization, or velocity-to-vorticity:** read
  [data-and-download](sub-skills/data-and-download/SKILL.md). It owns local
  HDF5 schemas, safe metadata checks, the converter, and spectral-vorticity
  APIs.
- **PDE simulation or NLE/JAX generation:** read
  [data-generation](sub-skills/data-generation/SKILL.md). It owns Hydra config
  selection, bounded generation planning, NLE families, and NPY-to-HDF5 merge
  boundaries.
- **Forward/inverse baselines, metrics, or result analysis:** read
  [models-and-evaluation](sub-skills/models-and-evaluation/SKILL.md). It owns
  FNO, U-Net, PINN, inverse, Hydra training/evaluation, and metric routing.

For a task that spans routes, start here, then load each relevant sub-skill in
upstream-to-downstream order: data layout → generation or retrieval → model or
evaluation.

## Install and inspect

The public distribution is `pdebench` and the repository declares Python
`>=3.9,<3.11`. A minimal install is:

```bash
python -m pip install pdebench
python -c "import pdebench; print('pdebench import ok')"
```

For the legacy-compatible package stack, use a Python 3.9 or 3.10 isolated
environment and let the package metadata select its base dependencies. The
`datagen39` and `datagen310` extras add optional Clawpack, PhiFlow, JAX, and
CUDA-oriented dependencies; install one only when a specific generation route
needs it. They are not required for metadata checks or the baseline CPU API
smokes.

PINN workflows use DeepXDE. Select the PyTorch backend before importing the PINN
modules when more than one DeepXDE backend is installed:

```bash
DDE_BACKEND=pytorch python -c "import deepxde; print(deepxde.backend.backend_name)"
```

PyTorch and JAX code can use CUDA when a compatible backend build is installed.
The verified baseline for this skill is CPU PyTorch/JAX; do not claim CUDA
runtime coverage from a CPU import.

## Shared operating rules

1. Identify the PDE family, data filename/layout, model route, and expected
   output before constructing a command.
2. Read the nearest linked reference before using a long parameter list or
   HDF5 schema. Keep data paths explicit; Hydra may change the working
   directory during a run.
3. Start with `--help`, config rendering, a local metadata check, or a tiny
   deterministic smoke. Do not download multi-GB/TB datasets, upload to
   DaRUS, generate benchmark-scale data, or train for hundreds of epochs by
   default.
4. Treat `data_path`, `filename`, `single_file`, resolutions, `initial_step`,
   and model-specific channel counts as a coupled contract. Validate shapes
   before training or evaluation.
5. Keep output directories new and explicit. Never overwrite checkpoints or
   converted HDF5 files without an intentional `--overwrite`-style decision.
6. Use [cross-cutting troubleshooting](references/troubleshooting.md) for
   install, optional dependency, backend, path, and artifact problems.

## Provenance and limits

Read [repository provenance](references/repo-provenance.md) before deciding
whether this skill matches a current checkout or whether a refresh is needed.
Read [installation and compatibility](references/installation-and-compatibility.md)
when versions, optional extras, or backends are unclear. This operating graph
covers public package workflows; it does not certify benchmark scores, replace
large datasets, or make network and credential decisions for the user.
