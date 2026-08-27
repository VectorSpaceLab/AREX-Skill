# Structure Analysis Workflows

These workflows are self-contained patterns for Biotite structure analysis. They avoid network access, plotting side effects, and source-checkout dependencies.

## Build a Tiny Structure In Memory

1. Import `numpy as np` and `biotite.structure as struc`.
2. Create an `AtomArray(n)` or individual `Atom` objects and combine them with `struc.array()`.
3. Set `coord` to a float array with shape `(n, 3)`.
4. Fill mandatory annotations: `chain_id`, `res_id`, `res_name`, `atom_name`, `element`, and usually `hetero`.
5. Add task-specific annotations with `add_annotation()` or `set_annotation()`.
6. Use NumPy boolean masks for selections, and call `.copy()` before mutating a slice independently.

Minimal pattern:

```python
import numpy as np
import biotite.structure as struc

atoms = struc.AtomArray(3)
atoms.coord = np.array([[0.0, 0.0, 0.0], [1.5, 0.0, 0.0], [2.5, 1.0, 0.0]])
atoms.chain_id[:] = "A"
atoms.res_id[:] = [1, 1, 1]
atoms.res_name[:] = "GLY"
atoms.atom_name[:] = ["N", "CA", "C"]
atoms.element[:] = ["N", "C", "C"]
```

## Filter and Summarize Atoms

1. Compose chemistry filters with annotation masks, for example `struc.filter_amino_acids(atoms) & (atoms.atom_name == "CA")`.
2. Apply masks as `atoms[mask]` for arrays or `stack[..., mask]` for stacks.
3. Use residue or chain helpers to aggregate values: `apply_residue_wise()`, `get_residue_starts()`, `residue_iter()`, `apply_chain_wise()`.
4. For alternate locations loaded with `altloc="all"`, use `filter_first_altloc()` or `filter_highest_occupancy_altloc()` after ensuring `altloc_id` and, for occupancy selection, `occupancy` are present.
5. For nonstandard residues, compare `filter_amino_acids()` with `filter_canonical_amino_acids()` or use `info.full_name()`/`info.link_type()` to inspect residue identity.

Use this pattern to avoid accidentally treating solvent, ions, ligands, or alternate conformers as polymer atoms.

## Edit Coordinates and Annotations Safely

1. Mutate coordinate and annotation arrays directly: `atoms.coord += shift`, `atoms.chain_id[:] = "B"`.
2. Do not assign annotations on a temporary filtered subarray unless you intentionally discard the result.
3. Use `atoms.copy()` before editing a slice that should not share state with the source.
4. Use `set_annotation(name, values)` only when `len(values) == atoms.array_length()`.
5. For string annotations, let `set_annotation()` widen dtypes when values exceed default widths.

Correct annotation edit:

```python
mask = atoms.element == "C"
atoms.atom_name[mask] = ["CA", "C"]
```

Avoid this when you intend to mutate the original:

```python
atoms[mask].atom_name = ["CA", "C"]
```

## Add and Maintain Bonds

1. Prefer parser-provided bonds when file IO was configured with `include_bonds=True`; route parser details to `../../file-io-formats/`.
2. If bonds are missing, choose `struc.connect_via_residue_names(atoms)` for CCD-template chemistry or `struc.connect_via_distances(atoms, periodic=...)` for geometry-based inference.
3. Attach bonds as `atoms.bonds = bond_list`; the atom count must match `atoms.array_length()`.
4. When filtering atoms, attached `BondList` indices are remapped automatically.
5. To edit a bond list broadly, convert with `as_array()`, filter or modify the transient array, then create a new `BondList`.
6. Use `find_connected()` for connected components and `find_rotatable_bonds()` when bond orders are meaningful.

Tiny in-memory bond pattern:

```python
bond_array = np.array([[0, 1, struc.BondType.SINGLE], [1, 2, struc.BondType.SINGLE]])
atoms.bonds = struc.BondList(atoms.array_length(), bond_array)
```

## Measure Geometry

1. Use `struc.distance()`, `angle()`, and `dihedral()` for atoms, arrays, stacks, or raw coordinates.
2. Use index-based functions such as `index_distance()` when you already have atom-index pairs or tuples.
3. Expect NumPy broadcasting: array-to-atom, stack-to-array, and raw coordinate combinations are valid when shapes align.
4. Use `dihedral_backbone()` and `dihedral_side_chain()` for protein torsions; use nucleotide-specific dihedral functions for nucleic acids.
5. Treat undefined torsions as expected `NaN` values at termini, incomplete residues, or nonmatching residue types.

## Superimpose and Compare Structures

1. Ensure fixed and mobile structures have corresponding atoms in the same order, or derive corresponding anchors first.
2. Choose a mask such as `atoms.atom_name == "CA"` when only representative atoms should drive fitting.
3. Call `fitted, transform = struc.superimpose(fixed, mobile, atom_mask=mask)`.
4. Compare with `struc.rmsd(fixed, fitted)`; for trajectories use `struc.rmsd(reference_frame, trajectory)`.
5. Reuse `transform.apply(other_atoms)` when another structure should receive the same transformation.
6. For outliers, use `superimpose_without_outliers()`; for homologs with deletions, use `superimpose_homologs()`.

