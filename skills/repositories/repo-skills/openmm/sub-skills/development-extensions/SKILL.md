---
name: development-extensions
description: "Guides OpenMM maintainer and extension-author work on C++ core
  APIs, Python wrappers, serialization, plugins, platform kernels, CMake builds,
  and focused tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT, GPL, LGPL
---

# OpenMM Development Extensions

Use this sub-skill when the task is to change or extend OpenMM itself rather than to run ordinary molecular simulations. It is for maintainers and extension authors working on C++ APIs, implementation classes, kernels, plugins, serialization, Python wrapper generation, or build/test triage.

## Route by Task

- For repository layout, ownership boundaries, and the public C++ to implementation to kernel call chain, read `references/repository-architecture.md`.
- For configuring builds, selecting CMake options, wrapper builds, `ctest`, and Python test candidates, read `references/build-test-workflows.md`.
- For adding a C++ Force, Integrator, plugin, platform kernel, serialization proxy, or shared CUDA/OpenCL/HIP implementation, read `references/plugin-and-platform-development.md`.
- For symptoms such as missing platform kernels, plugin load order problems, wrapper build environment variables, serialization compatibility, CMake option mistakes, and ABI/compiler issues, read `references/troubleshooting.md`.

## Boundaries

- Stay here for maintainer workflows: C++ API and implementation edits, platform-specific kernels, plugin registration, serialization proxies, Python wrapper maintenance, CMake build/test layout, and contribution-safe test selection.
- Route normal Python simulation recipes, reporters, checkpoints, and application workflows to `../simulation-workflows/SKILL.md`.
- Route force-field XML, `ForceField`, `Modeller`, PDB/mmCIF, and modeling data workflows to `../force-fields-modeling/SKILL.md`.
- Route user-level custom expression forces and Python `CustomIntegrator` recipes to `../custom-forces-integrators/SKILL.md`; return here only when the user needs a compiled C++ API, kernel, or plugin.
- Route runtime platform choice, precision/performance tuning, and hardware-facing simulation advice to `../platforms-performance/SKILL.md`; return here for implementing or debugging platform code.

## Maintainer Defaults

- Treat C++ build, plugin, wrapper-generation, and native test commands as checkout/build-tree workflows. Do not present them as safe zero-cost verification unless the user has an existing build tree and asks to run them.
- For a new OpenMM feature, check that the API, implementation, serialization, Python exposure, documentation, and tests are all considered; OpenMM’s contribution guidance expects this breadth for nontrivial features.
- Prefer the Reference platform as the first correctness implementation, then add CPU and Common Compute/GPU implementations where the feature requires them.
- If a useful source helper is mentioned, keep it as reference-only unless it can run independent of an OpenMM checkout/build tree. The maintainer helpers for `ctest` selection and wrapper generation are intentionally not bundled as runtime scripts because they depend on generated build products and source-tree state.
