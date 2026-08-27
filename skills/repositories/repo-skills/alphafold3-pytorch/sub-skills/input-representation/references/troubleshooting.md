# Input troubleshooting

Start by running the bundled inspection helper on the smallest failing JSON
specification. It reports the entity summary and stops before model inference.
Then apply the matching recovery below.

## Empty or invalid entities

- **`you have an empty alphafold3 input` / empty-token assertion:** at least
  one supported protein, RNA, DNA, ligand, or metal entity must be present.
  `misc_molecule_ids` alone does not establish a direct converted entity in the
  current path.
- **Unknown residue or nucleotide:** normalize to uppercase and use only the
  tables documented in the API reference. Do not rely on the integer helper's
  unknown fallback for string conversion; molecule lookup can still reject the
  character.
- **Invalid SMILES, no conformer, or sanitization failure:** isolate the SMILES,
  use a chemically valid small molecule, and confirm it can be parsed by the
  installed RDKit variant. Do not use an empty string or `.` as a general
  ligand. A ligand SMILES is not a CCD identifier.
- **Unknown metal:** use an exact supported metal key. Chemical symbols such as
  `Zn2+` are not interchangeable with the accepted dictionary key `Zn`.
- **RDKit warnings for ions:** warnings about valence, charge, or atom type can
  occur for metal conformers. Treat an exception or missing molecule as a hard
  failure; do not hide a failed sanitization behind warning suppression.

## Relative CCD data and molecule sources

The direct sequence/SMILES/metal path uses packaged residue templates and does
not need a downloaded Chemical Component Dictionary. Structure-derived
`PDBInput` conversion, especially atomized or modified residues, may require a
local CCD SMILES cache under the package's `data/ccd_data` layout. If that cache
is absent, the conversion reports that CCD relative data is unavailable. Do
not make the no-download inspection helper acquire it. Route mmCIF, CCD, MSA,
and template preparation to [data-pipeline](../../data-pipeline/SKILL.md), where
large-data and network requirements are explicit.

## Atom and token count failures

- **Molecule length mismatch:** the sum of RDKit atom counts must equal
  `molecule_token_pool_lens` for a manual `MoleculeInput`. Re-check that the
  list is in molecule order and that ligand atoms were not counted as one atom.
- **Unexpected token count:** dsDNA/dsRNA each add the reverse-complement
  strand; atomized ligands add one token per atom; metals add one token each.
- **Missing-index list assertion:** direct conversion expects local missing atom
  lists aligned to its internal molecule list, and its current expanded-token
  check is incompatible with some nonempty lists when a multi-atom ligand is
  present. Use a polymer-only missing-atom preflight, or construct a validated
  `AtomInput` explicitly. Never pad the list with guesses.
- **Out-of-range index:** all nonnegative center, distogram, and frame indices
  must be less than `m`; missing entries are `-1`. Local molecule indices must be
  within that molecule's RDKit atom count before flattening.
- **Nonascending indices:** preserve the converter's molecule order. Run the
  ascending-index validator after every crop, manual concatenation, or custom
  atom reorder. A valid missing value is `-1`, not an arbitrary padding index.

## Custom atom and bond embeddings

- **Unknown atom symbol:** extend `custom_atoms` in a deterministic order and
  set the model's `num_atom_embeds` to at least its length. Include every symbol
  in every SMILES and metal entity; the default atom list is not universal.
- **Embedding index out of range:** inspect `atom_ids.max()` and
  `atompair_ids.max()` after conversion. Configure embedding counts strictly
  above those maxima. Zero is a real no-bond category.
- **Directed-bond mismatch:** directed mode creates reverse-direction offsets.
  Changing `custom_bonds` or `directed_bonds` changes the category range. Use
  the same flags and vocabulary during model construction and input creation.
- **Unexpected pair dimension:** default pair features are five floats. Atom or
  bond ids are separate optional integer fields; they do not change
  `atompair_inputs.shape[-1]`.

## Masks, padding, and optional features

- **Wrong batch shapes:** compare each input's unpadded `m`, `n`, `s`, and `t`
  before collation. The collator pads to per-field maxima, not to a universal
  fixed length.
- **Padded rows treated as real atoms:** use `molecule_atom_lens==0` for padded
  tokens and `missing_atom_mask==True` for padded atom rows. Integer padding is
  `-1`, and float padding is zero.
- **None versus supplied masks:** when templates or MSA features exist without a
  mask, the atom transform creates an all-true mask. If the feature tensor is
  absent, its mask remains absent. Supplying a mask with the wrong leading size
  is an error, not an implicit crop.
- **MSA/template shape mismatch:** these features are token-aligned after ds
  expansion and ligand atomization. Do not attach pre-expansion `[n,...]`
  tensors to a post-expansion input. Route feature generation to
  [data-pipeline](../../data-pipeline/SKILL.md).
- **Collator silently duplicates examples:** generic collation can replace
  failed conversions with random choices from successful values. Use
  `raise_exception=True` and the bundled helper for deterministic validation.

## Serialization failures

- **Existing output file:** `atom_input_to_file` refuses overwrite by default;
  choose a new temporary/versioned target or explicitly opt into overwrite.
- **Load failure with older `.pt`:** the loader intentionally uses
  `torch.load(weights_only=True)`. Recreate the file from tensor-only fields in
  the current version rather than enabling arbitrary-object deserialization.
- **Empty dataset folder:** `AtomDataset` requires an existing directory and at
  least one `.pt` file. It does not create or populate datasets.
- **Round-trip inequality:** compare every tensor field and its dtype/shape;
  `filepath` is metadata and may be intentionally omitted or uncollatable.

## Coordinates and output conversion

- **Model output passed to `alphafold3_input_to_biomolecule`:** sampling is
  normally `[b,m,3]`; standalone conversion requires `[n,47,3]` for one input.
  Select one example, map/prepare the token-major 47-slot representation, and
  validate `n` before conversion. Do not merely reshape a batched atom array.
- **First dimension assertion:** the coordinate first dimension must equal the
  converted token count. Recompute the count after reverse-complement and
  ligand expansion.
- **Last dimension assertion:** coordinates must end in 3 Cartesian values.
- **Suspicious ligand/metal output names:** the direct converter uses compact
  ligand-compatible residue constants and may emit `UNL`/`UNK`-style chemical
  ids or incomplete ligand naming metadata. Inspect `chemid`, `chemtype`, masks,
  and the generated mmCIF before relying on it as a chemically annotated file.
- **Missing atom coordinates:** preserve the missing mask and avoid writing
  missing positions as observed coordinates. For atom-level output, mask before
  passing positions to an mmCIF writer.

## Dependency and safety failures

If the helper cannot import the package, report the first missing optional
package or binary and stop. Do not install, download, launch a server, train, or
run a full model as part of input validation. Optional acceleration (including
Nim/MSA tooling) is outside this sub-skill's required path.
