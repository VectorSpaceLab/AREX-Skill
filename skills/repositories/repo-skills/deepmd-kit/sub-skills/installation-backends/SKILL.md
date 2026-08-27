---
name: installation-backends
description: "Install, build, verify, select, and troubleshoot DeePMD-kit
  backend variants safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# DeePMD-kit Installation and Backends

Use this sub-skill when the task is about installing DeePMD-kit, choosing a package variant, selecting a runtime backend, validating the `dp` command, or diagnosing backend/build failures before training or inference work begins.

## Scope

This sub-skill covers:

- Choosing between pip, conda, Docker, offline installers, and source builds.
- Installing Python 3.10+ environments for TensorFlow, PyTorch, JAX, and Paddle backends.
- Selecting CLI backend aliases such as `--tf`, `--pt`, `--jax`, `--pd`, `--pt-expt`, and `--backend ...`.
- Planning source builds with `DP_VARIANT`, backend enable flags, framework roots, CUDA/ROCM roots, LAMMPS, and i-PI toggles.
- Running safe validation checks: `dp -h`, `dp --version`, backend help, Python imports, and bundled environment checks.
- Troubleshooting missing backends, Python/platform mismatches, CUDA/toolkit issues, ABI roots, stale builds, and optional integration toggles.

Do not use this sub-skill for:

- Training input authoring or optimizer/model selection; route to `../training-models/SKILL.md`.
- Data system schemas, type maps, or neighbor-stat interpretation; route to `../data-config/SKILL.md`.
- Running inference, `dp test`, model conversion, compression, or model deviation workflows; route to `../inference-model-ops/SKILL.md`.
- LAMMPS, i-PI, C API, C++ API, or Node API implementation details; route to `../integrations-development/SKILL.md`.

## First Decision: Install Path

1. If the user wants the simplest complete runtime with `dp`, LAMMPS, and MPI tools, prefer conda-forge unless they explicitly need pip wheels.
2. If the user only needs Python workflows, choose pip and install exactly the backend family they need.
3. If the platform is unsupported by wheels or the user needs ROCM, custom CUDA, custom TensorFlow/PyTorch roots, or integration toggles, plan a source build.
4. If the user needs a reproducible prebuilt shell runtime without changing an existing environment, use Docker or offline installers.
5. If the user reports a failure, validate Python, package import, `dp`, and backend modules before recommending a reinstall.

Read `references/install-backend-reference.md` for the full decision tree, backend matrix, source-build environment variables, and command examples.

## Backend Selection Rules

- DeePMD-kit imports as Python package `deepmd`; the distribution name is `deepmd-kit`.
- The `dp` CLI defaults to the TensorFlow backend unless `DP_BACKEND` or a backend flag overrides it.
- Training and freezing commands should pass explicit backend flags when the desired backend is not TensorFlow.
- Supported parser aliases include `tensorflow`/`tf`, `pytorch`/`pt`, `jax`, `paddle`/`pd`, and `pytorch-exportable`/`pt-expt`.
- Use `dp --backend <name> -h` or aliases such as `dp --pt -h` to confirm the CLI recognizes a backend before deeper debugging.
- Model-file suffixes help inference pick a backend, but install diagnosis should still confirm that the corresponding backend module is importable.

Typical backend choices:

- TensorFlow: default CLI backend; `.pb` frozen models and TensorFlow checkpoints; install `tensorflow` or `tensorflow-cpu` as appropriate.
- PyTorch: use `dp --pt`; `.pth` frozen models and `.pt` checkpoints; install `torch`; custom C++ OPs require source-build opt-in.
- JAX: use `dp --jax`; install JAX stack; exported `.savedmodel` usage also needs TensorFlow support.
- Paddle: use `dp --pd`; install `paddlepaddle` or `paddlepaddle-gpu`; frozen model output uses paired graph/parameter files.
- PyTorch exportable: use `--pt-expt` or `--backend pytorch-exportable` only for workflows that explicitly target exportable/AOT PyTorch behavior.

## Safe Validation Workflow

When a user asks whether an install is usable, run the least invasive checks first:

```bash
python --version
python -c "import deepmd; print('deepmd import ok')"
dp --version
dp -h
dp --tf -h
dp --pt -h
```

Then run the bundled helper from this sub-skill, choosing backend checks that match the user's intended model family:

```bash
python scripts/check_deepmd_environment.py --backend tensorflow
python scripts/check_deepmd_environment.py --backend pytorch --check-backend-help
python scripts/check_deepmd_environment.py --backend all --strict
```

