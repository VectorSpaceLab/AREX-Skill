---
name: build-and-maintenance
description: "Use this sub-skill for Torch-TensorRT source builds, package
  variants, CI/test lane selection, contributor workflows, and safe maintainer
  diagnostics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Torch-TensorRT Build and Maintenance

Use this sub-skill when the user is working on the repository itself: building from source, selecting wheel variants, diagnosing package/test setup, or choosing a safe maintainer test lane.

## Route by maintenance task

| User goal | Read/run |
| --- | --- |
| Build a wheel or install from source | `references/build-and-test.md` and `references/package-variants.md` |
| Understand package flags such as `PYTHON_ONLY`, `NO_TORCHSCRIPT`, `USE_TRT_RTX`, `CU_VERSION`, or JetPack/Windows ARM64 selectors | `references/package-variants.md` |
| Choose a safe local test lane | `references/test-selection.md` |
| Inspect CI suites or list available maintenance helpers | `scripts/list_ci_suites.py --help` |
| Probe source-build prerequisites without compiling everything | `scripts/source_build_probe.py --help` |
| Diagnose a source-build or test failure | `references/troubleshooting.md` |

## Maintenance workflow

1. Confirm whether the user is trying to build, test, package, or inspect the repository.
2. Decide whether the desired variant is standard, Python-only, no-TorchScript, TensorRT-RTX, JetPack, or Windows ARM64.
3. Check prerequisites before building: Python, PyTorch/CUDA/TensorRT family, Bazel or other build tools, and any target-specific SDKs.
4. Start from the smallest relevant lane or probe before recommending a broad test suite.
5. If a build is required, make the command match the selected package variant and platform.
6. If the task is only source inspection or CI understanding, use the bundled scripts and references rather than a full build.

## Guardrails

- Do not run long builds, full test matrices, or release automation unless the user explicitly wants them.
- Do not hide package-variant choices behind a generic `pip install .` when flags change runtime features.
- Do not tell users to edit or run files from another checkout; the skill must stand on its bundled references/scripts.
- Do not treat a successful import as proof that build/test lanes are healthy.
