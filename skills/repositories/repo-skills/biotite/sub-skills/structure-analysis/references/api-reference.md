# Structure Analysis API Reference

Use this reference for in-memory structure work after data has already been loaded or constructed. Parser classes and file-format options belong in the sibling `file-io-formats` sub-skill.

## Imports and Units

| Need | Import or object | Notes |
| --- | --- | --- |
| Core structure APIs | `import biotite.structure as struc` | Exposes `Atom`, `AtomArray`, `AtomArrayStack`, filters, geometry, bonds, trajectories, contacts, and comparison helpers. |
| Chemical component facts | `import biotite.structure.info as info` | Use for residue templates, masses, radii, CCD-derived bonds, residue names, and atom/residue metadata. |
| Structural alphabets | `import biotite.structure.alphabet as strucalph` | Use for 3Di/protein-block style residue encodings before sequence-style alignment. |
| Array operations | `import numpy as np` | Biotite structure attributes are NumPy arrays; most filtering and editing is NumPy-style. |

Biotite structure lengths are in Å. Coordinates use shape `(n, 3)` for an `AtomArray` and `(m, n, 3)` for an `AtomArrayStack`.

## Atom Containers

| Object or helper | Use | Key expectations |
| --- | --- | --- |
| `struc.Atom(coord, ...)` | Single atom with scalar annotations | Coordinates are converted to a NumPy float vector of length 3. Missing mandatory annotations get defaults. |
| `struc.AtomArray(length)` | Allocate one model with `length` atoms | Mandatory annotation arrays and `coord` are initialized with zero/default values. Set arrays with length `n`. |
| `struc.AtomArrayStack(depth, length)` or `struc.stack([...])` | Multiple frames/models sharing annotations | Coordinate shape is `(m, n, 3)`. All stacked arrays must have compatible annotations. |
| `struc.array(iterable_of_atoms)` | Build an `AtomArray` from `Atom` objects | Carries compatible custom annotations from atoms into annotation arrays. |
| `array.copy()` / `stack.copy()` | Avoid view-backed edits | Slices may share underlying arrays; copy before independent mutation. |
| `struc.concatenate([...])`, `array_a + array_b` | Combine structures with matching dimensionality | Associated bonds are remapped when possible. |

Mandatory annotations are `chain_id`, `res_id`, `ins_code`, `res_name`, `hetero`, `atom_name`, and `element`. Common optional annotations include `atom_id`, `b_factor`, `occupancy`, `charge`, `sym_id`, and `entity_id`.

## Editing and Annotation Arrays

| Task | API pattern | Notes |
| --- | --- | --- |
| Edit coordinates | `array.coord[...] = values` | Assign a floating NumPy-compatible shape `(n, 3)` or selected rows. |
| Edit existing annotation | `array.chain_id[:] = "A"`; `array.res_id = np.array([...])` | Apply the index to the annotation array, not to a temporary subarray. |
| Add annotation | `array.add_annotation("foo", dtype=bool)` | Initializes a new annotation array with type-specific defaults. |
| Set custom annotation | `array.set_annotation("score", values)` | `values` length must match `array.array_length()`. Biotite widens string dtype when needed. |
| Read annotation generically | `array.get_annotation("chain_id")` | Useful when the annotation name is dynamic. |
| Delete or replace atoms | `del array[i]`; `array[i] = atom` | Tests cover both array and stack deletion/replacement. |
| Print compactly | `struc.set_print_limits(...)` | Reset with `struc.set_print_limits()` after custom limits. |

## Indexing and Iteration

| Pattern | Result |
| --- | --- |
| `array[0]` | One `Atom`. |
| `array[mask]`, `array[[0, 2]]`, `array[10:20]` | Filtered `AtomArray`. |
| `stack[0]` | One `AtomArray` frame. |
| `stack[:10]` | `AtomArrayStack` with selected frames. |
| `stack[:, mask]` | All frames with selected atoms. |
| `stack[frame_index, atom_index]` | Reduced according to the integer dimensions used. |
| `array.array_length()` / `stack.stack_depth()` | Atom count and frame count. |

## Filters