Use `--module <python-module>` for a direct module availability check when the backend package has a nonstandard import name or the user is debugging optional dependencies.

## Pip Install Patterns

Use pip when the user wants a Python environment and accepts backend-specific wheels:

- TensorFlow CPU: install `deepmd-kit[cpu]`.
- TensorFlow GPU on CUDA 12: install `deepmd-kit[gpu,cu12]` when CUDA toolkit/cuDNN wheels are needed.
- PyTorch CPU: install CPU `torch` first from the PyTorch CPU wheel index, then install `deepmd-kit`.
- PyTorch GPU: install a PyTorch wheel compatible with the user's CUDA/driver stack, then install `deepmd-kit`.
- JAX CPU: install `deepmd-kit[jax]`.
- JAX CUDA: install `deepmd-kit[jax]` plus a CUDA-enabled JAX wheel matching the machine.
- Paddle CPU/GPU: install the correct Paddle wheel first, then install `deepmd-kit`.
- LAMMPS or i-PI extras: add only when integration commands are required, and route detailed integration setup to `../integrations-development/SKILL.md`.

Keep backend installs minimal. Do not install every heavy backend unless the user explicitly needs multi-backend compatibility.

## Conda, Docker, and Offline Packages

Choose conda-forge when the user wants solver-managed binary compatibility across Python, MPI, LAMMPS, and backend libraries. It is often the safest route for maintainers who need command-line tools plus compiled integrations.

Choose Docker when the user wants to avoid mutating host environments or needs a quick CPU/GPU runtime image.

Choose offline installers when the user has restricted network access and can satisfy runtime platform requirements. Offline and conda packages require GNU C Library 2.17 or newer; pip wheels may require newer glibc on some Linux variants.

For GPU packages, confirm the NVIDIA driver supports the package CUDA minor version. A toolkit installed in the environment does not replace the need for a compatible driver at runtime.

## Source Build Router

Use source builds only when prebuilt packages do not meet the user's target:

- Unsupported platform or wheel tag.
- Need ROCM support.
- Need custom CUDA toolkit discovery.
- Need to compile against already installed TensorFlow or PyTorch libraries.
- Need C++ interface, LAMMPS plugin/version integration, or i-PI entry points.
- Need custom PyTorch C++ OPs.

Common Python-package source-build controls:

- `DP_VARIANT=cpu|cuda|rocm` chooses CPU, CUDA, or ROCM build mode.
- `DP_ENABLE_TENSORFLOW=1|0` enables or disables TensorFlow build support; default is enabled.
- `DP_ENABLE_PYTORCH=1|0` enables or disables custom PyTorch C++ OPs; default is disabled.
- `TENSORFLOW_ROOT` points to a TensorFlow Python-library root when isolated build discovery is insufficient.
- `PYTORCH_ROOT` points to a PyTorch Python-library root when isolated build discovery is insufficient.
- `CUDAToolkit_ROOT` points to CUDA toolkit discovery for CUDA source builds.
- `ROCM_ROOT` or `ROCM_PATH` points to ROCM discovery for ROCM source builds.
- `DP_ENABLE_IPI=1` requests i-PI entry point support.
- `DP_LAMMPS_VERSION=<version>` requests LAMMPS-version-aware C++ interface build behavior.

For CPU-only development installs that avoid heavy custom OPs, install the chosen Python backend first, keep `DP_VARIANT=cpu`, disable backend C++ OPs that are not needed, and validate `deepmd` import plus `dp -h` before attempting training or inference.

## Troubleshooting Router

Read `references/troubleshooting.md` when any of these appear:

- `ModuleNotFoundError` for `tensorflow`, `torch`, `jax`, or `paddle`.
- `dp --pt` fails while `dp --tf` works, or a `.pth` model is opened in a TensorFlow-only environment.
- Python is older than 3.10.
- Package installation downloads unexpectedly large wheels or stalls on backend dependency resolution.
- CUDA is found at build time but not usable at runtime.
- TensorFlow/PyTorch ABI or root discovery fails during source build.
- Repeated source builds keep using stale CMake or build-cache state.
- LAMMPS or i-PI commands are missing after a Python-only install.

## Handoff Checklist

Before routing onward to training, data, inference, or integrations, report:

- Installation method and backend family selected.
- Python version and whether `import deepmd` passes.
- Whether `dp --version` and `dp -h` pass.
- Which backend modules were checked and whether each is importable.
- Any source-build environment variables the user must set.
- Any remaining platform, CUDA, ABI, LAMMPS, or i-PI risk.
