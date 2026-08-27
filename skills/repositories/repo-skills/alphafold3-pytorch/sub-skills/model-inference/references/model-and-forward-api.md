# Model and forward API

This reference describes the public model surface and the tensor contracts that
must be preserved when routing a request. Shapes use `b` for batch, `m` for
padded atoms, `n` for tokens/molecules, `s` for MSA rows, `t` for templates,
`w` for `atoms_per_window`, and `d*` for configured feature widths.

## Model construction

`Alphafold3` requires `dim_atom_inputs` and `dim_template_feats`. The most
important defaults and invariants are:

| Constructor setting | Contract and selection guidance |
|---|---|
| `dim_atom_inputs` | Must equal the last dimension of `atom_inputs`. It is not the number of atoms. |
| `dim_atompair_inputs` | Must equal the last dimension of dense or windowed `atompair_inputs`; default is 5. |
| `dim_template_feats` | Must equal the last dimension of `templates`; use the configured template feature width even when templates are omitted. |
| `atoms_per_window` | Window width for local atom attention. Dense `[b,m,m,dapi]` pairs are windowed internally; pre-windowed pairs use `[b,nw,w,2w,dapi]`. |
| `dim_atom`, `dim_atompair`, `dim_single`, `dim_pairwise`, `dim_token` | Internal widths. Reduce them together for a smoke model; changing only one may make nested attention projections incompatible. |
| `num_molecule_mods` | Set to `0` and omit `is_molecule_mod` when modifications are unused. If positive, pass `[b,n,num_molecule_mods]` boolean features. |
| `num_atom_embeds`, `num_atompair_embeds` | These enable integer embedding tables. Pass the matching `atom_ids`/`atompair_ids` only when the corresponding table is configured; the model asserts on one-sided use. |
| `num_dist_bins`, `distance_bins` | The number of distance bins must equal `len(distance_bins)`. Confidence PAE/PDE bins are similarly controlled by their bin lists. |
| `plm_embeddings`, `nlm_embeddings` | Optional frozen language-model wrappers. They are not part of a no-download smoke and require their own dependencies and cached weights. |

The public architecture components are useful for reduced diagnostics and
experiments: `InputFeatureEmbedder`, `RelativePositionEncoding`,
`TemplateEmbedder`, `MSAModule`, `PairformerStack`, `DiffusionModule`,
`DiffusionTransformer`, `ConfidenceHead`, and `DistogramHead`. `Attention` and
its local-window path are lower-level components. Select a component only when
the diagnostic isolates it; a component test does not validate the integrated
model.

Production constructor defaults are intentionally large (including a deep
Pairformer, deep diffusion transformer, many diffusion augmentations, and a
large sample schedule). A bounded check should explicitly reduce depth, heads,
internal widths, augmentation count, and sample steps. Checkpoint dimensions
must still match the constructor that created the checkpoint.

## Required forward tensors

The `Alphafold3.forward` call is keyword-only. The core inputs are:

| Argument | Shape | Meaning |
|---|---|---|
| `atom_inputs` | `[b,m,dim_atom_inputs]` | Per-atom continuous features. `m` is padded atom capacity. |
| `atompair_inputs` | `[b,m,m,dim_atompair_inputs]` or `[b,nw,w,2w,dim_atompair_inputs]` | Dense atom-pair features or the local-window representation. Dense inputs are windowed internally. |
| `additional_molecule_feats` | `[b,n,5]` | Integer/metadata features produced by input preparation, including chain/entity-related fields. Preserve the package-produced ordering. |
| `is_molecule_types` | `[b,n,5]` boolean | One-hot-like molecule type flags used by geometry, losses, and ranking. |
| `molecule_atom_lens` | `[b,n]` integer | Number of atoms for each token. Negative values represent padded token slots; valid lengths must sum to no more than `m`. |
| `molecule_ids` | `[b,n]` integer | Package molecule/residue IDs; padded IDs are tolerated by the model but should be produced by the input adapter. |

Useful optional tensors are:

