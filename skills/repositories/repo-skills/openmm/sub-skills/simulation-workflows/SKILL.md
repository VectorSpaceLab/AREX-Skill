---
name: simulation-workflows
description: "Set up and run practical OpenMM Python application-layer
  simulations from PDB, PDBx/mmCIF, Amber, GROMACS, CHARMM, and Tinker inputs,
  including Simulation setup, integrators, reporters, minimization, stepping,
  checkpoints, portable state restarts, and small validation smokes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT, GPL, LGPL
---

# Simulation Workflows

Use this sub-skill when the task is to write, adapt, debug, or sanity-check an OpenMM Python application-layer simulation script. It owns the workflow that loads input files, creates or receives a `System`, creates a `Simulation`, initializes the `Context`, attaches reporters, minimizes, runs steps, and saves or resumes progress.

## Route Here For

- Creating short scripts around `Simulation(topology, system, integrator, platform=None, platformProperties=None, state=None)`.
- Loading coordinates/topologies from `PDBFile`, `PDBxFile`, Amber `prmtop`/`inpcrd`, GROMACS `top`/`gro`, CHARMM `psf` plus coordinate and parameter files, or Tinker `xyz`/parameter files.
- Choosing ordinary application-layer integrators such as `LangevinMiddleIntegrator`, `LangevinIntegrator`, or `VerletIntegrator` for simple production or smoke runs.
- Adding `DCDReporter`, `StateDataReporter`, `CheckpointReporter`, `PDBReporter`, or `PDBxReporter` output.
- Using `minimizeEnergy()`, `step()`, `runForClockTime()`, `saveCheckpoint()`, `loadCheckpoint()`, `saveState()`, and `loadState()`.
- Writing quick Reference/CPU smoke checks that avoid long trajectories and verify positions, energy, step count, or reporter output.

## Use Other Sub-skills For

- Force-field XML choice, `Modeller`, solvation, ions, missing atoms, templates, and model editing: `../force-fields-modeling/SKILL.md`.
- Custom expression forces, custom reporters beyond basic app-layer reporting, advanced alchemical systems, or custom integrators: `../custom-forces-integrators/SKILL.md`.
- CUDA/OpenCL/HIP/CPU/Reference platform selection, precision, device properties, performance, and platform-specific errors: `../platforms-performance/SKILL.md`.
- C++ APIs, plugins, serialization internals, or source-level extension work: `../development-extensions/SKILL.md`.

## Working References

- Start with `references/simulation-recipes.md` for PDB, Amber, GROMACS, CHARMM, Tinker, smoke, minimization, stepping, and restart recipes.
- Use `references/file-formats-and-reporters.md` for loader pairing, reporter options, checkpoint/state differences, and validation snippets.
- Use `references/troubleshooting.md` when a script fails to load files, builds a bad `System`, produces NaNs, writes no output, or cannot resume from a checkpoint.
- Run `scripts/minimal_reference_smoke.py` to verify that OpenMM imports, units, `Context`, `Simulation`, minimization, stepping, and serialization work on the Reference platform without external data files.

## Default Safe Pattern

1. Import from `openmm.app`, `openmm`, and `openmm.unit`; use explicit unit-bearing quantities such as `300*kelvin`, `1/picosecond`, and `0.002*picoseconds`.
2. Load topology and positions from matching input files; pass periodic box vectors from the coordinate file when the topology format needs them.
3. Create or receive a `System` before constructing `Simulation`; changes to `System` after `Simulation` creation do not affect the existing `Context`.
4. Create an integrator, then `Simulation(topology, system, integrator, ...)`; set positions and, for dynamics or restart-sensitive tests, set velocities explicitly.
5. Minimize before dynamics unless the workflow is intentionally evaluating unminimized input.
6. Attach reporters before `step()`; use short intervals and small step counts for smoke tests.
7. Prefer `saveState()`/`loadState()` for portable restarts across hardware/platforms; use checkpoints only for same-system, same-platform, same-version continuation.

## Acceptance Checks

- The script imports `openmm`, `openmm.app`, and `openmm.unit` without relying on the OpenMM source checkout.
- Every physical value has units or is intentionally unitless where OpenMM expects a count, boolean, or enum.
- The topology, positions, and system particle count are consistent before the first `step()`.
- Reporters write to intentional paths or file-like objects, and progress reporters specify `totalSteps`.
- Smoke runs are bounded, usually 0-10 steps on `Reference` or `CPU`, and check a concrete invariant such as `currentStep`, finite energy, positions present, or a restart restoring positions.
