# OpenMM workflow contracts

## Inputs and outputs

The reusable baseline accepts a validated protein PDB and an empty or new output directory. It produces a solvated PDB, a minimized PDB, an equilibrated PDB, `system.xml`, `integrator.xml`, and `state.xml`. Filenames are stable within the selected output directory, but a caller should treat the directory as an artifact bundle and record the command-line parameters beside it.

The continuation helper accepts four artifacts from one preparation: an equilibrated PDB, its serialized `system.xml`, its serialized `state.xml`, and a new output directory. It produces a continuation PDB plus new serialized system, integrator, and state files. A PDB is used for topology and coordinates; the XML state supplies velocities and periodic-box state when present. Do not combine XML from unrelated runs.

## Baseline apo workflow

1. **Curate and validate.** Remove unintended waters or chains, decide protonation/capping externally where required, and validate that atom positions match topology. Preserve a copy of the input.
2. **Load and solvate.** Load with `openmm.app.PDBFile`; create an `openmm.app.Modeller`; add TIP3P solvent with a stated padding and ionic strength. The helper defaults are intentionally modest and should be recorded.
3. **Create the system.** Use an Amber protein force field and TIP3P water, PME nonbonded interactions, hydrogen-bond constraints, and optional hydrogen mass repartitioning only when the structure and timestep plan support it.
4. **Add pressure control.** A Monte Carlo barostat is appropriate for periodic NPT equilibration; state pressure and temperature explicitly. Do not treat adding a barostat as proof that an ensemble is scientifically appropriate for every project.
5. **Minimize.** Create a context, set positions, minimize, and write the minimized coordinates. Inspect initial/final energy and whether the context reports periodic box vectors.
6. **Equilibrate briefly.** Use a Langevin integrator, normally 2 fs for the baseline. `steps × iterations × timestep` is the simulated time; the helper’s bounded defaults are for smoke checks, not production.
7. **Serialize.** Save positions, velocities, energy, forces, and periodic state as `state.xml`; serialize the `System` after applying the current periodic box vectors and save the integrator. Write an equilibrated PDB with periodic wrapping enabled.

The historical project recipes used a 2 fs preparation phase, often with 4 amu hydrogen mass and a longer continuation phase. Those values are conventions to reproduce and review, not universal defaults. A 4 amu mass can alter dynamics and must be disclosed.

## Longer-timestep continuation

Use the continuation helper only after the 2 fs artifact has been inspected. Load the serialized system and state, deserialize the integrator when possible, or construct a new Langevin integrator only when the user explicitly chooses new temperature/collision settings. Set the requested timestep and splitting, apply the state to a context, and run a bounded continuation. A 4 or 5 fs timestep requires a compatible hydrogen-mass/constraint strategy and should be validated on the actual system; a CPU one-step success is not a stability proof.

Keep the original timestep and mass in the provenance record. Compare energies, temperature, box vectors, and coordinate sanity before and after continuation. Do not concatenate outputs or call a system “production-ready” solely because XML serialization succeeded.

## Optional complex workflow

Protein–ligand preparation is a separate branch. Validate the ligand’s residue identity, atom names, bonds, formal charge, and stereochemistry; choose a parameterization source; then use a verified SystemGenerator/OpenFF/GAFF path. Read [ligand-complex.md](ligand-complex.md). If ligand chemistry is ambiguous, stop before solvation and route back to structure-curation.

## Bounded-run policy

For an initial smoke test, use one iteration and one or a few integration steps. Increase only after the input, force field, topology, and output bundle are inspected. The bundled helper refuses excessive step/iteration products by default. A production run requires a separately reviewed command, hardware plan, checkpoint strategy, and scientific rationale; this skill deliberately does not automate that workflow.
