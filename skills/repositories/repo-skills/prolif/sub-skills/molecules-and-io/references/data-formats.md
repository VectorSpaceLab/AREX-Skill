# ProLIF Input Data Formats

ProLIF molecule preparation combines RDKit, MDAnalysis, and ProLIF residue metadata. Choose the input path that preserves coordinates, bond orders, charges, hydrogens, and residue labels well enough for the intended fingerprint workflow.

## MDAnalysis Topologies and Trajectories

Use `Molecule.from_mda` for MDAnalysis `Universe` or `AtomGroup` inputs from trajectories, PDB/MOL2 files, or other MDAnalysis-supported formats.

Key behavior:

- `selection` can be a selection string when `obj` is a `Universe`.
- An empty selection raises an MDAnalysis `SelectionError` with an `AtomGroup is empty` message.
- Conversion forwards `**kwargs` to the MDAnalysis RDKit converter.
- `use_segid=None` auto-detects whether segment indices should replace chain IDs in ProLIF residue IDs.
- The resulting `Molecule` represents a single coordinate snapshot; iterate frames and rebuild molecules when preparing per-frame pose iterables manually.

Common converter kwargs:

- `NoImplicit=False` when implicit valence behavior needs to be relaxed for conversion.
- `force=True` in MDAnalysis conversion contexts where bond/order inference needs a forced path.
- Newer MDAnalysis inferrer objects, such as a template inferrer, when topology bond orders and charges need template-guided inference.

## RDKit Molecules

Use `Molecule.from_rdkit` for RDKit-loaded ligands, proteins, or residue fragments.

Key behavior:

- Direct `Molecule(rdmol)` expects residue monomer metadata to already exist.
- `Molecule.from_rdkit` patches missing `AtomPDBResidueInfo` using `resname`, `resnumber`, and `chain` defaults.
- If the first atom already has monomer info, ProLIF assumes the molecule is annotated and does not patch all atoms.
- Use `removeHs=False` when reading files if explicit hydrogens are needed for downstream interactions.

## SDF

Use `sdf_supplier(path, sanitize=True, **kwargs)` for docking poses or ligand ensembles in SDF.

Strengths:

- Usually preserves bond orders better than PDBQT.
- Supplier is reusable and supports `len()`, iteration, indexing, and slicing.
- RDKit reads with hydrogens preserved (`removeHs=False`).

Troubleshooting knobs:

- `sanitize=False` can bypass RDKit sanitization errors for inspection, but the resulting chemistry should be validated before fingerprinting.
- Use `resname`, `resnumber`, and `chain` kwargs to assign consistent ligand residue IDs.

## MOL2

Use `mol2_supplier(path, cleanup_substructures=True, sanitize=True, **kwargs)` for MOL2 pose files.

Behavior:

- Each `@<TRIPOS>MOLECULE` block is treated as one pose.
- Comment lines starting with `#` are ignored.
- Iteration and integer indexing are supported; slicing raises `NotImplementedError`.
- `cleanup_substructures=True` asks RDKit to clean up common substructures based on MOL2 atom types.

Troubleshooting knobs:

- Use `sanitize=False` if RDKit sanitization blocks exploratory inspection.
- Use `cleanup_substructures=False` if cleanup alters a structure unexpectedly.
- If residue parsing from MOL2 appends residue indices into residue names, parse and rewrite residue IDs with `ResidueId.from_string` before conversion.

## PDBQT

Use `pdbqt_supplier(paths, template, converter_kwargs=None, **kwargs)` for AutoDock Vina-style PDBQT files when SDF is unavailable.

Requirements:

- `paths` is an iterable of PDBQT file paths.
- Each PDBQT file should contain a single model; split multi-model Vina output before use.
- `template` is an RDKit molecule with correct bond orders and formal charges for the ligand.
- The template must exactly match the ligand in the PDBQT file after hydrogen handling.

Behavior:

- MDAnalysis reads the PDBQT file.
- ProLIF guesses elements from atom names and maps segids to chain IDs for conversion.
- The RDKit converter runs without inferring bond orders and charges.
- Bond orders are assigned from the template.
- Hydrogens present in PDBQT coordinates are restored after template assignment.

Cautions:

- PDBQT discards key chemistry; prefer SDF from a chemistry-aware docking/preparation pipeline when possible.
- Generic PDBQT-to-SDF conversion may create wrong bond orders or charges.
- Unexpected atom counts usually mean the template and PDBQT ligand do not match.

## PDB and PDB-Like Structures

PDB inputs are common for proteins and complexes but often need preparation.

Recommended approaches:

- Use MDAnalysis plus `Molecule.from_mda` for prepared proteins or trajectory-derived selections.
- Use RDKit `Chem.MolFromPDBFile(..., removeHs=False)` plus `Molecule.from_rdkit` when RDKit parses the structure correctly.
- Use `MoleculeStandardizer` when residue names and bond orders require template-backed correction.

Important preparation points:

- Explicit hydrogens are needed for many explicit-hydrogen interaction checks.
- If a PDB file includes bond records, avoid partial bond information; either provide all explicit bonds or let the parser infer all bonds.
- Non-standard residues, cofactors, ligands, and modified amino acids often need CIF or RDKit templates.
- Prepared PQR-like files should be converted to PDB before using ProLIF input paths.

## CIF, XML, and Template Standardization

ProLIF `prolif.io` provides standardization helpers for PDB/RDKit/ProLIF molecule inputs.

Template sources:

- `cif_template_reader(path)` reads a CIF file as a `gemmi.cif.Document`.
- `MoleculeStandardizer(templates=[...])` accepts CIF documents and `(residue_name, Chem.Mol)` templates.
- Built-in standard amino acid templates are always included as fallback.
- XML alternative-name mappings are used internally for residue/atom aliases in the standardization machinery.

Standardization behavior:

- Guesses forcefield family from residue names to standardize names such as histidine/cysteine variants.
- Converts residue names to ProLIF standard names where supported.
- Checks heavy atom counts against templates and warns on mismatches.
- Applies CIF or RDKit template engines to fix residue bond orders.
- Raises if a residue is not standard and no custom template is available.

CIF/RDKit template mismatch signs:

- Missing heavy atom warnings.
- `Could not apply template for residue ...` errors.
- Formal charge or aromaticity problems after standardization.
- Failure when a SMILES template represents a full molecule but ProLIF is standardizing a residue fragment split at peptide bonds.

## Package Data

Installed package data is available through `prolif.datafiles` and can be used for diagnostics:

- `TOP` and `TRAJ` for a protein/ligand trajectory example.
- `WATER_TOP` and `WATER_TRAJ` for water-containing examples.
- `datapath / "vina"` for SDF, MOL2, PDBQT, ligand, and receptor examples.
- `datapath / "molecule_standardizer/templates"` for CIF/XML standardization examples.

Do not make user workflows depend on the original source checkout. Package data is acceptable only when accessed from the installed `prolif` package.
