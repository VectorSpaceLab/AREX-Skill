# Molecules and I/O Troubleshooting

Use this guide when ProLIF input conversion, residue labels, pose suppliers, or molecule standardization fail before fingerprinting.

## RDKit or MDAnalysis Import Failure

Symptoms:

- `ModuleNotFoundError: No module named 'rdkit'`.
- `ModuleNotFoundError: No module named 'MDAnalysis'`.
- ProLIF imports but `Molecule.from_mda` or suppliers fail immediately.

Actions:

- Confirm the environment has ProLIF with the needed optional dependencies installed.
- Run `python scripts/inspect_inputs.py` to produce a JSON import/package-data smoke report.
- If only RDKit routes are needed, use `Molecule.from_rdkit` or SDF/MOL2 suppliers; if MDAnalysis is missing, avoid `Molecule.from_mda` and PDBQT supplier until the dependency is installed.
- If MDAnalysis is present but conversion fails, inspect the selected atom group and converter kwargs rather than assuming ProLIF has a separate CLI fallback.

## Empty MDAnalysis AtomGroup

Symptoms:

- `SelectionError: AtomGroup is empty, please check your selection`.
- Prepared ligand or protein molecule has zero residues.

Actions:

- Check `u.select_atoms(...).n_atoms` before conversion.
- Use `Molecule.from_mda(u, "selection text")` only when converting from a `Universe`; pass an `AtomGroup` directly if already selected.
- Verify residue names, segment IDs, chain IDs, and topology attributes in MDAnalysis before building the ProLIF molecule.
- For group-based selections, pass named groups to `select_atoms` consistently with MDAnalysis syntax.

## Missing or Unexpected Hydrogens

Symptoms:

- Hydrogen-bond-sensitive interactions are missing later.
- PDBQT poses have fewer hydrogens than expected.
- RDKit sanitization or valence errors mention implicit/explicit hydrogens.

Actions:

- Read RDKit files with `removeHs=False` when explicit hydrogens should be preserved.
- Prepare PDB proteins with explicit hydrogens unless the later interaction setup intentionally uses implicit-hydrogen modes.
- For PDBQT, remember the format omits key chemistry; ProLIF restores hydrogens present in the PDBQT coordinates after assigning bond orders from the template, but it does not invent a chemically complete prepared ligand.
- Use `NoImplicit=False` or a template inferrer only when the MDAnalysis RDKit converter needs those options for a known topology issue.
- Route implicit-hydrogen interaction choices to `../../interactions/SKILL.md` after molecules are prepared.

## Chain, Segment, and Residue Label Surprises

Symptoms:

- Residue labels look like `TIP34.3` instead of `TIP34.A`.
- Duplicate residue keys disappear or overwrite each other.
- Downstream lookups by string key raise `KeyError`.
- Chain IDs are blank, reused, or different from segment IDs.

Actions:

- Decide explicitly whether labels should use chain IDs or segment indices; pass `use_segid=True` or `False` to `Molecule.from_mda`, `Molecule.from_rdkit`, or `Molecule`.
- For multi-segment trajectories with reused chain IDs, prefer `use_segid=True` to keep residues distinct.
- Use `ResidueId` objects for unusual labels, especially if chain IDs include characters that string parsing may not represent cleanly.
- Inspect `mol.residues.name`, `mol.residues.number`, and `mol.residues.chain` arrays before building residue masks.
- Keep the same `use_segid` choice across ligand, protein, water, and later visualization inputs.

## ResidueGroup Selection Issues

Symptoms:

- Boolean masks return too many, too few, or zero residues.
- Python `and`/`or` operators fail on residue arrays.
- Integer lookup gives a residue but string lookup does not.

Actions:

- Build masks from `rg.name`, `rg.number`, and `rg.chain` arrays.
- Combine masks with `&`, `|`, `^`, and `~`, and wrap comparisons in parentheses.
- Use integer lookup for position in the sorted residue list; use string or `ResidueId` lookup for identity.
- Confirm missing chains are represented as `None`, not an empty string.

## SDF Supplier Returns Unexpected Poses

Symptoms:

- `len(sdf_supplier(...))` is not the expected number of poses.
- Iteration yields `None`-like failures from RDKit before ProLIF wrapping.
- Sanitization fails.

Actions:

