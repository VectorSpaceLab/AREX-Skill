---
name: openmm
description: "Use OpenMM for molecular simulation workflows, force-field/model
  preparation, custom forces/integrators, platform/performance diagnostics, and
  maintainer extension work."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT, GPL, LGPL
---

# OpenMM

Use this repo skill when a task involves OpenMM, the molecular simulation toolkit exposed through `openmm`, `openmm.app`, `openmm.unit`, C++ APIs, runtime platforms, plugins, or the OpenMM source tree.

## Quick Start

- Install OpenMM from the public package channel appropriate for the user's environment; for Python workflows, verify `import openmm, openmm.app, openmm.unit` before writing larger scripts.
- Run `scripts/openmm_reference_smoke.py` for a checkout-independent Reference-platform sanity check that constructs a tiny system, evaluates a `Context`, and reports available platforms.
- Read `references/environment-and-platform-facts.md` for package/version caveats, install extras, platform expectations, and safe verification commands.
- Read `references/openmm-capability-map.md` when routing a broad request across sub-skills.
- Read `references/troubleshooting.md` first for cross-cutting install/import, unit, platform, and workflow failures.

## Route by User Task

- Use `sub-skills/simulation-workflows/SKILL.md` for Python application-layer simulations: loading PDB/mmCIF, Amber, GROMACS, CHARMM, or Tinker inputs; creating `Simulation`; attaching reporters; minimizing; stepping; and checkpoint or XML-state restarts.
- Use `sub-skills/force-fields-modeling/SKILL.md` for `ForceField`, `Modeller`, bundled XML files, `createSystem()`, missing hydrogens, solvent/ions, membranes, residue template errors, parameterized file formats, and ffxml authoring.
- Use `sub-skills/custom-forces-integrators/SKILL.md` for `Custom*Force` classes, expression syntax, runtime parameters, tabulated functions, force groups, `CustomIntegrator`, and serialization-aware custom systems.
- Use `sub-skills/platforms-performance/SKILL.md` for `Reference`, `CPU`, `CUDA`, `OpenCL`, or `HIP` platform selection, `platformProperties`, precision/device/thread choices, plugin availability, benchmark interpretation, and performance diagnostics.
- Use `sub-skills/development-extensions/SKILL.md` for changing OpenMM itself: C++ API/implementation work, kernels, plugins, serialization proxies, Python wrapper generation, CMake builds, and focused native tests.

## Core Concepts

- `openmm.System` stores particles, constraints, forces, virtual sites, and periodic box information; most simulation errors trace back to mismatch among `System`, topology, positions, and force parameters.
- `openmm.Context` binds a `System`, an `Integrator`, and a `Platform`; changes to a `System` after `Context` creation usually require updating parameters in context or reinitializing.
- `openmm.app.Simulation(topology, system, integrator, platform=None, platformProperties=None, state=None)` is the high-level Python workflow object for most application scripts.
- `openmm.app.ForceField(*files)` creates `System` objects from topologies and bundled or custom XML; use `Modeller(topology, positions)` before `createSystem()` when the structure needs hydrogens, solvent, ions, membranes, or extra particles.
- Physical quantities should carry `openmm.unit` units, for example `300*kelvin`, `1/picosecond`, `0.004*picoseconds`, and `1*nanometer`.
- The `Reference` platform is slow but excellent for correctness smokes; `CPU`, `CUDA`, `OpenCL`, and `HIP` need environment-specific package/plugin/runtime support.

## Safe Working Pattern

1. Clarify whether the user is running a simulation, preparing a model, defining custom physics, diagnosing hardware/performance, or modifying OpenMM internals.
2. Route to the narrowest sub-skill and use its nearest references/scripts rather than writing a large one-off script from memory.
3. Start with a bounded smoke: import OpenMM, list platforms, build or load a tiny system, run 0-10 steps or one energy evaluation, and assert finite output.
4. Escalate to production settings only after topology, positions, `System`, integrator, reporter paths, and platform choice are validated.
5. For source-tree development, separate build-required/native tests from package-level Python smokes; do not assume a user has a compiled OpenMM build tree.

## Bundled Runtime Assets

- `references/repo-provenance.md` records the source commit, dirty state, package version facts, and evidence paths used to create this skill.
- `references/openmm-capability-map.md` maps natural OpenMM requests to sub-skill owners, evidence, and validation signals.
- `references/environment-and-platform-facts.md` summarizes install/import/platform facts verified during skill creation without exposing private environment paths.
- `references/troubleshooting.md` covers cross-cutting failures and points to sub-skill-specific troubleshooting files.
- `scripts/openmm_reference_smoke.py` is a safe, checkout-independent Reference-platform smoke test.

## Boundaries

- This skill is self-contained runtime guidance. It does not require the original OpenMM checkout to be available.
- Do not link future agents to original repo docs, examples, tests, scripts, or absolute local paths; use the bundled references and scripts here.
- Treat benchmarks, GPU runs, source builds, `ctest`, and wrapper generation as optional, environment-dependent workflows that require explicit user context.