| Argument | Shape | When to pass it |
|---|---|---|
| `additional_token_feats` | `[b,n,dim_additional_token_feats]` (default width 33) | Extra token features. Omit only when the configured adapter supports the absence. |
| `msa`, `msa_mask`, `additional_msa_feats` | `[b,s,n,dim_msa_inputs]`, `[b,s]`, `[b,s,n,dim_additional_msa_feats]` | Prepared MSA features and masks. The model can run without MSA; it does not create a biological MSA. |
| `templates`, `template_mask` | `[b,t,n,n,dim_template_feats]`, `[b,t]` | Prepared template pair features and row mask. The model substitutes a masked zero template when omitted. |
| `molecule_atom_indices` | `[b,n]` | Flattened representative atom per token, required for confidence/model-ranking paths and several label paths. Indices are into the padded atom axis. |
| `distogram_atom_indices` | `[b,n]` | Flattened representative atoms for token-resolution distance labels. Required when deriving token distance labels from coordinates. |
| `atom_pos` | `[b,m,3]` | Ground-truth coordinates. Its presence makes the default mode a loss path. |
| `distance_labels`, `resolved_labels` | `[b,n,n]` or `[b,m,m]`, `[b,m]` | Precomputed labels. `resolved_labels` has binary classes; invalid entries use the configured ignore index. |
| `atom_indices_for_frame` | `[b,n,3]` plus optional validity mask | Three atoms per token for aligned-error/PAE labels. Required only for that label path. |
| `missing_atom_mask`, `atom_parent_ids`, `token_bonds`, `atom_ids`, `atompair_ids` | Package-produced atom/bond metadata | Pass only with matching model configuration and semantics. `missing_atom_mask=True` means missing and is masked in coordinate output. |
| `atom_mask` | `[b,m]` boolean, accepted by the signature | In the integrated `Alphafold3.forward` path, the effective mask is rebuilt from `molecule_atom_lens`; use lengths for padding and `missing_atom_mask` for missing coordinates rather than relying on a conflicting hand-written mask. |

Keep every tensor on the same device. Integer IDs/masks must remain integer or
boolean; do not cast them to the model's floating dtype. For batched examples,
representative indices must include each example's atom offset. The input
adapter owns this bookkeeping; do not reuse un-offset per-token indices after
collation.

## Return-mode decision table

`return_loss` defaults to `True` when coordinates or supported labels make a
loss possible, and to `False` otherwise. Do not rely on this inference when a
call contains both labels and a request for coordinates.

| Intent | Explicit call controls | Result |
|---|---|---|
| Train/diagnose loss | `return_loss=True`, usually with `atom_pos`; add `return_loss_breakdown=True` for detail | Scalar loss, or `(loss, LossBreakdown)`. `LossBreakdown` exposes total, diffusion, distogram, PAE, PDE, pLDDT, resolved, confidence, and diffusion sub-losses. |
| Sample coordinates | `return_loss=False`, `num_sample_steps=...` | `[b,m,3]` coordinates, padded/missing positions zeroed. `num_sample_steps` controls the EDM schedule; it is not a training step count. |
| Force sampling despite labels | `return_loss=False` | Coordinates are sampled even if `atom_pos` or labels are present. This is the key diagnosis for a user who accidentally receives a loss. |
| Force a loss without labels | `return_loss=True` | The model returns a differentiable zero when there is insufficient label information; this is a control-path check, not a training signal. |
| Inspect all diffusion states | `return_loss=False`, `return_all_diffused_atom_pos=True` | A timestep-leading coordinate tensor, typically `[ts,b,m,3]`. Do not combine with `return_bio_pdb_structures`. |
| Add confidence logits | `return_loss=False`, `return_confidence_head_logits=True` | `(coordinates, ConfidenceHeadLogits)`. This performs an extra confidence-head pass over detached trunk/sample values. |
| Add distogram logits too | Also `return_distogram_head_logits=True` | `(coordinates, Alphafold3Logits)`, whose fields include confidence logits plus `distance`. |
| Request Bio.PDB structures | `return_bio_pdb_structures=True` | A list of structures instead of coordinate tensors; use only for the supported conversion path and route general heterogeneous output conversion to input-representation. |