| Filter | Use |
| --- | --- |
| `struc.filter_amino_acids(array)` / `filter_canonical_amino_acids()` | Select amino-acid residues, optionally canonical only. |
| `struc.filter_nucleotides(array)` / `filter_canonical_nucleotides()` | Select nucleic-acid residues, optionally canonical only. |
| `struc.filter_carbohydrates(array)`, `filter_solvent(array)`, `filter_monoatomic_ions(array)`, `filter_heavy(array)` | Common chemistry-based selections. |
| `struc.filter_peptide_backbone(array)`, `filter_phosphate_backbone(array)` | Backbone atom selections. |
| `struc.filter_polymer(array, min_size=..., pol_type="p"|"n"|"carb")` | Select polymer chains by type and minimum size. |
| `struc.filter_intersection(a, b)` | Keep atoms from one array that match another by annotation identity. |
| `struc.filter_first_altloc(array, altloc_id)` / `filter_highest_occupancy_altloc(array, altloc_id, occupancy)` | Resolve alternate locations after loading `altloc="all"` and required fields. |
| `struc.filter_linear_bond_continuity(array)` | Keep atoms participating in a linear bonded path. |

Filter functions return boolean masks with atom-array length. Apply them as `array[mask]` or `stack[..., mask]`.

## Residues and Chains

| API | Use |
| --- | --- |
| `struc.get_residue_starts(array)` / `get_chain_starts(array)` | Start indices for residue or chain segments. |
| `struc.get_residue_count(array)` / `get_chain_count(array)` | Segment counts. |
| `struc.get_residues(array)` / `get_chains(array)` | Residue or chain IDs/names. |
| `struc.residue_iter(array)` / `chain_iter(array)` | Iterate residue or chain subarrays. |
| `struc.apply_residue_wise(array, values, func)` / `apply_chain_wise(...)` | Aggregate atom-level values per residue or chain. |
| `struc.spread_residue_wise(array, values)` / `spread_chain_wise(...)` | Broadcast segment values back to atoms. |
| `struc.get_residue_masks(array, starts)` | Boolean masks for selected residues. |

## Bonds and Connectivity

| API | Use | Notes |
| --- | --- | --- |
| `struc.BondList(atom_count, bonds=None)` | Store pairs or triples of bonded atom indices | Triples include a `BondType` enum value; omitted types become `BondType.ANY`. |
| `array.bonds = bond_list` | Attach bonds to an array or stack | Bond atom count must equal `array.array_length()`. `array.bonds` is `None` when absent. |
| `bond_list.as_array()` | Get transient `[[i, j, type], ...]` array | Modify this transient array, then create a new `BondList`. |
| `bond_list.get_bonds(atom_index)` | Get bonded partners and bond types for one atom | Useful for local connectivity checks. |
| `struc.connect_via_residue_names(array)` | Infer canonical bonds from residue templates | Based on CCD residue definitions; good for standard residues and ligands with known names. |
| `struc.connect_via_distances(array, periodic=False)` | Infer bonds from geometry | Useful fallback; may miss or overcall in unusual chemistry. |
| `struc.find_connected(bond_list, root, as_mask=False)` | Connected component from one atom | Use to split molecules/chains by bond graph. |
| `struc.find_rotatable_bonds(bond_list)` | Single-bond rotors | Requires meaningful bond orders. |

Some functions work without bonds but warn and infer candidates from distances. Attach a `BondList` when contact chemistry matters.

## Geometry, Transformations, and Comparison

| API | Use |
| --- | --- |
| `struc.coord(obj)` | Extract coordinate arrays from atoms/arrays/stacks or normalize coordinates. |
| `struc.displacement(a, b)`, `distance(a, b)`, `angle(a, b, c)`, `dihedral(a, b, c, d)` | Broadcasted geometric measurements over atoms, arrays, stacks, or raw coordinates. |
| `struc.index_distance(sample, indices)`, `index_angle(...)`, `index_dihedral(...)` | Measure by integer atom-index tuples. |
| `struc.centroid(atoms_or_coord)` | Coordinate centroid. |
| `struc.translate(atoms, vector)`, `rotate(atoms, angles)`, `rotate_centered(...)`, `rotate_about_axis(...)` | Return transformed copies for arrays, stacks, or raw coordinates. |
| `struc.orient_principal_components(atoms)` | Align coordinates by principal axes. |
| `struc.superimpose(fixed, mobile, atom_mask=None)` | Fit `mobile` to `fixed`; returns `(fitted, transformation)`. Fixed and mobile atom order/count must correspond. |
| `struc.superimpose_without_outliers(...)` | Fit while excluding outliers; returns anchors. |
| `struc.superimpose_homologs(fixed, mobile)` | Find homologous residue anchors before fitting. |
| `struc.rmsd(reference, subject)`, `struc.rmspd(...)`, `struc.rmsf(reference, trajectory)`, `struc.average(stack)` | Structure comparison and trajectory summaries. |

