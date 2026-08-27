---
name: molecules-and-io
description: "Prepare ProLIF molecules, residues, and input files from RDKit,
  MDAnalysis, SDF, MOL2, PDBQT, PDB, and CIF/template-backed sources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProLIF Molecules and I/O

Use this sub-skill when an agent needs to turn chemistry or trajectory inputs into ProLIF `Molecule`, `Residue`, `ResidueId`, or `ResidueGroup` objects before interaction fingerprinting.

## Route Here For

- Creating `prolif.Molecule` objects with `Molecule.from_mda`, `Molecule.from_rdkit`, `sdf_supplier`, `mol2_supplier`, `pdbqt_supplier`, or `split_molecule`.
- Diagnosing residue labels, `chain` versus `segid` behavior, residue masks, and `ResidueId` string/index lookup.
- Preparing docking poses from SDF, MOL2, or PDBQT files before passing ligand pose iterables to fingerprint workflows.
- Preparing PDB/PDB-like structures, non-standard residues, CIF templates, and `MoleculeStandardizer` inputs.
- Running the bundled safe helper `scripts/inspect_inputs.py` to smoke-test installed package data or inspect user SDF/MOL2/PDBQT files.

## Do Not Use This For

- Choosing interaction classes, tuning interaction parameters, or water/implicit hydrogen interaction modes; use `../interactions/SKILL.md`.
- Running `Fingerprint.run`, `run_from_iterable`, `generate`, exports, pickles, or parallel execution; use `../fingerprints/SKILL.md`.
- Plotting residues, networks, barcodes, or 3D complexes; use `../visualization/SKILL.md`.
- Claiming or invoking a ProLIF CLI. ProLIF is used as a Python API; the helper in this skill is only a bundled diagnostic script.

## Quick Decision Map

1. **MDAnalysis Universe or AtomGroup**: use `Molecule.from_mda(obj, selection=None, use_segid=None, **converter_kwargs)`; verify the selection is non-empty and decide whether residue identity should use chain IDs or segment indices.
2. **RDKit molecule**: use `Molecule.from_rdkit(mol, resname="UNL", resnumber=1, chain="", use_segid=False)` when atoms may not already carry `AtomPDBResidueInfo`.
3. **SDF docking poses**: use `sdf_supplier(path, sanitize=True, resname=..., resnumber=..., chain=...)`; it behaves like a reusable sequence of `Molecule` poses.
4. **MOL2 docking poses**: use `mol2_supplier(path, cleanup_substructures=True, sanitize=True, ...)`; disable cleanup/sanitization only as a targeted troubleshooting step.
5. **PDBQT docking poses**: use `pdbqt_supplier(paths, template, converter_kwargs=None, ...)`; a template with correct bond orders and charges is mandatory.
6. **PDB or non-standard residues**: use RDKit/MDAnalysis loading plus `prolif.io.MoleculeStandardizer` with CIF or RDKit-molecule templates when bond orders, residue names, or protonation-sensitive residues need correction.

## References

- `references/api-reference.md` covers classes, constructor signatures, suppliers, standardization APIs, and residue selection.
- `references/workflows.md` provides input-preparation recipes for trajectories, docking, PDB, and residue splitting.
- `references/data-formats.md` explains SDF, MOL2, PDBQT, PDB, CIF/template, and package-data behavior.
- `references/troubleshooting.md` lists common conversion, labeling, hydrogen, standardization, and supplier failures.

## Safe Inspection Helper

Run from any project where ProLIF is installed:

```bash
python scripts/inspect_inputs.py
python scripts/inspect_inputs.py --sdf poses.sdf
python scripts/inspect_inputs.py --mol2 poses.mol2
python scripts/inspect_inputs.py --pdbqt pose1.pdbqt --pdbqt-template-smiles 'CCO'
```

The helper prints JSON, performs no destructive writes, and only reads user-specified files plus installed `prolif.datafiles` package data in no-argument mode.
