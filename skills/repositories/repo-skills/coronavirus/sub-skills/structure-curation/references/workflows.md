# Curation workflows

## Validate first

Run `validate_pdb.py --input-pdb INPUT` without an output path. Record chains, residue IDs, atom count, coordinate count, and duplicate-name warnings. Add `--require-chain` for each chain that must be present and `--reject-duplicate-atom-names` when downstream parameterization requires unique names.

## Select or truncate

Use `select_chains_and_residues.py` with a new `--output-pdb` and one or more selectors. `--chain A` keeps all atoms in chain A. `--residue-range A:14-306` keeps residues in the inclusive numeric interval in chain A. Selectors combine as a union: a chain selector keeps the whole chain, while a range selector keeps only that range. Run `--dry-run` first; it prints selected chains/residues and atom count without writing.

The helper preserves the selected topology graph and positions and does not assume historical names such as “RBD.” For insertion codes or non-numeric residue IDs, stop and make a selector that explicitly handles the records with a reviewed tool; do not coerce IDs.

## Normalize a residue

After validation, invoke `normalize_ligand_residue.py` with `--chain-id`, `--residue-name`, and `--residue-id`. The selected residue must be unique. The helper changes the residue name and makes duplicate atom names deterministic while rebuilding the same atom/bond graph. It does not add hydrogens, infer bond orders, assign charges, or create force-field parameters. Revalidate and then perform the chemistry-specific handoff.

## External preparation handoff

If a structure requires PyMOL extraction, Maestro protonation/capping, PDBFixer repair, OpenFF conversion, or another external operation:

1. save the pre-tool PDB and tool/version/settings;
2. perform only the intended transformation;
3. validate chain/residue identity, atom/position counts, termini, hydrogens, and ligand chemistry afterward;
4. route to system preparation only once the resulting topology is explicit.

Unavailable Maestro/PyMOL is not a reason to silently claim the structure is protonated or capped. State the blocked step and use a CPU OpenMM run only after an approved replacement workflow.