`return_loss_breakdown` affects loss returns. It does not convert a sampling
return into a loss tuple. `num_recycling_steps` controls trunk recycling and is
independent of diffusion `num_sample_steps`; use a small positive integer for a
smoke check and increase only with a memory budget. The EDM schedule computes a
step interpolation using `N - 1`, so use at least two sampling steps for a
finite diagnostic; a one-step request is degenerate in this implementation. `detach_when_recycling`
defaults to the configured setting and can be disabled when gradients through
recycling are explicitly required.

`forward_with_alphafold3_inputs` accepts one input object or a list, performs
package collation/windowing, moves the resulting dictionary to the model device,
and delegates to `forward`. It is the preferred bridge when the request starts
with a package input object rather than already prepared tensors. It does not
replace validation of data semantics; route object construction to the input
sub-skill.

## Confidence, distogram, and ranking outputs

`DistogramHead.forward(pairwise_repr, molecule_atom_lens=None, atom_feats=None)`
returns `[b,num_dist_bins,n,n]` at token resolution, or atom resolution when
constructed with `atom_resolution=True` and given lengths plus atom features.
`ConfidenceHead` returns:

- `pae`: `[b,num_pae_bins,n,n]` or `None` when PAE is deliberately disabled;
- `pde`: `[b,num_pde_bins,n,n]`;
- `plddt`: `[b,num_plddt_bins,m]`;
- `resolved`: `[b,2,m]`.

`ComputeConfidenceScore` converts pLDDT logits to `[b,m]` values on a 0–100
scale, and PAE logits plus `asym_id`/`has_frame` to pTM and (in multimer mode)
ipTM. These are expected confidence estimates, not calibrated guarantees.

`ComputeRankingScore` provides:

- full-complex score = `0.8 * ipTM + 0.2 * pTM + 0.5 * disorder - 100 * clash`;
- single-chain score from pTM;
- interface score for the requested chain tuples;
- modified-residue score from pLDDT.

Its full-complex path needs token chain IDs, frame validity, atom lengths and
positions/mask, and molecule type flags. Keep those metadata aligned with the
same sample; never mix logits from one structure with coordinates from another.

`ComputeModelSelectionScore` evaluates multiple models on one prepared batch.
It samples each model under `no_grad`, computes confidence and distance logits,
then combines weighted lDDT and global PDE. With `return_details=True`, inspect
`ScoreDetails.best_gpde_index`, `best_lddt_index`, the aggregate score, and
per-sample records. A chosen index is a model-selection result, not a claim that
the structure is experimentally correct.

## Checkpoints and optional encoders

`save(path, overwrite=False)` writes package metadata containing the model
version, constructor arguments, and state dictionary. `load(path, strict=False,
map_location='cpu')` loads into an already constructed instance. `init_and_load`
reconstructs the constructor from a package saved by `save` and then loads it;
use it first when available. `strict=True` is useful for compatibility auditing,
while the default permissive load can hide missing/unexpected keys and should be
followed by a deliberate review.

`Alphafold3WithHubMixin` adds a Hugging Face-compatible `from_pretrained` path.
A local model file can be used without network access; a remote identifier may
resolve `alphafold3.bin` through the hub. Use `local_files_only=True` for a
no-network check and make cache/revision/model filename explicit. Do not infer
that a hub identifier supplies a compatible constructor if the package cannot
read its saved init arguments. In the inspected release, the hub override also
forwards a `strict` keyword to `init_and_load` even though the public
`init_and_load` signature exposes only `path` and `map_location`; if that
unexpected-keyword error appears, use the direct package-native loader or treat
hub loading as a release compatibility issue rather than claiming success.

Optional PLM registries include ESM2 and ProstT5; the NLM registry includes
RiNALMo. Instantiating these wrappers may import optional packages and fetch
large pretrained weights, and their wrappers run frozen/no-gradient inference.
They are removed while model state is saved or loaded, so their external weights
and exact configuration must be made available again when the model is rebuilt.
Keep them disabled for smoke, shape, and checkpoint-format checks. If enabled,
verify cache availability, sequence masking, embedding width, and device before
calling the full model; route the acquisition decision to the operator rather
than silently downloading.
