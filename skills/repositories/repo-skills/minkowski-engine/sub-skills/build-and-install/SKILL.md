---
name: build-and-install
description: "Guides package users through installing, building, and diagnosing
  MinkowskiEngine with PyPI, source, Docker, CPU/CUDA, BLAS, compiler, and
  import-check triggers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Build and Install Router

Use this operating sub-skill when the user asks to install, build, rebuild, or diagnose MinkowskiEngine. Trigger terms include `pip install`, `setup.py`, `Docker`, `CPU_ONLY`, `force_cuda`, `CUDA_HOME`, `nvcc`, `cublas_v2.h`, `BLAS not found`, `openblas`, `mkl`, `MAX_JOBS`, `OMP_NUM_THREADS`, `undefined symbol`, `pkg_resources`, and import checks such as `ME.is_cuda_available()`.

## Route the request

- **Choose an install/build command:** read [references/build-reference.md](references/build-reference.md), then use `python scripts/build_command_helper.py --help` or a dry-run helper invocation to print a command. Prefer CPU-only commands unless the user explicitly needs CUDA and has a PyTorch CUDA build plus a matching CUDA toolkit with `nvcc`.
- **Diagnose build or import failures:** read [references/troubleshooting.md](references/troubleshooting.md) and match the observed symptom text before recommending a rebuild.
- **Verify a completed install:** use the import checks in [references/build-reference.md](references/build-reference.md). Do not claim CUDA support unless `MinkowskiEngine.is_cuda_available()` returns `True` in the user's installed environment.
- **Handle package usage questions after install:** route sparse tensor and quantization tasks to `../sparse-tensor-data/SKILL.md`, layer/network tasks to `../layers-and-networks/SKILL.md`, and training/demo adaptation to `../training-and-demos/SKILL.md`.

## Operating guardrails

1. Keep CUDA conditional. A CPU-only build is a valid install route; CUDA instructions are documented but require user-side verification.
2. Do not point the user to the original repository documentation for missing details. Use the bundled references here.
3. Prefer safe dry-run planning before running build commands. The bundled helper prints commands only and never installs packages.
4. When a path is needed, ask the user for their active environment, source tree, CUDA toolkit, or BLAS locations instead of inventing local paths.
