# Structure Analysis Troubleshooting

Use this guide for common Biotite structure-analysis failures after a structure is in memory. For parser-specific load options, route to `../../file-io-formats/`; for external DSSP or database fetching, route to sibling sub-skills.

## Coordinates and Shapes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `coord` assignment raises a shape or dtype error | Coordinates are not numeric or do not match `(n, 3)` / `(m, n, 3)` | Convert with `np.asarray(values, dtype=float)` and validate shape before assignment. |
| Geometry output has an unexpected shape | `distance()`, `angle()`, or `dihedral()` broadcasted inputs | Print `struc.coord(input).shape`; use slices or index functions when pairwise atom-index tuples are intended. |
| `superimpose()` fails or RMSD is nonsensical | Fixed/mobile atoms differ in count, order, or correspondence | Filter both structures to the same atom set in the same order; use a stable mask such as `atom_name == "CA"` or derive homolog anchors. |
| Raw coordinate helper works but AtomArray helper fails | Annotation length or container shape differs from coordinate shape | Check `array.array_length()`, `stack.stack_depth()`, and `array.coord.shape` together. |

Quick coordinate guard:

```python
coord = np.asarray(coord, dtype=float)
assert coord.shape == (atoms.array_length(), 3)
atoms.coord = coord
```

## Annotation Arrays

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `set_annotation()` raises `IndexError` or `ValueError` | New annotation length does not equal atom count | Use `len(values) == array.array_length()` and reshape before assignment. |
| Edits to a filtered selection do not affect the original | Assignment was made to a temporary subarray | Apply the mask to the annotation array: `array.chain_id[mask] = "B"`. |
| Atom names, residue names, or elements are blank/default | `AtomArray(length)` was allocated but annotations were not filled | Set mandatory annotations before filters, chemistry, SASA, or sequence conversion. |
| Long chain IDs or names are truncated in manual NumPy assignment | Existing string dtype is too narrow | Prefer `set_annotation()` for full-array replacement so Biotite can choose a compatible dtype. |
| Filters return empty selections | Invalid residue/atom names or noncanonical naming | Inspect `np.unique(array.res_name)`, `np.unique(array.atom_name)`, and `np.unique(array.element)`; compare with `info.full_name()` or group-name helpers. |

Mandatory annotations are `chain_id`, `res_id`, `ins_code`, `res_name`, `hetero`, `atom_name`, and `element`. Many advanced helpers assume these are meaningful, not just present.

## Bonds and Connectivity

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `array.bonds = ...` raises `TypeError` | Assigned object is not a `BondList` | Create `struc.BondList(array.array_length(), bond_array)`. |
| `array.bonds = ...` raises `ValueError` | BondList atom count differs from `array.array_length()` | Rebuild the `BondList` for the current filtered or concatenated array. |
| Hydrogen bond analysis warns about missing `BondList` | `atoms.bonds is None` and Biotite must infer hydrogens from distance | Attach parser-provided bonds, `connect_via_residue_names()`, `connect_via_distances()`, or a merged bond list. |
| Rotatable bonds or bond orders look wrong | Bond types are `BondType.ANY` or missing | Use parser bonds with orders, CCD-derived residue bonds, or explicitly typed bond triples. |
| Connectivity splits are surprising | Solvent/ions/alternate locations are included | Filter solvent/ions and resolve altlocs before graph analysis. |

Distance-based bonds are useful but not a substitute for known chemical bond orders when bond type matters.

## File-Load Side Effects in Structure Work

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Alternate conformers appear duplicated | File was loaded with `altloc="all"` | Use `filter_first_altloc()` or `filter_highest_occupancy_altloc()` after loading required fields. Parser option details belong in `../../file-io-formats/`. |
| Bonds are missing after loading PDBx/BinaryCIF | Structure was loaded with `include_bonds=False` or format lacks bond data | Reload with bonds via file-IO guidance when possible, or infer with structure connectivity helpers. |
| Only one model/frame is present | Loader used `model=1` or trajectory template/file options selected a subset | Route load option troubleshooting to `../../file-io-formats/`, then return here for analysis. |
| Author chain/residue IDs differ from expected labels | Parser used author vs label fields differently | Confirm file-IO `use_author_fields` behavior before constructing masks. |

This sub-skill should not instruct future agents to open original repo examples or data files to fix these issues.

