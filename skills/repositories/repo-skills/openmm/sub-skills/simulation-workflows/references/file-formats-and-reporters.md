# File Formats and Reporters

Use this reference to pick matching OpenMM application-layer loaders and reporters, and to avoid common output and restart mistakes.

## Loader Pairing Matrix

| Source format | Topology source | Position source | System source | Key setup detail |
| --- | --- | --- | --- | --- |
| PDB | `PDBFile(...).topology` | `PDBFile(...).positions` or `getPositions(frame=...)` | `ForceField(...).createSystem(pdb.topology, ...)` | PDB/PDBx topology must match the force-field templates. |
| PDBx/mmCIF | `PDBxFile(...).topology` | `PDBxFile(...).positions` | `ForceField(...).createSystem(pdbx.topology, ...)` | Substitute `PDBxFile` for `PDBFile`; model-editing issues route elsewhere. |
| Amber | `AmberPrmtopFile(...).topology` | `AmberInpcrdFile(...).positions` | `AmberPrmtopFile.createSystem(...)` | For periodic systems, pass `periodicBoxVectors=inpcrd.boxVectors`. |
| GROMACS | `GromacsTopFile(...).topology` | `GromacsGroFile(...).positions` | `GromacsTopFile.createSystem(...)` | Pass box vectors from `.gro`; set `includeDir` for external includes. |
| CHARMM | `CharmmPsfFile(...).topology` | `PDBFile`, `CharmmCrdFile`, or `CharmmRstFile` positions | `CharmmPsfFile.createSystem(params, ...)` | Load every required parameter/topology/stream file into `CharmmParameterSet`. |
| Tinker | `TinkerFiles(...).topology` | `TinkerFiles(...).positions` | `TinkerFiles.createSystem(...)` | Intended for AMOEBA-style Tinker force-field data. |

## Reporter Choices

`Simulation.reporters` is a normal Python list. Append reporter objects before calling `step()` or `runForClockTime()`.

### `DCDReporter`

Signature: `DCDReporter(file, reportInterval, append=False, enforcePeriodicBox=None, atomSubset=None)`

Use for binary coordinate trajectories.

- `reportInterval` is in integration steps.
- `append=True` appends to an existing DCD; otherwise the file is newly written.
- `enforcePeriodicBox=None` lets OpenMM decide from the system's periodic boundary conditions. Set `True` or `False` when you need explicit wrapping behavior.
- `atomSubset` is a zero-indexed atom-index list; when used, only those atoms are written.

### `StateDataReporter`

Signature: `StateDataReporter(file, reportInterval, step=False, time=False, potentialEnergy=False, kineticEnergy=False, totalEnergy=False, temperature=False, volume=False, density=False, progress=False, remainingTime=False, speed=False, elapsedTime=False, separator=',', systemMass=None, totalSteps=None, append=False)`

Use for CSV-like logs of thermodynamic and progress data.

- Pass a filename or a file-like object such as `stdout` or `StringIO`.
- `progress=True` or `remainingTime=True` requires `totalSteps`.
- `.gz` and `.bz2` filename extensions are compressed when Python supports them; appending to compressed output is not supported.
- `append=True` suppresses the header and appends to existing plain-text output.
- Temperature reporting uses an integrator-provided `computeSystemTemperature()` when available, otherwise derives temperature from kinetic energy and degrees of freedom.

### `CheckpointReporter`

Signature: `CheckpointReporter(file, reportInterval, writeState=False)`

Use for periodic restart files.

- With `writeState=False`, it writes binary checkpoints via `simulation.saveCheckpoint()`.
- With `writeState=True`, it writes XML serialized states via `simulation.saveState()`.
- It overwrites the target with the latest checkpoint/state rather than keeping every frame.
- For file objects, use binary mode for checkpoints and text mode for states; reporter tests confirm file objects are truncated to the latest content.

### PDB/PDBx Reporters

Use `PDBReporter` or `PDBxReporter` for readable structure snapshots. They are useful for short smoke outputs and interoperability, but DCD is more typical for longer trajectories.

## Reporter Scheduling and Wrapping

During `Simulation.step()`, OpenMM asks each reporter for its next report via `describeNextReport(simulation)`. Modern reporters return a dictionary containing:

- `steps`: number of steps until the next report.
- `include`: state components needed, such as `positions`, `velocities`, `forces`, `energy`, `parameters`, `parameterDerivatives`, or `integratorParameters`.
- `periodic`: whether positions should be wrapped into the periodic box; `None` lets OpenMM infer from the `System`.

OpenMM groups reporters that need wrapped and unwrapped positions, calls `Context.getState(...)`, and passes the resulting `State` to each reporter. If a custom reporter is needed, route complex design to custom-forces-integrators, but the minimal contract is `describeNextReport()` plus `report(simulation, state)`.

## Checkpoint vs State

| Restart artifact | API | Strength | Limitation |
| --- | --- | --- | --- |
| Binary checkpoint | `saveCheckpoint()` / `loadCheckpoint()` | Captures internal Context data and can resume very closely or exactly. | Specific to the same `System`, platform, OpenMM version, and hardware/software context. |
| XML State | `saveState()` / `loadState()` | Portable across platforms/hardware when the rebuilt `System` is compatible. | Stores public state only; do not expect identical future trajectories. |
| `Simulation(..., state='file.xml')` | Constructor argument | Initializes a new `Simulation` from a serialized `State` file. | Requires compatible topology/system/integrator setup. |

When diagnosing restart failures after hardware or platform changes, switch from checkpoints to XML states before suspecting model setup.

## Output Path Practices

- For examples and tests, write outputs under a temporary or caller-provided working directory, not beside imported package files.
- Avoid long runs just to prove a workflow; 0-10 steps with a concrete assertion is enough for smoke validation.
- Delete or overwrite intentionally. `CheckpointReporter` overwrites by design; `DCDReporter(append=True)` and `StateDataReporter(append=True)` require compatible existing files.
- If no output appears, check whether `reportInterval` exceeds the number of steps run.

## Unit-Aware Parameters

OpenMM Python expects physical quantities for most dimensional values. Use unit expressions instead of bare floats:

```python
temperature = 300*kelvin
friction = 1/picosecond
timestep = 0.002*picoseconds
cutoff = 1*nanometer
```

Safe exceptions are integer step counts, booleans, enum-like options (`PME`, `HBonds`, `NoCutoff`), filenames, and file-like objects.