For structure-alphabet-guided homolog fitting, encode peptide chains with `strucalph.to_3di()`, align 3Di sequences with sequence alignment APIs, map aligned residue anchors back to `CA` atoms, then call `superimpose()` on those anchors.

## Analyze Trajectories After Loading

1. Use the file-IO sub-skill to load trajectory coordinates with a template `AtomArray` because trajectory formats often store coordinates only.
2. Work with an `AtomArrayStack` where annotations are shared and coordinates have shape `(m, n, 3)`.
3. Superimpose frames before comparing them: `trajectory, _ = struc.superimpose(trajectory[0], trajectory)`.
4. Filter atoms with `trajectory[..., trajectory.atom_name == "CA"]` or another stable mask.
5. Compute `struc.rmsd(trajectory[0], trajectory)` and `struc.rmsf(struc.average(trajectory), trajectory)`.
6. Preserve or validate `trajectory.box` before periodic calculations.

## Use Periodic Boxes

1. Build or validate a box with `vectors_from_unitcell()`; angles must be radians.
2. Assign `array.box` as shape `(3, 3)` or `stack.box` as shape `(m, 3, 3)`.
3. Use PBC-aware functions with `periodic=True` or an explicit `box=` parameter when supported.
4. Use `move_inside_box()` to wrap coordinates and `remove_pbc()` to unwrap fragmented molecules before non-PBC measurements.
5. Remember that coordinates and box vectors are both in Å.

## Compute SASA and Secondary Structure

1. Filter to the relevant polymer or molecule before computing SASA or secondary structure.
2. Use `struc.sasa(atoms, vdw_radii="ProtOr")` when hydrogens are absent, as in many crystal structures.
3. Use `vdw_radii="Single"` when explicit hydrogens are resolved and element annotations are reliable.
4. Aggregate atom-level SASA to residues with `struc.apply_residue_wise(atoms, atom_sasa, np.nansum)`.
5. Use `struc.annotate_sse(atom_array)` for Biotite's built-in estimate returning `a`, `b`, and `c`.
6. Use the database/application sub-skill for DSSP because it requires an external application wrapper and different setup assumptions.

## Find Hydrogen Bonds and Contacts

1. Attach or infer bonds before calling `struc.hbond()` when donor hydrogens and bonded relationships matter.
2. For stacks, expect `triplets, mask = struc.hbond(stack)` and summarize with `struc.hbond_frequency(mask)`.
3. Use `selection1`, `selection2`, and `selection1_type` to constrain donor/acceptor search boundaries.
4. Use `acceptor_elements=("O", "N")` or similar when matching another tool's chemistry assumptions.
5. Set `periodic=True` only when a valid box is present.
6. Treat missing-bond warnings as a prompt to add `atoms.bonds`, not as proof the structure is unusable.

## Analyze Nucleic Acids

1. Filter nucleotides with `filter_nucleotides()` or `filter_canonical_nucleotides()` depending on whether modified bases should remain.
2. Use `map_nucleotide()` to inspect modified bases and incomplete residues.
3. Use `base_pairs()`, `base_pairs_edge()`, `base_pairs_glycosidic_bond()`, and `base_stacking()` for geometric base-pair analysis.
4. Use `dot_bracket_from_structure()` to summarize secondary structure; handle pseudoknots explicitly with `pseudoknots()` if the downstream notation cannot represent crossing pairs.
5. Expect warnings and missing interactions when rings or hydrogen-bond atoms are incomplete.

## Use Chemical Component Information

1. Use `info.residue(res_name)` to generate a small molecule or residue template for local testing, connectivity checks, or rotatable bond inspection.
2. Use `info.bonds_in_residue()`, `info.bond_type()`, and `struc.connect_via_residue_names()` when CCD residue names are reliable.
3. Use `info.vdw_radius_single()` or `info.vdw_radius_protor()` to debug SASA/radius issues.
4. Use `info.one_letter_code()` and `struc.to_sequence()` only after residue names and polymer filtering look correct.

## Source Example Adaptation Notes

Biotite's structure examples cover contacts, molecules, nucleotides, modeling, alphabets, proteins, and miscellaneous workflows. In this generated runtime skill:

- Safe local geometry, filtering, bond, and contact ideas are distilled into this reference and `../scripts/structure_geometry_smoke.py`.
- Network examples that fetch RCSB or remote files are reference-only; route future database fetching to `../../database-application/` and file parsing to `../../file-io-formats/`.
- Plotting or visualization examples are reference-only; route graphics, PyMOL, RDKit, OpenMM, and display concerns to `../../interfaces-visualization/`.
- External-data MD, docking, and application examples are reference-only because they require downloaded trajectories, optional binaries, or external packages.
- No runtime instruction in this sub-skill requires opening the original examples, tests, or repository checkout.
