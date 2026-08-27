# Protein–ligand preparation boundary

The project contains a protein–inhibitor workflow that combines OpenMM, OpenMMTools/SystemGenerator, OpenFF tooling, and ParmEd. This is an optional path because the ligand’s chemical identity and parameterization are input-specific. Do not silently fall back to a protein-only force field when a ligand is present.

## Required evidence before parameterization

Record:

- ligand residue name and a unique selection (chain, residue number, and atom count);
- formal charge, bond orders, stereochemistry, protonation/tautomer choice, and whether the coordinates are experimental or modeled;
- force-field/parameterization method and versions;
- any residue/atom renaming or bond-copy operation performed before parameterization;
- a validation result showing that the final topology contains the intended ligand and that all atoms have positions.

If any of these are unknown, stop and route the coordinate problem to [structure-curation](../../structure-curation/SKILL.md). A note that a ligand is “N3” or “inhibitor” is not sufficient chemical parameter evidence.

## Safe construction order

1. Validate and normalize the input structure without overwriting it.
2. Load the protein force field and choose a ligand parameter source that is installed and supported. SystemGenerator can combine small-molecule and protein force fields, but its option names and supported force fields are version-sensitive; inspect the live signature and documentation before use.
3. Confirm that the ligand template matches the residue and atom names. Fail closed on an unmatched template, missing bond, unsupported element, or ambiguous residue.
4. Create the combined system, then inspect force counts, atom counts, nonbonded parameters, and periodic-box behavior before adding solvent or dynamics.
5. Solvate, minimize, and run a tiny CPU smoke test. Save the parameterization/provenance record with the resulting XML bundle.

## Optional dependencies

OpenMM is required for the baseline. OpenMMForceFields/SystemGenerator, OpenFF Toolkit, ParmEd, and a compatible small-molecule toolkit are optional and must be checked independently. Their presence does not guarantee that a particular ligand can be parameterized. A missing package, unavailable force field, or toolkit conversion error is a clear prerequisite failure. Do not install packages or download force-field files from inside a runtime helper.

The generic `simulate_openmm_system.py` helper intentionally targets ordinary protein PDB input and does not invent ligand parameters. Use it for a complex only if the supplied topology/force-field path is already known to be complete; otherwise keep complex preparation as a separately reviewed workflow.

## Handoff

After successful complex construction, pass downstream the exact ligand identity, parameter source, atom/residue mapping, force-field files, charge model, serialized artifact names, and all warnings. Route target interpretation to [project-context](../../project-context/SKILL.md). This route does not validate binding, potency, or clinical relevance.