- Run `inspect_inputs.py --sdf poses.sdf` and compare reported pose counts with the docking output.
- Retry `sdf_supplier(path, sanitize=False)` only for diagnosis or trusted input; inspect chemistry before fingerprinting.
- Assign explicit ligand residue metadata with `resname`, `resnumber`, and `chain` kwargs when labels matter downstream.
- Confirm the file is an SDF with separate records rather than a single molecule in another format.

## MOL2 Supplier Parsing or Sanitization Issues

Symptoms:

- Pose count differs from expected MOL2 blocks.
- Slicing raises `NotImplementedError`.
- RDKit reports valence/sanitization errors or unusual aromaticity.
- Residue information is embedded into residue names incorrectly.

Actions:

- Count `@<TRIPOS>MOLECULE` blocks and compare with `len(mol2_supplier(path))`.
- Use integer indexing or iteration; do not rely on slicing for MOL2 suppliers.
- Retry with `cleanup_substructures=False` if RDKit cleanup changes the molecule unexpectedly.
- Retry with `sanitize=False` only to inspect problematic input.
- If residue labels are malformed, parse intended labels with `ResidueId.from_string` and repair the MDAnalysis/RDKit residue metadata before conversion.

## PDBQT Supplier and Template Failures

Symptoms:

- PDBQT parsing fails in MDAnalysis.
- `AssignBondOrdersFromTemplate` or sanitization fails.
- Pose atom counts do not match the template.
- Multiple Vina poses in one file produce only one or no usable molecule.

Actions:

- Split multi-model PDBQT into one model per file before using `pdbqt_supplier`.
- Prefer SDF output from a chemistry-aware preparation tool when available.
- Provide an RDKit template with the exact ligand chemistry, bond orders, and formal charges.
- Remove `NoImplicit` from custom `converter_kwargs`; ProLIF's PDBQT supplier manages this internally.
- Inspect each PDBQT path independently; one bad pose file can fail an otherwise correct sequence.
- Avoid generic PDBQT-to-SDF conversion as evidence that bond orders and charges are correct.

## PDB Parsing and Bond-Order Problems

Symptoms:

- Prepared protein conversion fails or produces implausible chemistry.
- Hydrogen bonds, pi interactions, or salt bridges are missing later.
- MDAnalysis does not infer bonds because partial PDB bond records are present.

Actions:

- Ensure the PDB is prepared with explicit hydrogens where required.
- Avoid partial bond records; provide all explicit bonds or none.
- Use MDAnalysis for protein PDB parsing when residue metadata is more reliable there than direct RDKit parsing.
- For ligand PDB files, use a template, SMILES, SDF, or MOL2 source to recover bond orders before `Molecule.from_rdkit`.
- Use `MoleculeStandardizer` when non-standard residue names or bond orders need correction.

## CIF/XML Template Mismatches

Symptoms:

- `Residue {'ACE'} is not a standard residue or not in the templates`.
- `Could not apply template for residue ...`.
- Heavy atom count warnings.
- Aromaticity, formal charge, or bond-order mismatch after standardization.

Actions:

- Provide custom templates for every non-standard residue, ligand, cap, modified amino acid, or cofactor.
- Use `cif_template_reader("RES.cif")` for CIF templates or `(resname, Chem.Mol)` for RDKit molecule templates.
- Match template residue names to the residue names after ProLIF forcefield/name standardization.
- For SMILES/RDKit templates, represent the residue fragment ProLIF standardizes, not necessarily the isolated full molecule from a database.
- If a residue is missing heavy atoms, fix the input structure rather than suppressing the warning for production workflows.

## MoleculeStandardizer Side Effects

Symptoms:

- A `Molecule` passed to `MoleculeStandardizer` has changed residue names or bond orders afterward.
- Split molecules keep standardized residue information.

Actions:

- Treat `MoleculeStandardizer(existing_molecule)` as in-place for ProLIF `Molecule` inputs.
- Deep-copy or reload the input if the original labels/bond orders must be preserved for comparison.
- Use `split_molecule` after standardization when ligand/protein/water child molecules should preserve corrected residue objects.

## When to Route Elsewhere

- If molecule objects are prepared but no interactions are found, route to `../../interactions/SKILL.md` for interaction class, parameter, and hydrogen-mode decisions.
- If the issue is `Fingerprint.run`, result DataFrames, pickles, parallel execution, or `RunRequiredError`, route to `../../fingerprints/SKILL.md`.
- If the issue is `display_residues`, 2D networks, barcode plots, or 3D views, route to `../../visualization/SKILL.md`.
