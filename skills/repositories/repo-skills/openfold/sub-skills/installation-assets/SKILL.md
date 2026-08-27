---
name: installation-assets
description: "Plan and troubleshoot OpenFold installation, package builds,
  runtime dependencies, parameters, databases, Docker prerequisites, and safe
  environment validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenFold Installation and Runtime Assets

Use this sub-skill when a user needs to set up OpenFold, diagnose installation or import failures, plan model parameters/databases, check CUDA/PyTorch/OpenMM/TensorRT/DeepSpeed/cuEquivariance readiness, or validate an environment before inference or training.

## Start Here

1. Read `references/environment-and-assets.md` for supported runtime assumptions, package build behavior, dependency families, Docker notes, and asset requirements by workflow.
2. Run `python scripts/check_openfold_environment.py --json` inside the target environment to report imports, optional backends, extension availability, CUDA state, and external binaries without running downloads, inference, training, or builds.
3. Run `python scripts/plan_asset_downloads.py --workflow monomer`, `--workflow multimer`, `--workflow soloseq`, or `--workflow training` to produce a dry-run parameter/database plan. The planner never downloads or creates files.
4. Use `references/troubleshooting.md` to map symptoms such as missing `torch` during build isolation, missing `attn_core_inplace_cuda`, CUDA library failures, absent optional dependencies, missing HMMER/HHSuite/Kalign binaries, or absent parameters/databases to recovery actions.

## Boundaries

- For inference command construction, route to `../inference/` after environment and assets are selected.
- For alignment, mmCIF, cache, and training data layouts, route to `../data-preparation/`.
- For training or fine-tuning command execution, route to `../training/`.
- For model internals, TensorRT/DeepSpeed/cuEquivariance APIs, kernel behavior, and weight import details, route to `../model-apis/`.

## Safety Notes

The bundled scripts are validation and planning helpers only. They do not download assets, create conda environments, build extensions, run unit tests, run inference, run training, mutate repositories, or require a source checkout. CLI `--help` probing is opt-in and only inspects user-supplied script paths.
