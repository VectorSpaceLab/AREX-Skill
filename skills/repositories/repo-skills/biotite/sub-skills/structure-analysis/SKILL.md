---
name: structure-analysis
description: "Use Biotite structure analysis APIs for AtomArray construction,
  filtering, bonds, geometry, superposition, contacts, trajectories, and
  structural alphabets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Biotite Structure Analysis

Use this sub-skill when the task centers on in-memory molecular structures with `biotite.structure`: constructing or editing `Atom`, `AtomArray`, or `AtomArrayStack` objects; filtering atoms/residues/chains; managing bonds/connectivity; measuring geometry; superimposing structures; computing RMSD/RMSF, SASA, hydrogen bonds, base pairs, pseudoknots, secondary structure, periodic boxes, or trajectory summaries.

For file parser classes, PDB/PDBx/BinaryCIF conversion, or trajectory file reading/writing, route to `../file-io-formats/`. For RCSB/Entrez/AlphaFold fetching or external applications such as DSSP, route to `../database-application/`. For PyMOL/RDKit/OpenMM or plotting/export-oriented tasks, route to `../interfaces-visualization/`.

## Start Here

- Read `references/api-reference.md` for the main classes, annotations, filters, geometry, connectivity, and structure-info helpers.
- Read `references/workflows.md` for task recipes covering construction, filtering, bonds, superposition, trajectories, nucleic acids, and structural alphabets.
- Read `references/troubleshooting.md` when coordinates, annotations, bonds, altlocs, periodic boxes, secondary structure, or residue names behave unexpectedly.
- Run `scripts/structure_geometry_smoke.py --help` to inspect the bundled smoke helper, or run it directly for a tiny local AtomArray geometry check.

## Core Routing Rules

- Prefer `import biotite.structure as struc` and `import biotite.structure.info as info` for structure work.
- Treat coordinates, distances, surface areas, boxes, and trajectory lengths as Å-based unless a caller explicitly converted units.
- Keep parser decisions out of this sub-skill: load structures with the file-IO sub-skill, then return here for in-memory analysis.
- Keep database and visualization side effects out of structure recipes unless another sub-skill owns that step.

## Evidence Base

This sub-skill distills the Biotite structure tutorial pages for atoms, filtering, bonds, editing, measurement, trajectories, and structural alphabets; source modules under `src/biotite/structure/`; structure examples under `doc/examples/scripts/structure/`; and behavior checks from `tests/structure/test_atoms.py`, `test_filter.py`, `test_geometry.py`, `test_superimpose.py`, `test_hbond.py`, `test_sasa.py`, `test_connect.py`, and `test_basepairs.py`.
