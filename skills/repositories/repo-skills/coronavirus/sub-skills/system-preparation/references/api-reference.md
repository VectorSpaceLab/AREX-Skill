# Verified API and parameter reference

The runtime facts below were checked against the prepared inspection environment. They describe API usage, not a guarantee that any scientific parameter choice is valid for a particular structure.

## Modern imports

Prefer:

```python
from openmm import LangevinIntegrator, MonteCarloBarostat, XmlSerializer
from openmm import app, unit
```

The historical scripts use the legacy `simtk` namespace. New skill helpers use `openmm`; do not require the legacy namespace in a fresh environment.

## Core objects

- `app.PDBFile(filename)` loads topology and positions. A PDB topology and its positions must have the same atom count.
- `app.Modeller(topology, positions)` owns editable topology/coordinates. `addSolvent(forcefield, model='tip3p', padding=..., ionicStrength=...)` adds periodic solvent and ions; inspect the resulting atom count and box.
- `app.ForceField('amber14/protein.ff14SB.xml', 'amber14/tip3p.xml')` loads the project’s common protein/water templates. A missing template or unmatched residue is a data/force-field error, not a reason to guess.
- `ForceField.createSystem(topology, nonbondedMethod=app.PME, constraints=app.HBonds, removeCMMotion=False, hydrogenMass=...)` creates a `System`. `hydrogenMass` is optional and changes the dynamical model.
- `MonteCarloBarostat(pressure, temperature)` adds pressure control to a periodic system. Use explicit units.
- `LangevinIntegrator(temperature, collision_rate, timestep)` creates the baseline stochastic integrator. The verified current API also accepts an optional `splitting` argument; preserve a deliberate splitting string when continuing.
- `Context(system, integrator, platform=None)` binds the system and integrator to a platform. Set positions before minimization or stepping.
- `LocalEnergyMinimizer.minimize(context)` performs local minimization; inspect energy and positions afterward.
- `XmlSerializer.serialize(object)` and `XmlSerializer.deserialize(text)` handle supported OpenMM `System`, `Integrator`, and `State` XML. XML files are not interchangeable across unrelated systems.
- `app.PDBFile.writeFile(topology, positions, file, keepIds=True)` writes coordinates. Use `getState(getPositions=True, enforcePeriodicBox=True)` for a periodic equilibrated snapshot.

## Units and settings

Use `unit.kelvin`, `unit.atmospheres`, `unit.picoseconds`, `unit.femtoseconds`, `unit.angstroms`, `unit.millimolar`, and `unit.amu` rather than bare numbers. The product of `steps × iterations × timestep` is the simulated time. Set a random seed only when a reproducibility plan calls for it; stochastic trajectories remain hardware/platform sensitive.

PME requires a periodic box. Hydrogen-bond constraints do not by themselves make a 4–5 fs run stable. Hydrogen mass repartitioning, constraints, temperature, integrator splitting, and timestep must be reported together.

## Platform policy

Select `CPU` explicitly for required checks. Enumerate platforms before requesting `CUDA`. A platform being listed is not proof that a context can be created. In the verified environment CUDA context creation failed with `CUDA_ERROR_UNSUPPORTED_PTX_VERSION`; diagnose drivers/toolkit/PTX before treating CUDA as available. CPU is the complete substitute for this skill’s selected baseline, but not necessarily for performance or a GPU-specific production claim.