`superimpose()` accepts an optional boolean atom mask, commonly `mobile.atom_name == "CA"`, and preserves input type/shape where possible.

## Surface, Contacts, Secondary Structure, and Nucleic Acids

| API | Use | Notes |
| --- | --- | --- |
| `struc.sasa(array, vdw_radii="ProtOr"|"Single", ...)` | Atom-wise solvent accessible surface area | Use `ProtOr` for missing hydrogens; `Single` when explicit hydrogens are present. |
| `struc.hbond(array_or_stack, selection1=None, selection2=None, ...)` | Hydrogen bond triplets, plus per-frame mask for stacks | Add bonds when possible; otherwise expect warnings and distance-based hydrogen inference. |
| `struc.hbond_frequency(mask)` | Convert stack h-bond mask to frequencies | Frequency is per detected triplet. |
| `struc.annotate_sse(atom_array)` | Built-in secondary structure estimate | Returns `a`, `b`, `c`; DSSP is an external application owned elsewhere. |
| `struc.dihedral_backbone(array_or_stack)` / `dihedral_side_chain(...)` | Protein backbone/side-chain torsions | Outputs can include `NaN` where angles are undefined. |
| `struc.nucleotide_dihedral_backbone(...)` / `nucleotide_dihedral_side_chain(...)` | Nucleotide torsions | Non-nucleotide residues produce undefined/`NaN` values. |
| `struc.base_pairs(array)`, `base_pairs_edge(...)`, `base_pairs_glycosidic_bond(...)`, `base_stacking(...)`, `map_nucleotide(...)` | Nucleic-acid base-pair and stacking analysis | Incomplete structures may warn and return fewer interactions. |
| `struc.dot_bracket_from_structure(array)` / `dot_bracket(...)` / `base_pairs_from_dot_bracket(...)` | Convert between base pairs and secondary-structure notation | Use pseudoknot handling when notation contains crossing pairs. |
| `struc.pseudoknots(base_pairs)` | Detect/remove pseudoknot conflicts from base pairs | Useful before plain dot-bracket output. |

## Periodic Boxes and Trajectories

| API | Use |
| --- | --- |
| `struc.vectors_from_unitcell(a, b, c, alpha, beta, gamma)` | Build `(3, 3)` box vectors; angles are radians. |
| `struc.unitcell_from_vectors(box)` | Convert vectors back to cell lengths and angles. |
| `struc.box_volume(box)`, `struc.is_orthogonal(box)` | Box properties. |
| `array.box = box` | `AtomArray` box shape is `(3, 3)`. |
| `stack.box = boxes` | `AtomArrayStack` box shape is `(m, 3, 3)`. |
| `struc.move_inside_box(coord, box)`, `struc.remove_pbc(atoms)` | Rewrap or unwrap periodic structures. |
| `struc.rdf(center, atoms, interval=(...), periodic=True)` | Radial distribution functions over atom selections. |

Trajectory files usually store coordinates only; use `file-io-formats` for loading them with a template structure, then use this sub-skill for superposition, RMSD/RMSF, RDF, and PBC-aware measurements.

## Chemical Information Helpers

| API | Use |
| --- | --- |
| `info.residue("TYR")` | CCD-derived residue template as an `AtomArray`. |
| `info.bonds_in_residue("TYR")`, `info.bond_type(res_name, atom1, atom2)` | Standard bond information. |
| `info.amino_acid_names()`, `nucleotide_names()`, `carbohydrate_names()`, `ion_names()` | Known CCD group names. |
| `info.full_name(res_name)`, `one_letter_code(res_name)`, `link_type(res_name)` | Residue metadata. |
| `info.mass(element_or_residue)`, `info.vdw_radius_single(element)`, `info.vdw_radius_protor(res_name, atom_name)` | Masses and radii for analysis and SASA/debugging. |
| `info.standardize_order(array)` | Canonical atom ordering inside residues when compatible. |

## Structural Alphabets

Use `biotite.structure.alphabet` when the task asks for structure-derived sequences, Foldseek-like 3Di encodings, or alignment-guided structure comparison.

| API | Use |
| --- | --- |
| `strucalph.to_3di(atom_array)` | Convert peptide chains to one 3Di sequence per chain plus chain starts. |
| `biotite.sequence.align.SubstitutionMatrix.std_3di_matrix()` | Score 3Di sequence alignments. |
| `struc.to_sequence(atom_array)` | Convert protein/nucleotide structures to sequence objects when annotations are sufficient. |

Structural alphabet alignment uses the sequence-analysis APIs for alignment, then maps aligned residue anchors back to structure coordinates for superposition.
