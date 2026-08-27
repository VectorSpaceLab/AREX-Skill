# Molecule Troubleshooting

Use this guide to diagnose common OpenFF molecule construction, IO, conversion, conformer, charge, matching, and visualization failures.

## Undefined Stereochemistry

Symptoms:

- `UndefinedStereochemistryError` from `Molecule.from_smiles()`, `Molecule.from_file()`, `Molecule.from_rdkit()`, or `Molecule.from_openeye()`.
- A non-isomeric SMILES works only with `allow_undefined_stereo=True`.
- Different backends disagree about whether a center or bond is stereogenic.

What to do:

1. Prefer a fully stereospecified input such as isomeric SMILES.
2. If ambiguity is acceptable, retry with `allow_undefined_stereo=True` and state that conformer generation or parameterization may be chemically ambiguous.
3. Use `enumerate_stereoisomers(undefined_only=True, max_isomers=...)` to propose explicit alternatives.
4. Use `is_isomorphic_with(..., atom_stereochemistry_matching=False, bond_stereochemistry_matching=False)` only for deliberate non-stereo validation.

## Mapped SMILES and Atom Ordering Problems

Symptoms:

- Atom order does not match atom-map labels after `Molecule.from_smiles()`.
- `from_mapped_smiles()` raises a parsing or remap error.
- SDF round-trip appears chemically identical but atom-index arrays no longer align.

What to do:

1. Use `Molecule.from_mapped_smiles()` for order-sensitive work.
2. Ensure every atom, including hydrogens, has exactly one 1-indexed atom-map label.
3. Remember that Python atom indices are 0-indexed, while mapped SMILES labels are typically 1-indexed.
4. Validate round-trips with both `to_smiles(mapped=True)` and `is_isomorphic_with()`.

## Missing RDKit or OpenEye

Symptoms:

- `ToolkitUnavailableException` when calling `from_rdkit()`, `to_rdkit()`, `from_openeye()`, `to_openeye()`, conformer generation, or toolkit-specific charge methods.
- OpenEye methods fail because OpenEye is not installed or licensed.
- A file format is unsupported even though examples mention it with another backend.

What to do:

1. Check the current registry and wrapper availability before promising a backend-specific path.
2. In a minimal environment, expect RDKit and BuiltIn wrappers if live inspection reported them; OpenEye, AmberTools, and NAGL may be absent.
3. Use RDKit-backed paths for `SDF`, `MOL`, `SMI`, conformers, `mmff94`, and `gasteiger` when RDKit is available.
4. Use BuiltIn `zeros` or `formal_charge` charges when cheminformatics charge methods are unavailable.
5. Route installation, wrapper precedence, and registry customization to `../toolkit-backends/SKILL.md`.

## Unsupported or Unsafe File Formats

Symptoms:

- `UnsupportedFileTypeError` for `XYZ` input.
- `NotImplementedError` says no toolkit can read `MOL2` or `PDB`.
- `MoleculeParseError` says no molecule could be read from a file.
- `to_file()` raises `ValueError` for an unavailable write format.

What to do:

1. Prefer `SDF` for small-molecule graph-preserving read/write workflows.
2. Provide `file_format` explicitly for file-like objects or unusual suffixes.
3. Do not parse `XYZ` into `Molecule`; it lacks bond order, formal charge, aromaticity, and stereochemistry.
4. Do not rely on bare `PDB` for small-molecule graph perception. Use `Molecule.from_pdb_and_smiles()` only for legacy molecule-level alignment, or route PDB systems to `../topology-and-systems/SKILL.md`.
5. For `MOL2` with RDKit-only environments, convert to `SDF` upstream or use a backend that supports the needed `MOL2` flavor.

## Partial Charge Method Failures

Symptoms:

- `ChargeMethodUnavailableError` for `am1bcc`, `am1bccelf10`, `am1-mulliken`, NAGL model names, or other methods.
- `IncorrectNumConformersError` or `IncorrectNumConformersWarning` when supplying `use_conformers`.
- Charges do not sum exactly to formal charge when normalization is disabled.
- Large molecule charge assignment is slow or warns.

What to do:

1. Inspect `molecule.get_available_charge_methods()` in the active environment.
2. Use `gasteiger` or `mmff94` with RDKit, and `zeros` or `formal_charge` with BuiltIn, when only those wrappers are available.
3. Use OpenEye, AmberTools, or NAGL methods only when those wrappers are installed and available.
4. Let `assign_partial_charges()` generate conformers internally unless the task requires supplied conformers.
5. Keep `normalize_partial_charges=True` unless exact backend output is required.
6. Route force-field-level charge sourcing and SMIRNOFF charge handler behavior to `../smirnoff-force-fields/SKILL.md`.

## Conformer Generation Errors

Symptoms:

- `ConformerGenerationError` from a backend.
- `molecule.n_conformers` is lower than requested.
- `visualize(backend="nglview")` raises `MissingConformersError`.
- Charge assignment complains about conformer count.

What to do:

1. Try a small `n_conformers` first, such as `1` or `3`.
2. Verify stereochemistry and formal charges before conformer generation.
3. Avoid expensive conformer generation for large molecules in smoke tests.
4. Use `molecule.generate_conformers(n_conformers=0, clear_existing=True)` to clear stale conformers.
5. For NGLView visualization, generate at least one conformer and ensure `nglview` is installed.

## PDB and Hierarchy Confusion

Symptoms:

- A user asks to load a protein, water box, ion set, ligand complex, multiple chains, or PDB hierarchy as a `Molecule`.
- `from_pdb_and_smiles()` warns that it is deprecated.
- Polymer PDB loading fails with multiple molecules, noncanonical residues, missing chemistry, or unsupported topology.

What to do:

1. Keep this sub-skill to molecule-level `from_pdb_and_smiles()` and `from_polymer_pdb()` triage.
2. Explain that PDB coordinates do not reliably encode small-molecule bond order, formal charge, aromaticity, or stereochemistry.
3. Route general PDB loading, `Topology.from_pdb()`, hierarchy iteration, and multi-component systems to `../topology-and-systems/SKILL.md`.
4. If a single ligand PDB must be used, require a matching SMILES and validate with `is_isomorphic_with()` after construction.

## Visualization Failures

Symptoms:

- `MissingOptionalDependencyError("nglview")` or missing RDKit/OpenEye visualization backend.
- `MissingConformersError` for `backend="nglview"`.
- Visualization code works in a notebook but not in a plain script.

What to do:

1. Use `backend="rdkit"` for 2D notebook depiction when RDKit is available.
2. Generate conformers before `backend="nglview"`.
3. Treat visualization output as an interactive display object, not a serialization or validation artifact.
4. For non-notebook checks, use `to_smiles()`, `to_file()`, `is_isomorphic_with()`, and `to_networkx()` instead.

## Isomorphism or SMARTS Surprises

Symptoms:

- Two molecules have different canonical SMILES strings but should represent the same graph.
- SMARTS match counts differ across toolkits.
- Isomorphism fails because of stereochemistry, formal charge, or bond order differences.

What to do:

1. Use `is_isomorphic_with()` rather than string equality for cross-route validation.
2. Keep strict matching defaults for chemistry-sensitive checks.
3. Relax `atom_stereochemistry_matching` or `bond_stereochemistry_matching` only when the task explicitly ignores stereochemistry.
4. Add atom-map tags to SMARTS queries to make returned match tuple ordering clear.
5. Use `unique=True` when reporting human-facing match counts.
