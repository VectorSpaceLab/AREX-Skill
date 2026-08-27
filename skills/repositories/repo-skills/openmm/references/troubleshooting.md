# Cross-cutting Troubleshooting

## Import or Package Failures

Symptoms:
- `ModuleNotFoundError: No module named 'openmm'`.
- `import openmm` succeeds in one shell but fails in another.
- `pip check` reports dependency conflicts.

Actions:
1. Verify the intended Python interpreter with `python -c "import sys; print(sys.executable)"`.
2. Run `python -m pip show openmm` or the package-manager equivalent in that same interpreter.
3. Run root `scripts/openmm_reference_smoke.py` after installation.
4. For source-tree wrapper builds, switch to `sub-skills/development-extensions/references/troubleshooting.md`; local builds require OpenMM libraries and include paths that ordinary package installs do not.

## Unit and Quantity Mistakes

Symptoms:
- Type errors involving incompatible units.
- Energies or temperatures that are off by large factors.
- Plain floats passed where OpenMM expects quantities.

Actions:
1. Import `openmm.unit` symbols and attach units to physical values: temperature, friction, timestep, cutoff, length, mass, pressure, and energy.
2. Keep counts, booleans, enum constants, and reporter intervals unitless.
3. Use tiny Reference-platform checks before long trajectories.

## Topology, Positions, and System Mismatch

Symptoms:
- `System` particle count differs from topology or positions.
- First `step()` fails after model editing.
- Reporter or minimization fails with inconsistent dimensions.

Actions:
1. Confirm `topology.getNumAtoms()`, `system.getNumParticles()`, and `len(positions)` agree.
2. If using `Modeller`, call `getTopology()` and `getPositions()` after every edit and before `createSystem()`.
3. Rebuild the `System` after topology-changing edits; do not reuse a system created for an older topology.
4. Use `force-fields-modeling` for template, water, ion, and parameterization problems.

## Platform and Plugin Failures

Symptoms:
- `There is no registered Platform called CUDA`.
- Platform creation fails with device or precision property errors.
- GPU works on one machine but not another.

Actions:
1. List installed platforms and property names before selecting one.
2. Use `platforms-performance` troubleshooting for CUDA/OpenCL/HIP package, driver, plugin directory, precision, and device-index diagnosis.
3. Prefer `Reference` or `CPU` fallback for correctness checks; do not block script validation on GPU availability unless the user requested GPU-specific behavior.

## NaNs, Exploding Energies, or Unstable Dynamics

Symptoms:
- `StateDataReporter` shows NaN energy or temperature.
- Simulation crashes after minimization or a few steps.
- Constraints fail.

Actions:
1. Minimize before dynamics and reduce timestep for diagnosis.
2. Check unit-bearing cutoff, temperature, friction, and timestep values.
3. Validate structure preparation: hydrogens, water model, periodic box, constraints, and force-field compatibility.
4. Run a 0-step or single-step energy check on `Reference` before switching to GPU.
5. For custom physics, inspect expression variables, exclusions, and parameter records in `custom-forces-integrators`.

## Source-tree Development Confusion

Symptoms:
- A user asks to run `ctest`, build wrappers, or edit C++ kernels from a package-only environment.
- Build failures mention CMake options, missing OpenMM libraries, generated wrapper files, or ABI/compiler problems.

Actions:
1. Route to `development-extensions`.
2. Confirm whether a compiled build tree exists before recommending native tests.
3. Treat source helper scripts as checkout/build-tree workflows, not as public package runtime scripts.
