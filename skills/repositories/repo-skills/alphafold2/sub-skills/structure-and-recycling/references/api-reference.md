# Structure API reference

## Evidence status

This reference is pinned to `alphafold2-pytorch==0.4.32`. Constructor and
forward signatures were checked against the installed package, while behavior
was checked against the structure path, return dataclasses, coordinate tests,
and recycling tests for the same release. A tiny CPU coordinate run verified
finite `(B, N, 3)` output. CUDA was visible in the inspection stack but a
shared-device out-of-memory condition prevented allocation, so this reference
does not claim CUDA execution was verified.

The package is an early, unofficial implementation. Where source and README
conflict, the current signature and implementation below are authoritative.

## Structure constructor flags

The complete installed constructor includes the following structure-relevant
arguments:

```python
Alphafold2(
    *,
    dim,
    # trunk and template arguments omitted here
    predict_angles=False,
    predict_coords=False,
    structure_module_depth=4,
    structure_module_heads=1,
    structure_module_dim_head=4,
    disable_token_embed=False,
    recycling_distance_buckets=32,
)
```

| Argument | Verified behavior |
| --- | --- |
| `predict_coords` | Must be `True` to continue from trunk logits into the coordinate path, unless `return_trunk=True` short-circuits it. |
| `structure_module_depth` | Stored on the model and used as the iteration count of the IPA refinement loop. A value of `1` is appropriate for a tiny smoke. |
| `structure_module_heads` | Passed as `heads` when constructing `invariant_point_attention.IPABlock`. |
| `structure_module_dim_head` | Accepted by the public signature but not stored or passed to `IPABlock` in this release. Do not claim that changing it changes the active IPA head width. |
| `recycling_distance_buckets` | Number of embeddings used after discretizing recyclable pair distances. Boundaries are linearly spaced from 2 to 20 with `steps=recycling_distance_buckets`; the last boundary is excluded before `torch.bucketize`. |

`templates_dim`, `templates_embed_layers`, and
`templates_angles_feats_dim` configure the current template feature path; they
do not enable atom-level output.

## Forward contract

The installed signature is:

```python
Alphafold2.forward(
    self,
    seq,
    msa=None,
    mask=None,
    msa_mask=None,
    extra_msa=None,
    extra_msa_mask=None,
    seq_index=None,
    seq_embed=None,
    msa_embed=None,
    templates_feats=None,
    templates_mask=None,
    templates_angles=None,
    embedds=None,
    recyclables=None,
    return_trunk=False,
    return_confidence=False,
    return_recyclables=False,
    return_aux_logits=False,
)
```

Structure-relevant input contracts are:

| Input | Current contract and cautions |
| --- | --- |
| `seq` | Integer token tensor `(B, N)`. The default vocabulary has 21 ordinary amino-acid token ids (`0..20`); the embedding has one additional row used as the MLM mask token. |
| `msa` | Optional integer tensor `(B, M, N)`. Its final dimension is explicitly asserted equal to `seq.shape[-1]`. If omitted, the source creates a one-row MSA from `seq`. |
| `mask` | Boolean residue mask `(B, N)`. Always supply it: the no-MSA fallback immediately rearranges it, and the structure module passes it into IPA. |
| `msa_mask` | Boolean `(B, M, N)`. When an MSA is supplied and this is omitted, the source defaults it to all true. Supplying it explicitly is safer for padded rows/residues. |
| `templates_feats` | Pair features `(B, T, N, N, templates_dim)`. Requires `templates_mask`. These are already prepared features, not PDB paths or raw coordinates. |
| `templates_angles` | Per-template residue features `(B, T, N, templates_angles_feats_dim)`, projected and appended to the MSA rows. Requires `templates_mask`. |
| `templates_mask` | Boolean `(B, T, N)`, used both for pairwise template masking and for angle-feature MSA rows. |
| `extra_msa` | Intended integer extra-MSA input. The current implementation enters the branch based on this argument but embeds `msa`, not `extra_msa`; see [the safe workflow](workflows.md). |
| `extra_msa_mask` | Boolean mask passed to the extra-MSA Evoformer. Use the same shape as the supplied ordinary `msa` in this release's conservative workaround. |
| `recyclables` | A `Recyclables` instance from a compatible coordinate pass. Validate the field shapes, device, dtype compatibility, finiteness, and detachment before use. |

Keep tokens, features, masks, and recyclables on one device. Use integer dtypes
for token tensors and boolean dtypes for masks. Template and embedding feature
tensors should use a floating dtype accepted by the model's linear layers; a
float32 model and inputs are the conservative baseline.

## Coordinate path and high precision refinement

After trunk processing, the implementation takes the first MSA row as the
single representation and linearly maps it and the pair representation for
structure refinement. It then:

1. remembers the current single-representation dtype;
2. converts single and pair representations to `float32`;
3. initializes each residue with identity quaternion and zero translation;
4. runs `structure_module_depth` IPA/update iterations, passing `mask`, pair
   features, rotations, and translations;
