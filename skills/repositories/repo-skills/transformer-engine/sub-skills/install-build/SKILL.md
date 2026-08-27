---
name: install-build
description: "Install, build, and verify NVIDIA Transformer Engine runtime variants safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# install-build

Use this sub-skill when the task is about Transformer Engine installation or
build readiness, including:

- installing from PyPI, NGC containers, or a source checkout;
- choosing PyTorch, JAX, both-framework, or core-only builds;
- preparing CUDA, cuDNN, NCCL, compiler, CMake, Ninja, and submodule inputs;
- building editable or wheel-like source variants without broad QA/dev extras;
- verifying imports, extension loading, package-version consistency, and GPU
  capability boundaries;
- debugging CUDA/cuDNN/NCCL/submodule/shared-object/framework import failures.

Do not use this sub-skill as the final native verification owner. This sub-skill
can make installation and import validation safe; final framework behavior and
native test coverage remain owned by the repo-skill verification flow.

## Route

1. For install method selection, framework extras, source-build commands,
   environment variables, submodule requirements, and safe validation order,
   read [build-and-install](references/build-and-install.md).
2. For failures after or during install, read
   [troubleshooting](references/troubleshooting.md) and match the first exact
   symptom before changing packages or loader paths.
3. For source builds, adapt the bundled
   [source build environment template](scripts/source_build_env_template.sh).
   The template is non-destructive by default and requires explicit `--install`
   to run `pip install --no-build-isolation -e .`.

## Fast decisions

- Prefer an NGC PyTorch or JAX container when the user wants a known-good GPU
  stack and does not need a custom source patch.
- Prefer PyPI extras for stable package use: `pytorch`, `jax`, both extras, or
  core-only CUDA package.
- Prefer a source build when the user needs the current checkout, an editable
  install, a custom CUDA architecture list, or a framework selection not matched
  by the installed wheels.
- On A100/SM80, build for BF16-capable Ampere use, set `NVTE_CUDA_ARCHS=80`,
  and disable NCCL EP with `NVTE_WITH_NCCL_EP=0`; do not promise FP8, MXFP8, or
  NVFP4 runtime there.
- On Hopper/Ada/Blackwell, distinguish support by feature: FP8 requires compute
  capability 8.9 or newer, NCCL EP requires Hopper or newer SM90+, and MXFP8 or
  NVFP4 runtime requires Blackwell-class hardware.
