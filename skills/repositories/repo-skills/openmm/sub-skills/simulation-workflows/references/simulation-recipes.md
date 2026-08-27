# Simulation Recipes

This reference distills OpenMM application-layer examples and tests into reusable recipes. The canonical workflow is: load topology/positions, build a `System`, create an integrator, create `Simulation`, initialize the `Context`, minimize if appropriate, attach reporters, step, and save restart data.

## Core Simulation Skeleton

```python
from sys import stdout
from openmm.app import *
from openmm import *
from openmm.unit import *

# loader = ...                  # PDBFile, AmberInpcrdFile + AmberPrmtopFile, etc.
# topology = ...                # loader.topology or topology reader.topology
# positions = ...               # loader.positions, loader.getPositions(), or coordinate reader positions
# system = ...                  # ForceField.createSystem(...) or topology-reader.createSystem(...)
integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.004*picoseconds)
simulation = Simulation(topology, system, integrator)
simulation.context.setPositions(positions)
simulation.minimizeEnergy()
simulation.reporters.append(DCDReporter('trajectory.dcd', 1000))
simulation.reporters.append(StateDataReporter(stdout, 1000, step=True, potentialEnergy=True, temperature=True))
simulation.step(10000)
```

Important details:

- `Simulation` creates a `Context`; set positions before minimization or dynamics.
- `Simulation.step(steps)` requires an integer step count.
- `simulation.currentStep` reads/writes the Context step count; tests confirm time advances consistently with integrator step size.
- `Simulation.runForClockTime(time, checkpointFile=..., stateFile=..., checkpointInterval=...)` runs until wall-clock time and can write final or periodic restart files.
- Add custom forces or alter the `System` before constructing `Simulation`; after the Context exists, changing the Python `System` object will not update that Context.

## PDB or PDBx/mmCIF Inputs

Use PDB/PDBx when coordinates and topology come from structure files and the `System` is created from OpenMM force-field XML files.

```python
pdb = PDBFile('input.pdb')
# For mmCIF/PDBx, use: pdb = PDBxFile('input.cif')
forcefield = ForceField('amber19-all.xml', 'amber19/tip3pfb.xml')
system = forcefield.createSystem(
    pdb.topology,
    nonbondedMethod=PME,
    nonbondedCutoff=1*nanometer,
    constraints=HBonds,
)
integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.004*picoseconds)
simulation = Simulation(pdb.topology, system, integrator)
simulation.context.setPositions(pdb.positions)
```

Validation before stepping:

```python
assert system.getNumParticles() == pdb.topology.getNumAtoms()
state = simulation.context.getState(positions=True, energy=True)
print(state.getPotentialEnergy())
```

PDB loader behavior to remember:

- `PDBFile(file, extraParticleIdentifier='EP')` accepts a filename or open file object.
- `pdb.topology` and `pdb.positions` expose the first model; use `getNumFrames()` and `getPositions(frame=i)` for multi-frame PDB files.
- Periodic box vectors are read when present; PDB tests cover triclinic boxes, altloc handling, formal charges, extra particles, binary streams, and large files.
- PDB topology may not contain all atoms required by a force field; use the force-fields/modeling sub-skill for missing atoms, hydrogens, solvent, ions, or templates.

## Amber Inputs

Amber topology and coordinates are split between `prmtop` and `inpcrd`/restart files. The `prmtop` creates the `System`; coordinates come from the coordinate file.

```python
inpcrd = AmberInpcrdFile('input.inpcrd')
prmtop = AmberPrmtopFile('input.prmtop', periodicBoxVectors=inpcrd.boxVectors)
system = prmtop.createSystem(
    nonbondedMethod=PME,
    nonbondedCutoff=1*nanometer,
    constraints=HBonds,
)
integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.004*picoseconds)
simulation = Simulation(prmtop.topology, system, integrator)
simulation.context.setPositions(inpcrd.positions)
```

Amber caveats:

- For periodic systems, pass `periodicBoxVectors=inpcrd.boxVectors` to `AmberPrmtopFile`; periodic box information from `prmtop` is legacy and less preferred.
- Amber `prmtop` support targets new-style topology files; old-style files from very old Amber distributions are not supported.
- `AmberPrmtopFile.createSystem()` supports common nonbonded methods such as `NoCutoff`, `CutoffNonPeriodic`, `CutoffPeriodic`, `Ewald`, `PME`, and `LJPME`, plus constraints, implicit solvent options, hydrogen mass repartitioning, and center-of-mass motion removal.

## GROMACS Inputs

GROMACS coordinates and topology are split between `.gro` and `.top`. The `.top` may include other force-field files, so include directory handling matters.

