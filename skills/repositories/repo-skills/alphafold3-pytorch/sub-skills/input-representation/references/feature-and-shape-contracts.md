# Feature and shape contracts

Use these symbols consistently:

- `b`: batch size
- `n`: token count
- `m`: atom count, `sum(molecule_atom_lens)` for one example
- `s`: MSA row count
- `t`: template count
- `w`: configured atoms per window
- `nw`: number of atom windows
- `dai`, `dapi`, `dmf`, `dtf`, `dmi`: feature dimensions

## Core atom and token fields

| Field | Unbatched shape | Batched shape | Meaning and checks |
|---|---:|---:|---|
| `atom_inputs` | `[m, dai]` | `[b, m, dai]` | Default extractor produces `dai=3`: formal charge, implicit valence, explicit valence. A custom extractor must return a consistent final dimension. |
| `atompair_inputs` | `[m, m, dapi]` | `[b, m, m, dapi]` | Default extractor produces `dapi=5`: relative xyz (3), inverse squared distance (1), and same-reference-space flag (1). |
| windowed `atompair_inputs` | `[nw, w, 2w, dapi]` | `[b, nw, w, 2w, dapi]` | Produced by `full_pairwise_repr_to_windowed`; the final `2w` side is the padded key context used by the model. Only window a full 3-D pairwise tensor once. |
| `molecule_ids` | `[n]` | `[b, n]` | Residue/chemical ids. Batch padding uses `-1`. |
| `molecule_atom_lens` | `[n]` | `[b, n]` | Atom counts per token. Batch padding uses `0`; padded tokens can be identified from this field. |
| `additional_molecule_feats` | `[n, 5]` | `[b, n, 5]` | `[residue_index, token_index, asym_id, entity_id, sym_id]`. The residue index restarts per chain; the token index is global. |
| `is_molecule_types` | `[n, 5]` | `[b, n, 5]` | One-hot-like flags in `[protein, RNA, DNA, ligand, metal]` order. |
| `token_bonds` | `[n, n]` | `[b, n, n]` | Token-level connectivity; polymer links are added between adjacent residues in a chain and atomized ligands use their RDKit bond matrix. |
| `atom_parent_ids` | `[m]` | `[b, m]` | Parent molecule/chain grouping used by atom attention. |

## Optional atom/bond ids and masks

| Field | Shape | Contract |
|---|---:|---|
| `atom_ids` | `[m]` / `[b, m]` | Present only with `add_atom_ids=True`; ids are zero-based positions in the selected atom vocabulary. Every generated atom symbol must be in that vocabulary. |
| `atompair_ids` | `[m, m]` or windowed `[nw, w, 2w]` | Integer category matrix, with zero for no bond. It is batched by adding `[b]`. |
| `missing_atom_mask` | `[m]` / `[b, m]` | True means an atom coordinate is absent. When not supplied it defaults to all false; batch padding defaults to true. |
| `molecule_atom_indices` | `[n]` / `[b, n]` | Global atom index for the token center used by atom attention, or `-1` when unavailable/missing. |
| `distogram_atom_indices` | `[n]` / `[b, n]` | Global atom index used for distance labels, or `-1`. |
| `atom_indices_for_frame` | `[n, 3]` / `[b, n, 3]` | Three global atom indices for a residue frame, or all `-1` when no frame is available. |
| `atom_pos` | `[m, 3]` / `[b, m, 3]` | Reference/label coordinates in flattened atom order. This is not the same shape as standalone Biomolecule conversion input. |
| `msa` | `[s, n, dmi]` / `[b, s, n, dmi]` | MSA features; `msa_mask` is `[s]`/`[b,s]`. |
| `additional_msa_feats` | `[s, n, dmf]` / `[b,s,n,dmf]` | Defaults to one zero MSA row with `dmf=2` if no MSA features are supplied. |
| `additional_token_feats` | `[n, dtf]` / `[b,n,dtf]` | Defaults to zero `[n,33]` token features. |
| `templates` | `[t, n, n, dt]` / `[b,t,n,n,dt]` | Template pair features; `template_mask` is `[t]`/`[b,t]`. Keep this in data-pipeline/model-inference ownership. |
| `token_constraints` | `[n,n,dac]` / `[b,n,n,dac]` | Constraint channels: pocket/contact use one channel and docking uses four. Constraint mask values are `-1.0`. |
| `distance_labels` | `[n,n]` or atom-resolution equivalent | Training labels, not required for sampling. |
| `resolved_labels` | `[m]` / `[b,m]` | Training resolution labels. |
| `resolution` | scalar / `[b]` | Optional experimental resolution. |
| `chains` | length-two integer tensor | Chain selector metadata; `None` values become `-1`. |

## Directed bond ids

`get_atompair_ids` starts with zero for no bond. Bond categories are assigned
from the selected `custom_bonds` (or the four default types: `SINGLE`, `DOUBLE`,
`TRIPLE`, `AROMATIC`), with additional categories for inter-residue links and
unrecognized bond types. Directed mode offsets the reverse direction by the
number of bond types. Therefore:

1. Inspect the maximum id actually emitted for the chosen molecule set.
2. Set the model's `num_atompair_embeds` strictly above that maximum (zero is
   also an embedding category).
3. If a custom bond list changes, recompute the cardinality; do not reuse a
   previous model configuration.
4. Set `num_atom_embeds` to at least the number of entries in `custom_atoms` and
   keep the atom vocabulary identical between input preparation and model.

Custom ids are auxiliary integer embeddings; they do not replace the five
floating-point default atom-pair features.

## Missing values, padding, and ascending indices

- Missing atom lists are local to each molecule before flattening. The resulting
  `missing_atom_mask` is global and has one entry per atom.
- If a missing atom is a token center, distogram center, or frame atom, the
  corresponding index is changed to `-1` so the model can ignore it.
- `hard_validate_atom_indices_ascending` treats `-1` as missing and checks the
  remaining global indices in nondecreasing order. Run it for molecule centers,
  distogram centers, and frame triples after conversion.
- Generic collation pads integer tensors with `-1`, booleans with `False`,
  floats with `0`, `molecule_atom_lens` with `0`, and `missing_atom_mask` with
  `True`. Do not infer a valid atom from a padded row; use the lens/mask.
- When one input has optional MSA/templates and another does not, collation
  creates zero-shaped/default tensors for the absent side and pads dimensions to
  the batch maximum. Prefer homogeneous optional-feature presence in a real
  model batch.

## Coordinates and output

There are three distinct coordinate contracts:

1. **Reference/model input:** `atom_pos` is `[m,3]` per example (or batched
   `[b,m,3]`) and follows flattened atom order.
2. **Sampling:** a model sampling call normally returns `[b,m,3]`; with all
   diffused positions it can return a leading sample-step dimension. Mask padded
   or missing atoms before writing atom coordinates.
3. **Standalone Biomolecule conversion:**
   `alphafold3_input_to_biomolecule` expects one unbatched, token-major array
   `[n,47,3]`. Its first dimension must equal the converted token count and its
   last dimension must be 3. It builds 47-slot masks and chemical metadata for
   the `Biomolecule` object. A batched atom output `[b,m,3]` cannot be passed to
   this function directly.

For direct inference output, prefer the model's structure-returning route when
available. For a standalone conversion, validate `[n,47,3]`, then pass the
resulting `Biomolecule` to `to_inference_mmcif`. This output path is compatible
with mmCIF writing but is not a guarantee of chemical naming fidelity for every
ligand/metal; inspect chemical ids and masks.
