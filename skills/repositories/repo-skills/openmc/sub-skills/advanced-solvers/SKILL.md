---
name: advanced-solvers
description: "Route OpenMC's native-backed solvers, variance-reduction controls,
  C API lifecycle, and optional geometry or physics integrations with explicit
  build and verification limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Advanced solvers and native integrations

Use this route when the task involves random ray, CMFD, weight windows or
weight-window generation, `openmc.lib`, a C/C++ build or CTest, MPI/DAGMC/
libMesh/NCrystal, photon or charged-particle transport, or restart/specialized
native interfaces.

## Route

1. **Check the native boundary first.** Run
   [`scripts/check_native_features.py`](scripts/check_native_features.py) with
   `--help` or no arguments for a safe diagnostic; add explicit
   `--executable`, `--library`, and/or `--build-dir` paths when inspecting a
   particular build. Read
   [`references/native-and-optional-builds.md`](references/native-and-optional-builds.md)
   for CMake flags, dependency gates, and safe native test selection.
2. **Choose the solver workflow.** Read
   [`references/advanced-api-reference.md`](references/advanced-api-reference.md)
   for random-ray settings and restrictions, CMFD lifecycle, weight-window
   shapes/generation, and `openmc.lib` sequencing.
3. **Diagnose instead of inferring support.** Read
   [`references/troubleshooting.md`](references/troubleshooting.md) whenever a
   shared library, feature flag, optional dependency, data prerequisite, or
   solver input is missing. A configured option or Python class is not proof
   that the native capability is available in the current build.
4. **Verify at the smallest feasible level.** Keep the base `import openmc`
   gate separate from the executable and `libopenmc` gates. Prefer import and
   XML/API smoke checks first, then a bounded native test only when the
   executable/shared library and required data are present. Do not download
   external data or claim an unavailable optional backend.

## Boundaries

- Route routine materials, geometry, sources, and settings construction to
  [`../model-geometry/SKILL.md`](../model-geometry/SKILL.md); this route only
  covers advanced solver-specific settings and native constraints.
- Route ordinary statepoint, tally, track, and result analysis to
  [`../tallies-results/SKILL.md`](../tallies-results/SKILL.md).
- Route package installation, executable orchestration, MPI/OpenMP environment
  setup, and cross-section path setup to
  [`../setup-runtime/SKILL.md`](../setup-runtime/SKILL.md).
- Route nuclear-data conversion, MGXS production, and depletion semantics to
  [`../nuclear-data-depletion/SKILL.md`](../nuclear-data-depletion/SKILL.md).
- `openmc.lib` is an optional native binding: base `import openmc` can succeed
  while `import openmc.lib` fails because the packaged `libopenmc` shared
  library has not been built or is not loadable. Treat that as a native
  prerequisite failure, not as proof that the Python package is unusable.
- Do not promise GPU/CUDA support. The documented build contract is CPU/C++17
  with optional OpenMP and explicitly gated native integrations.

## References and bundled checks

- [`references/advanced-api-reference.md`](references/advanced-api-reference.md)
  contains the detailed API contracts and solver-specific constraints.
- [`references/native-and-optional-builds.md`](references/native-and-optional-builds.md)
  contains build, CTest, feature-detection, and optional-backend boundaries.
- [`references/troubleshooting.md`](references/troubleshooting.md) contains
  actionable recovery and verification limits.
- [`scripts/check_native_features.py`](scripts/check_native_features.py) only
  inspects supplied paths, CMake cache values, and (when explicitly supplied)
  the feature-query symbol in a shared library. It never builds, downloads,
  writes, or changes the environment.