```python
gro = GromacsGroFile('input.gro')
top = GromacsTopFile(
    'input.top',
    periodicBoxVectors=gro.getPeriodicBoxVectors(),
    includeDir='path/to/gromacs/top',
)
system = top.createSystem(
    nonbondedMethod=PME,
    nonbondedCutoff=1*nanometer,
    constraints=HBonds,
)
integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.004*picoseconds)
simulation = Simulation(top.topology, system, integrator)
simulation.context.setPositions(gro.positions)
```

GROMACS caveats:

- Pass `periodicBoxVectors=gro.getPeriodicBoxVectors()` for periodic systems.
- Use `includeDir` when the `.top` has `#include` files outside the current working directory or default GROMACS include location.
- The parser handles common preprocessor lines such as `#include`, `#define`, and conditional blocks; errors often mean the include path, macro choices, or topology file set is incomplete.

## CHARMM Inputs

CHARMM workflows combine a PSF topology, coordinates, and a parameter set. Coordinates may come from PDB, CHARMM coordinate, or restart files.

```python
psf = CharmmPsfFile('input.psf')
pdb = PDBFile('input.pdb')
params = CharmmParameterSet('topology.rtf', 'parameters.prm')
system = psf.createSystem(
    params,
    nonbondedMethod=NoCutoff,
    constraints=HBonds,
)
integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.004*picoseconds)
simulation = Simulation(psf.topology, system, integrator)
simulation.context.setPositions(pdb.positions)
```

CHARMM caveats:

- Load all required topology, parameter, stream, or related files into `CharmmParameterSet` before `psf.createSystem(...)`.
- For periodic systems, provide periodic box vectors or dimensions when loading the PSF or set them consistently before system creation.
- A PSF may be polarizable/Drude or include CHARMM-specific terms; route detailed Drude or parameter diagnosis to force-fields/modeling unless the immediate issue is simulation setup.

## Tinker Inputs

Tinker support uses `TinkerFiles` for `.xyz`, `.prm`, and optional `.key`-style inputs, primarily for AMOEBA.

```python
tinker = TinkerFiles('input.xyz', ['forcefield.prm', 'additional.prm'])
system = tinker.createSystem(
    nonbondedMethod=PME,
    nonbondedCutoff=0.7*nanometer,
    vdwCutoff=0.9*nanometer,
)
integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.001*picoseconds)
simulation = Simulation(tinker.topology, system, integrator)
simulation.context.setPositions(tinker.positions)
```

Tinker caveats:

- `TinkerFiles` supports AMOEBA-style force fields; non-AMOEBA Tinker force fields are not the expected path.
- Tinker examples use shorter timesteps such as `0.001*picoseconds` for polarizable systems.
- Keep cutoff choices compatible with the specific parameter set; model details belong to force-fields/modeling.

## Minimize, Initialize Velocities, and Step

Typical production-style start:

```python
simulation.context.setPositions(positions)
simulation.minimizeEnergy(tolerance=10*kilojoules_per_mole/nanometer, maxIterations=100)
simulation.context.setVelocitiesToTemperature(300*kelvin)
simulation.step(steps)
```

Use `setVelocitiesToTemperature()` when the script needs velocities for dynamics or for testing restart fidelity. If velocities are not set, many integrators can still proceed from zero/default velocities, but kinetic-energy and temperature reporting may be misleading at the start.

## Restart Recipes

Same-machine/same-platform exact continuation:

```python
simulation.saveCheckpoint('restart.chk')
# Later, after rebuilding an identical System, Integrator, Platform, and Simulation:
simulation.loadCheckpoint('restart.chk')
```

Portable approximate continuation:

```python
simulation.saveState('restart_state.xml')
# Later, after rebuilding a compatible System and Simulation:
simulation.loadState('restart_state.xml')
```

Reporter-managed restart files:

```python
simulation.reporters.append(CheckpointReporter('restart.chk', 1000))
simulation.reporters.append(CheckpointReporter('restart_state.xml', 1000, writeState=True))
```

Decision rule:

- Use checkpoints for exact continuation only when the `System`, platform, OpenMM version, and hardware/software context are effectively identical.
- Use serialized states when moving across hardware, switching platforms, or sharing a restart recipe; expect approximate continuation, not bitwise-identical trajectories.

## Small Validation Snippets

Bounded step-count smoke:

```python
simulation.step(10)
assert simulation.currentStep == 10
state = simulation.context.getState(positions=True, energy=True)
assert state.getPositions() is not None
print(state.getPotentialEnergy())
```

Reporter smoke with in-memory output:

```python
from io import StringIO
log = StringIO()
simulation.reporters.append(StateDataReporter(log, 1, step=True, potentialEnergy=True))
simulation.step(2)
assert '#"Step"' in log.getvalue() or 'Step' in log.getvalue()
```

Restart smoke:

```python
simulation.context.setVelocitiesToTemperature(300*kelvin)
simulation.saveState('state.xml')
simulation.step(2)
simulation.loadState('state.xml')
restored = simulation.context.getState(positions=True, velocities=True)
assert restored.getPositions() is not None
assert restored.getVelocities() is not None
```
