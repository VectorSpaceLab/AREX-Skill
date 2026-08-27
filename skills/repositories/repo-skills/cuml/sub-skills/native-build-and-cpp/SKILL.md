---
name: native-build-and-cpp
description: "Route cuML source-build, libcuml, C++/CUDA API, and native test workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# native-build-and-cpp

Use this sub-skill when the task is about building cuML from source, choosing between `libcuml` and `cuml` source-build targets, validating the C++/CUDA toolchain, using public C++ APIs, selecting CTest or pytest partitions for source changes, or reviewing native/Python contribution pitfalls.

Do **not** use this sub-skill for ordinary installed-package estimator workflows, `cuml.dask` operating recipes, `cuml.accel` activation, release automation, CI secrets, devcontainer maintenance, or benchmark execution unless the user explicitly asks for a source-build benchmark.

## Route

1. If the user only needs to run cuML algorithms from Python, route back to the root package workflow or `python-estimators`; source builds are only required for local source edits, C++ API work, package-build validation, ABI/linkage debugging, or native tests/examples.
2. Before any source build, run the bundled non-mutating probe in `scripts/source_build_probe.py` to check GPU visibility, compute capability hints, `nvcc`, compiler, CMake, Ninja, Python, and Cython readiness. The probe reports evidence only and does not configure or build.
3. Use `references/source-build-and-cpp.md` to choose the smallest build path: `libcuml` for C++/CUDA library and C++ tests/examples, `cuml` for the Python package after matching `libcuml`, `prims` for primitive tests, and benchmarks only on explicit request.
4. Use `references/source-build-and-cpp.md` for manual CMake flags, `build.sh` target/flag taxonomy, C++ example patterns, and native test partition commands.
5. Use `references/troubleshooting.md` when CUDA hardware, toolkit, RAPIDS dependency pins, CMake, linker, source-package, or native-test failures appear.

## Safety and verification boundaries

- CUDA runtime validation needs an NVIDIA GPU. Building may configure without a GPU, but C++ examples, CTest GPU tests, Python estimator tests, and health checks require a compatible CUDA device.
- Match the CUDA major/minor and RAPIDS package version family across `libcuml`, `cuml`, RAFT, RMM, cuVS, cuDF, pylibraft, and optional Dask packages. Do not mix stable/nightly or CUDA 12/13 package suffixes.
- Prefer focused configure/build/test commands over broad CI scripts. Use benchmarks and multi-GPU tests only when the requested change requires them and the environment has the extra dependencies.
