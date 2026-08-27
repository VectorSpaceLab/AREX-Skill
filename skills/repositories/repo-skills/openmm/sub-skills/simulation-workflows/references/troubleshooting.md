# Simulation Workflow Troubleshooting

Use this guide for failures in application-layer simulation scripts. If the failure is primarily force-field template/model preparation, platform/hardware, custom forces/integrators, or C++ extension work, route to the relevant sibling sub-skill.

## File Loading and Format Pairing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` or loader cannot locate included files | Relative paths are evaluated from the process working directory; GROMACS/CHARMM inputs often depend on included files. | Use caller-provided absolute or working-directory-relative paths; for GROMACS pass `includeDir`; for CHARMM load all parameter/stream files. |
| Amber periodic system has missing or wrong box | `AmberPrmtopFile` was created without coordinate-file box vectors. | Load `AmberInpcrdFile` first and pass `periodicBoxVectors=inpcrd.boxVectors` to `AmberPrmtopFile`. |
| GROMACS `.top` fails on `#include` | Include directory or topology bundle is incomplete. | Supply `includeDir` and ensure local includes are available beside the `.top` or in the include directory. |
| CHARMM `MissingParameter` or PSF parse error | Parameter set incomplete, wrong file order, or incompatible PSF/parameter family. | Load the full `CharmmParameterSet`; escalate detailed parameter/model fixes to force-fields-modeling. |
| Tinker system creation fails for force-field terms | Input uses unsupported or non-AMOEBA Tinker force-field features. | Confirm the files are AMOEBA-style and include all required parameter/key data; route parameter support gaps to force-fields-modeling. |

## Topology, Positions, and System Mismatches

Before the first step, check:

```python
assert system.getNumParticles() == topology.getNumAtoms()
simulation.context.setPositions(positions)
state = simulation.context.getState(positions=True, energy=True)
print(state.getPotentialEnergy())
```

Common causes:

- Coordinates and topology are from different files or preprocessing stages.
- PDB/PDBx lacks hydrogens, solvent, ions, terminal atoms, extra particles, or residues expected by the force field.
- The force field creates virtual sites or extra particles that require model-editing preparation.
- Periodic box vectors are missing or inconsistent with the selected nonbonded method.

Route missing atoms, residue templates, solvation, and force-field XML decisions to force-fields-modeling.

## Unit Mistakes

OpenMM dimensional arguments should carry units. Examples:

- Good: `300*kelvin`, `1/picosecond`, `0.004*picoseconds`, `1*nanometer`.
- Risky: `300`, `1`, `0.004`, `1.0` where a dimensional value is expected.

If a script silently uses an unexpected scale, audit every integrator, cutoff, tolerance, pressure, temperature, and time argument. Integer step counts such as `simulation.step(10)` stay unitless.

## No Velocities or Odd Temperature Output

Symptoms include zero or surprising kinetic energy/temperature at the start.

Fix:

```python
simulation.context.setPositions(positions)
simulation.minimizeEnergy()
simulation.context.setVelocitiesToTemperature(300*kelvin)
```

Set velocities before production dynamics when temperature, kinetic energy, or restart fidelity matters. If continuing from a checkpoint or state that already includes velocities, do not overwrite them unless intentionally reinitializing.

## Reporter Output Problems

| Symptom | Fix |
| --- | --- |
| No trajectory/log file appears | Ensure the run reaches at least one `reportInterval`; a 10-step smoke with interval 1000 writes nothing. |
| `StateDataReporter` progress/remaining-time error | Provide `totalSteps` when `progress=True` or `remainingTime=True`. |
| Appending fails for compressed logs | Do not use `append=True` with `.gz` or `.bz2` state-data output. |
| DCD append gives unusable trajectory | Append only to compatible DCD files from the same topology and timestep/reporting convention. |
| Periodic molecules appear split or unexpectedly wrapped | Set reporter `enforcePeriodicBox=True` or `False` explicitly instead of relying on `None`. |

## Checkpoint Load Fails After Platform or Hardware Change

Binary checkpoints are Context-specific. They depend on the identical `System`, platform, OpenMM version, and often hardware/software details. If loading a checkpoint fails after moving between GPU/CPU machines, changing CUDA/OpenCL/HIP settings, or upgrading OpenMM, switch to serialized state restart:

```python
# During the original run
simulation.saveState('restart_state.xml')

# During restart after rebuilding a compatible Simulation
simulation.loadState('restart_state.xml')
```

Use `CheckpointReporter('restart_state.xml', interval, writeState=True)` when periodic portable restarts are more important than exact same-platform continuation.

## NaN or Infinite Energies

Immediate triage:

1. Run zero or one step on the `Reference` platform if available to separate model issues from accelerated platform issues.
2. Get energy before dynamics: `simulation.context.getState(energy=True).getPotentialEnergy()`.
3. Minimize with a bounded `maxIterations` and inspect whether energy improves.
4. Check units, positions, periodic box size, cutoff, constraints, and whether atom positions overlap.
5. If the issue appears only on CUDA/OpenCL/HIP/CPU, route to platforms-performance.

Common workflow-level causes include missing minimization, wrong coordinate/topology pairing, bare floats used where units were required, bad periodic boxes, or a timestep too large for the model.

## Long Runs in Examples or Tests

Repository examples often use production-like step counts such as 10,000 steps and write trajectory files. For a coding-agent smoke test, reduce to 0-10 steps, shorten reporter intervals to 1-5, and assert something concrete. Do not run expensive benchmarks as functional checks; platform benchmarking belongs to platforms-performance.

## Platform Errors

This sub-skill can pass `Platform.getPlatformByName('Reference')` or `Platform.getPlatformByName('CPU')` for a deterministic smoke, but device selection, precision modes, properties, CUDA/OpenCL/HIP driver errors, and performance tuning belong to platforms-performance.