## Periodic Boxes and Trajectories

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Assigning `box` raises `ValueError` | Shape is not `(3, 3)` for `AtomArray` or `(m, 3, 3)` for `AtomArrayStack` | Build boxes with `vectors_from_unitcell()` and stack one box per frame. |
| PBC distances are wrong or huge | Box units differ from coordinate units, or angles are degrees instead of radians | Convert all lengths to Å and all unit-cell angles to radians before `vectors_from_unitcell()`. |
| RDF or periodic h-bond search fails | `periodic=True` is used without a valid box | Check `atoms.box is not None` and the shape matches the container. |
| RMSD/RMSF over trajectory is inflated | Frames were not superimposed before comparison | Call `trajectory, _ = struc.superimpose(trajectory[0], trajectory)` before `rmsd()`/`rmsf()`. |
| Molecule is split across boundaries | Wrapped coordinates cross periodic boundaries | Use `remove_pbc()` before non-PBC geometry, or `move_inside_box()` when rewrapping is intended. |

## SASA, Radii, and Elements

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| SASA gives `NaN` or unexpected zeros | Missing/invalid element annotations or radii lookup failure | Validate `array.element`; use `info.vdw_radius_single(element)` or residue/atom-specific `info.vdw_radius_protor()`. |
| SASA differs strongly from another tool | Hydrogen handling or radii set differs | Use `vdw_radii="ProtOr"` for structures without hydrogens and `"Single"` for all-atom structures with hydrogens. |
| Residue SASA totals are wrong | Atom-level values were summed over the wrong grouping | Aggregate with `apply_residue_wise(array, atom_sasa, np.nansum)` after filtering to the intended chain/polymer. |

## Secondary Structure: Built-In Estimate vs DSSP

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `annotate_sse()` output differs from DSSP | Biotite's built-in estimator is not DSSP | Treat `annotate_sse()` as a built-in estimate returning `a`, `b`, `c`. Use `database-application` for external DSSP wrapper setup and binary troubleshooting. |
| SSE assignment fails or is mostly coil | Missing backbone atoms, wrong chain selection, or non-protein residues included | Filter amino acids and peptide backbone; check `atom_name` includes expected `N`, `CA`, `C`, `O` atoms. |
| Multi-chain SSE is hard to interpret | Chains were not split before annotation | Iterate with `chain_iter()` or filter one `chain_id` at a time. |

## Nucleic Acids, Base Pairs, and Pseudoknots

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `base_pairs()` warns about incomplete structures | Base-ring atoms or expected hydrogen-bond atoms are missing | Use `filter_heavy()` intentionally, inspect residue atom names, and expect fewer interactions for incomplete residues. |
| Modified bases are skipped or mapped unexpectedly | Noncanonical nucleotide residue names | Use `map_nucleotide(info.residue(res_name))` or `filter_nucleotides()` instead of canonical-only filters. |
| Dot-bracket output cannot represent crossing pairs | Pseudoknots exist | Use `pseudoknots()` to detect or remove crossing interactions before plain dot-bracket conversion. |
| Base-pair edge labels look ambiguous | Multiple edges have equal geometric support | Inspect full pair geometry or treat ambiguous edges as lower-confidence annotations. |

## Structural Alphabets

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `to_3di()` fails or returns no sequences | Input is not a peptide chain or lacks expected backbone atoms | Filter with `filter_amino_acids()` and verify `CA`/backbone atoms before encoding. |
| Alignment-guided superposition anchors are wrong | Alignment positions were not mapped back to residue-level `CA` atoms correctly | Use chain starts and residue order from `to_3di()`; filter both structures to representative atoms before indexing anchors. |
| 3Di alignment imports are missing | Sequence alignment APIs were not imported | Use `biotite.sequence.align` and `SubstitutionMatrix.std_3di_matrix()`; route alignment details to sequence-analysis if needed. |

## Source Example Exclusions

The upstream structure examples include network fetches, plotting, remote trajectories, docking, and optional visualization packages. They are not bundled as runnable runtime scripts here because future agents should not depend on network, external files, optional binaries, or the source checkout for core structure analysis. The bundled helper `../scripts/structure_geometry_smoke.py` preserves safe local construction, filtering, bonds, geometry, superposition, and PBC checks with in-memory data only.