5. detaches intermediate rotations before each non-final IPA iteration;
6. projects one local three-vector per residue and transforms it into global
   coordinates.

This is the source-backed meaning of high-precision coordinate refinement: the
structure representations and module are float32 even if the trunk entered in
a lower precision. It is not a claim of scientific or numerical accuracy.
The final `coords.type(original_dtype)` call is not assigned back, so callers
must inspect actual output dtype rather than assuming restoration to the trunk
dtype.

The verified output shape is:

```text
coords: (B, N, 3)
```

The final axis is XYZ and `N` remains residue length. Treat coordinates at
masked positions as invalid even if the returned tensor contains finite
numbers there; preserve the residue mask for downstream filtering.

## Exact return semantics and precedence

`ReturnValues` is declared with these fields:

```text
ReturnValues(
    distance=None,
    theta=None,
    phi=None,
    omega=None,
    msa_mlm_loss=None,
    recyclables=None,
)
```

The coordinate route obeys this order:

| Conditions | Outer return |
| --- | --- |
| `predict_coords=False` | `ReturnValues`; no coordinate path. |
| `predict_coords=True, return_trunk=True` | `ReturnValues`; `return_trunk` short-circuits structure refinement. |
| Coordinate path, `return_aux_logits=True` | `(coords, ret)`, where `ret` is `ReturnValues`. This branch is checked before confidence. |
| Coordinate path, no auxiliary return, `return_confidence=True` | `(coords, confidence)`, where confidence is `(B, N, 1)`. |
| Coordinate path, neither special return | `coords` only. |

`confidence` is `lddt_linear(single_repr.float())`: a raw learned scalar head
per residue. It is not a call to a coordinate metric and should not be labeled
calibrated probability, pLDDT percentage, or correctness without separate
training/calibration evidence.

`return_recyclables=True` only populates `ret.recyclables`; it does not by
itself change the outer return. In practice, combine it with
`return_aux_logits=True`. If `return_aux_logits=True` and
`return_confidence=True` are both set, the return is still `(coords, ret)` and
no separate confidence tensor is exposed. To obtain both forms, make separate
inference calls or derive a supported downstream plan; do not assume a
three-value tuple.

The implementation also fills `ret.distance` and may dynamically add
`theta_logits`, `phi_logits`, and `omega_logits` when angle prediction is
enabled. Those distogram/angle semantics belong to the
[core model](../../core-model/SKILL.md). The declared `theta`, `phi`, and
`omega` fields are not the dynamic logit attributes.

## `Recyclables` and second-pass behavior

The dataclass has exactly three required fields:

```text
Recyclables(
    coords:              (B, N, 3),
    single_msa_repr_row: (B, N, dim),
    pairwise_repr:       (B, N, N, dim),
)
```

When requested, all three tensors are detached before storage. On a later call:

- normalized `single_msa_repr_row` is added to the current first MSA row;
- normalized `pairwise_repr` is added to the current pair representation;
- `torch.cdist(coords, coords)` produces pair distances, which are bucketized,
  embedded, and added to the current pair representation.

The model performs one injection per call. It has no `num_recycles` argument
and no automatic outer loop. Reuse the same model and maintain compatible
`B`, `N`, model `dim`, device, masks, and optional feature shapes. A stale or
cross-model object can fail during in-place addition, normalization, cdist, or
device dispatch rather than through a friendly validator.

## Templates and extra MSA feeding structure

Templates and extra MSA affect the trunk representations before IPA:

- `templates_feats` is embedded, refined with template pairwise attention, and
  pooled into the main pair representation.
- `templates_angles` is projected and concatenated to the MSA representation;
  its mask rows are concatenated to `msa_mask`.
- entering the extra-MSA branch runs a separate Evoformer and updates the pair
  representation before the main trunk.

These paths do not directly return template coordinates, atoms, or a relaxed
structure. The current extra-MSA implementation uses `self.token_emb(msa)`
instead of `self.token_emb(extra_msa)`. Consequently, the `extra_msa` values
are not read by that embedding statement, and a different row count can make
its mask incompatible with the embedded ordinary MSA. Treat this as a release
limitation, not an intended semantic contract.

## Source/README drift

The README's Predicting Coordinates, Atoms, Real-Value Distance, Template
processing, and Equivariant Attention sections describe older or aspirational
interfaces. None of these names appears in the installed constructor/forward
signature:

- `atoms`
- `structure_module_type`
- `structure_module_dim`
- `structure_module_refinement_iters`
- `structure_num_global_nodes`
- `predict_real_value_distances`
- `templates_seq`, `templates_coors`, `templates_sidechains`

At this version:

- output is `(B, N, 3)`, not `(B, N * atom_count, 3)`;
- the structure path imports and uses `IPABlock`;
- `se3`, `en`, and `egnn` are not selectable `structure_module_type` values;
- no real-value mean/standard-deviation distance prediction flag exists;
- current template inputs are prepared `templates_feats`, optional
  `templates_angles`, and `templates_mask`.

Passing a stale keyword raises `TypeError` rather than selecting the README's
claimed behavior.
