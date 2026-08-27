# Input API

This reference describes the public input surface and the supported conversion
order. Names below are importable from `alphafold3_pytorch` unless noted.

## Public dataclasses

| Type | Use | Required core fields |
|---|---|---|
| `Alphafold3Input` | Human-friendly heterogeneous entity description | At least one of `proteins`, `ss_dna`, `ss_rna`, `ds_dna`, `ds_rna`, `ligands`, or `metal_ions` |
| `MoleculeInput` | RDKit molecules with token pooling already specified | `molecules`, `molecule_token_pool_lens`, ids, molecule features/types, source/target atom indices, token bonds |
| `AtomInput` | One unbatched model-ready example | atom features, molecule ids/lens, atom-pair features, molecule features, molecule type flags |
| `BatchedAtomInput` | Padded batch of `AtomInput` values | Same fields with a leading batch dimension |

`PDBInput` and `PDBDataset` belong to the data-pipeline boundary. They are
accepted by the generic transform registry, but they require structure/data
preparation and should not be substituted for a direct sequence input.

## `Alphafold3Input` entity fields

The converter preserves the top-level category order shown here when building
tokens. Within each sequence, residues are expanded in sequence order.

| Field | JSON/Python value | Semantics |
|---|---|---|
| `proteins` | list of strings or integer tensors | One-letter protein sequences; the supported table includes the 20 standard residues and `X`. |
| `ss_rna` | list of strings or integer tensors | Single-stranded RNA; use `A`, `C`, `G`, `U`, or `N`. |
| `ss_dna` | list of strings or integer tensors | Single-stranded DNA; use `A`, `C`, `G`, `T`, or `N`. |
| `ds_rna` | list of strings or integer tensors | Each entry becomes the supplied RNA strand followed by its reverse complement. |
| `ds_dna` | list of strings or integer tensors | Each entry becomes the supplied DNA strand followed by its reverse complement. |
| `ligands` | list of RDKit molecules or SMILES strings | Each SMILES is parsed and given a generated 3-D conformer. Ligands default to one token per atom. |
| `metal_ions` | list of exact keys or integer tensor | Supported keys include `Mg`, `Mn`, `Fe`, `Co`, `Ni`, `Cu`, `Zn`, `Na`, `Cl`, `Ca`, and `K`. Each ion is represented as an atomized molecule. |
| `misc_molecule_ids` | list of strings or integer tensor | Accepted by the dataclass, but the current direct `Alphafold3Input` conversion path does not consume this field. Use a ligand SMILES for a direct input and do not assume a miscellaneous ID is represented. |
| `missing_atom_indices` | list of per-molecule integer lists or `null` | Local atom indices marked missing before conversion. See the missing-atom limitation in troubleshooting. |
| `atom_pos` | tensor `[m, 3]`, or a list of per-molecule `[atoms, 3]` tensors | Reference coordinates, in the same molecule/atom order as the converter. This is normally training/reference data, not required for sampling. |
| `add_atom_ids` | bool | Add an integer atom-type id for every atom. |
| `add_atompair_ids` | bool | Add integer bond/category ids for every atom pair. |
| `directed_bonds` | bool | Reserve separate directed categories for reverse bond directions. |
| `custom_atoms` | list of strings | Atom vocabulary used when `add_atom_ids=True`; it must cover every atom symbol produced by the molecules. |
| `custom_bonds` | list of strings | Bond vocabulary used when `add_atompair_ids=True`; it must match the intended embedding cardinality. |
| `additional_msa_feats` | float tensor `[s, n, dmf]` | Optional extra MSA features; absent data receive a default `[1, n, 2]` zero feature. |
| `additional_token_feats` | float tensor `[n, dtf]` | Optional token features; absent data receive a default `[n, 33]` zero feature. |
| `msa`, `templates`, masks, labels, constraints | tensors | Optional training/data-pipeline features. Their dimensions must match the token count after all strand and ligand expansion. |
| `chains` | pair of optional integer chain selectors | Passed through for downstream structure/output handling; `None` becomes `-1` at atom level. |

Sequences are case-sensitive in the source tables. Validate and normalize to
uppercase before construction. A character not present in a sequence table is
not a safe way to request an unknown residue: molecule lookup can fail even
though the integer mapping helper has an unknown fallback.

## Conversion and batching functions

| Function | Contract |
|---|---|
| `maybe_transform_to_atom_input(value, raise_exception=False)` | Applies the registered transform for an exact input type. Use `raise_exception=True` during preflight so a bad example is not silently dropped. |
| `maybe_transform_to_atom_inputs(values)` | Converts a list and removes failed conversions; generic collation can duplicate surviving values to fill a batch, so deterministic validators should reject failures instead. |
| `alphafold3_inputs_to_batched_atom_input(value_or_list, **collate_kwargs)` | Converts one or more `Alphafold3Input` values, then calls generic collation. |
| `collate_inputs_to_batched_atom_input(inputs, int_pad_value=-1, atoms_per_window=None, map_input_fn=None, transform_to_atom_inputs=True)` | Converts, optionally windows full pairwise features, pads every field to the batch maxima, and returns `BatchedAtomInput`. |
| `atom_input_to_file(atom_input, path, overwrite=False)` | Saves the dataclass dictionary with `torch.save`; creates parent directories and refuses an existing target by default. |
| `file_to_atom_input(path)` | Loads a saved dictionary with `torch.load(weights_only=True)` and reconstructs `AtomInput`. |
| `AtomDataset(folder)` | Reads `.pt` atom inputs from a folder; it requires an existing folder containing at least one file. |
| `register_input_transform(type, fn)` | Adds or replaces a transform in the process-local registry. Avoid global replacement in a shared long-lived process unless intentional. |
| `alphafold3_input_to_biomolecule(af3_input, atom_positions)` | Converts an input description and token-major coordinate representation into `Biomolecule`; it is not a model call. |

The transform chain for a direct input is equivalent to
`alphafold3_input_to_molecule_lengthed_molecule_input` followed by
`molecule_lengthed_molecule_input_to_atom_input`, then defaults for missing
masks. Those intermediate classes are implementation-facing; prefer the public
entry points unless custom atom-level preparation requires them.

## Molecule and atom-level invariants

- `MoleculeInput.molecule_token_pool_lens` sums to the total RDKit atom count.
- `AtomInput.molecule_atom_lens` describes how atom rows are pooled to tokens;
  the sum is the atom dimension `m`.
- Polymer residues are normally one token with all residue atoms pooled.
  Ligands and modified molecules are atomized by default, so a ligand with
  `q` atoms contributes `q` tokens and `q` atom rows.
- Atom rows are concatenated in category order and then molecule order. All
  global index fields must use this flattened atom order; missing lists remain
  molecule-local until conversion.
- `is_molecule_types` has five columns in this order: protein, RNA, DNA,
  ligand, metal ion. A token belongs to exactly one category.
- `additional_molecule_feats` has five columns: residue index, token index,
  asymmetry/chain id, entity id, and symmetry id.
- An empty direct input is invalid. The converter asserts that at least one
  token exists.
