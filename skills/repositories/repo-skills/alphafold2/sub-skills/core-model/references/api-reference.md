# Core API reference

## Provenance and confidence

This reference is pinned to distribution `alphafold2-pytorch==0.4.32`, source
commit `931466e487e1be87d1182b17ed4ecfac9e70948d`. The constructor and forward
signatures were confirmed with `inspect.signature` against the installed
Python 3.10 package. Behavioral details were checked against the source files
`alphafold2_pytorch/alphafold2.py`, `constants.py`, `mlm.py`, `reversible.py`,
and `rotary.py`, the README `Usage`, `MSA processing in Trunk`, `Template
processing in Trunk`, `Convolutions`, and attention-variant sections, and the
core cases in `tests/test_attention.py`. The CPU package/model import and tiny
inference smokes passed; CUDA allocation was not verified because the shared
device was out of memory. Native repository tests and downloads are not part
of this skill's runtime checks.

The package is an early/unofficial PyTorch implementation. Prefer the installed
signature and source behavior over README snippets when they disagree.

## Public exports and constructors

The package root exports `Alphafold2` and `Evoformer` from
`alphafold2_pytorch.alphafold2`. `Evoformer` is a lower-level trunk component
for callers that already have pair and MSA representations; it does not create
token embeddings or prediction heads.

The installed signatures are:

```python
Evoformer(*, depth, **kwargs)
Evoformer.forward(self, x, m, mask=None, msa_mask=None)
```

A direct Evoformer call uses `x: (B, N, N, dim)`, `m: (B, M, N, dim)`, an
optional pair mask `(B, N, N)`, and an optional MSA mask `(B, M, N)`. A tiny
CPU inspection with `depth=1`, `dim=16`, `heads=1`, `dim_head=16`, `N=4`, and
`M=2` returned `(B, N, N, dim)` and `(B, M, N, dim)` tensors. This lower-level
route returns representations, not distogram or angle logits.

### Alphafold2 constructor

The public constructor is keyword-only:

```python
Alphafold2(
    *,
    dim,
    max_seq_len=2048,
    depth=6,
    heads=8,
    dim_head=64,
    max_rel_dist=32,
    num_tokens=21,
    num_embedds=1280,
    max_num_msas=20,
    max_num_templates=10,
    extra_msa_evoformer_layers=4,
    attn_dropout=0.0,
    ff_dropout=0.0,
    templates_dim=32,
    templates_embed_layers=4,
    templates_angles_feats_dim=55,
    predict_angles=False,
    symmetrize_omega=False,
    predict_coords=False,
    structure_module_depth=4,
    structure_module_heads=1,
    structure_module_dim_head=4,
    disable_token_embed=False,
    mlm_mask_prob=0.15,
    mlm_random_replace_token_prob=0.1,
    mlm_keep_token_same_prob=0.1,
    mlm_exclude_token_ids=(0,),
    recycling_distance_buckets=32,
)
```

Core/trunk knobs with direct source support:

| Argument | Observed use | Practical note |
| --- | --- | --- |
| `dim` | Width of token, MSA, pair, and trunk representations | Required. Embedding inputs must project to this width. |
| `depth` | Number of main `EvoformerBlock`s | Reduce for a smoke or memory-constrained run. |
| `heads`, `dim_head` | Attention heads and per-head width in main/extra/template blocks | The product controls attention projection width. |
| `max_seq_len` | Passed as `seq_len` while constructing Evoformer/template blocks | No explicit forward length check was found; it is not a reliable runtime cap in this commit. |
| `max_rel_dist` | Size/range of learned clipped relative-position embedding | Relative index differences are clipped to `[-max_rel_dist, max_rel_dist]`. |
| `extra_msa_evoformer_layers` | Depth of the optional extra-MSA Evoformer | Only used when `extra_msa` is supplied. |
| `attn_dropout` | Passed to template pointwise attention; accepted by several block constructors | Do not assume it enables dropout in every trunk attention: some block `dropout` parameters are not forwarded to their attention modules. |
| `ff_dropout` | Passed to trunk/extra `FeedForward` modules | Use `model.eval()` for deterministic inference. |
| `predict_angles` | Creates angle projection heads | Adds three `*_logits` attributes to the return object. |
| `symmetrize_omega` | Chooses symmetrized versus unsymmetrized pair representation for omega logits | Does not change shape. |
| `templates_dim`, `templates_embed_layers`, `templates_angles_feats_dim` | Template feature projection, pairwise template depth, and angle-feature input width | See template contracts below. |
| `disable_token_embed` | Replaces token embedding with a zero-returning module | Both `seq_embed` and `msa_embed` are required by assertions. |

`num_tokens`, `num_embedds`, and the MLM arguments are source-backed but are
usually only changed when the token vocabulary or external embedding width is
known. `max_num_msas` and `max_num_templates` are accepted in the signature
but are not used to validate or truncate tensors in the inspected constructor
or forward path. `predict_coords`, the structure-module dimensions, and
`recycling_distance_buckets` belong to the coordinate/recycling route; see
[structure-and-recycling](../../structure-and-recycling/SKILL.md) when that
sibling is available.

## Forward signature and input shapes

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

Core input contracts observed in the implementation:

- `seq`: integer tensor `(B, N)`. Values normally use the 21 amino-acid token
  ids `0..20` when `num_tokens=21`; the extra embedding row at id `21` is the
  MLM mask token used during training.
- `msa`: optional integer tensor `(B, M, N)`. When present, its final width
  **must equal** `seq.shape[-1]`; the source contains
  `assert msa.shape[-1] == seq.shape[-1]`. This contradicts README examples
  that say MSA width may differ.
- `mask`: optional boolean tensor `(B, N)`. It creates the pair mask by an
  outer product. Supply it for normal calls even though the MSA path can
  sometimes proceed without it: the no-MSA fallback immediately rearranges
  `mask`, so omitting it there fails before inference.
- `msa_mask`: optional boolean tensor `(B, M, N)`, used by MSA axial attention
  and masked outer-mean updates. If a supplied MSA has no mask, the source
  defaults to all `True`. In the no-MSA fallback, `msa` becomes `(B, 1, N)` and
  `msa_mask` is derived from `mask`, replacing any separately supplied value.
- `extra_msa`: optional integer tensor intended as another `(B, M_extra, N)`
  MSA processed by the extra-MSA Evoformer. `extra_msa_mask` is its boolean
  `(B, M_extra, N)` mask. The current source branch mistakenly calls
  `self.token_emb(msa)` rather than `self.token_emb(extra_msa)`; keep the row
  count/shape compatible with `msa` for a conservative call and treat the
  value path as a known source defect.
- `seq_index`: optional one-dimensional index tensor `(N,)` in the inspected
  code. It is converted to clipped pairwise relative distances and looked up
  in a learned embedding. A batched `(B, N)` tensor is not the source-backed
  contract.
- `seq_embed`: optional sequence representation `(B, N, dim)` added to the
  token embedding.
- `msa_embed`: optional MSA representation `(B, M, N, dim)` added to the MSA
  token embedding. With `disable_token_embed=True`, both this and `seq_embed`
  must be supplied, even for a sequence-only fallback (where `M=1`).
- `templates_feats`: optional template pair features `(B, T, N, N,
  templates_dim)`. `templates_mask` is required with it and has shape
  `(B, T, N)`; the source forms a pairwise template mask from its two residue
  axes.
- `templates_angles`: optional per-template residue features `(B, T, N,
  templates_angles_feats_dim)`. It is projected and concatenated as extra MSA
  rows, and also requires `templates_mask`. The source does not perform a
  friendly shape check, so a wrong last width reaches a linear-layer error.
- `embedds`: present in the forward signature and an apparent intended shape
  `(B, M, N, num_embedds)`, projected by `embedd_project`. In this commit the
  branch is unreachable: missing `msa` is first replaced by the sequence, so
  `exists(msa)` is true before the `embedds` branch. Do not claim that passing
  `embedds` changes the computation; use `seq_embed`/`msa_embed` or the
  separate embedding wrapper route instead.
- `recyclables`, `return_confidence`, and `return_recyclables` are coordinate
  and recycling controls. Their accepted fields and lifecycle are deliberately
  routed to [structure-and-recycling](../../structure-and-recycling/SKILL.md).

All masks should be boolean tensors on the same device as their corresponding
inputs. The source uses multiplicative mask broadcasting in attention and
outer-mean operations; a float mask can silently change behavior rather than
provide the intended boolean exclusion.

## Return values and bucket shapes

`constants.py` defines:

```python
DISTOGRAM_BUCKETS = 37
THETA_BUCKETS = 25
PHI_BUCKETS = 13
OMEGA_BUCKETS = 25
```

For the core/trunk path (`predict_coords=False`), inference returns one
`alphafold2_pytorch.alphafold2.ReturnValues` object. Its declared dataclass
fields are `distance`, `theta`, `phi`, `omega`, `msa_mlm_loss`, and
`recyclables`; the implementation dynamically attaches angle-logit fields.
Observed tensor contracts are:

```text
ret.distance       : (B, N, N, 37)  # distogram logits
ret.theta_logits   : (B, N, N, 25)  # only when predict_angles=True
ret.phi_logits     : (B, N, N, 13)  # only when predict_angles=True
ret.omega_logits   : (B, N, N, 25)  # only when predict_angles=True
```

The declared `ret.theta`, `ret.phi`, and `ret.omega` fields remain `None` in
this source path; consume the `*_logits` attributes. `ret.msa_mlm_loss` is also
declared but is not assigned before return in the inspected forward path, so
do not treat it as a populated inference loss. These are logits, not normalized
probabilities. The README's tuple unpacking (`distogram, theta, phi, omega =
model(...)`) is stale for this commit and should not be used.

Output routing is order-sensitive:

1. If `predict_coords=False`, return `ret` after trunk logits, even when
   `return_trunk` or `return_aux_logits` is set.
2. If `predict_coords=True` and `return_trunk=True`, return `ret` before the
   structure module. This is the core way to inspect trunk outputs from a
   coordinate-enabled model.
3. If `predict_coords=True` and `return_trunk=False`, return coordinates with
   shape `(B, N, 3)`. With `return_aux_logits=True`, the observed result is
   `(coords, ret)`, where `ret.distance` and any angle logits are available.
4. Confidence, recycling, and coordinate field interpretation are outside this
   skill. In particular, `return_aux_logits` is not a way to obtain a second
   core-only return value when `predict_coords=False`.

## Source-backed trunk behavior

The source creates a learned pair representation from the sequence embedding,
adds clipped relative position embeddings, processes MSA and pair features
through checkpointed Evoformer blocks, then symmetrizes the pair feature only
for distogram prediction. MSA row masks participate in masked outer-mean
updates; residue masks form pair masks and are forwarded through axial
attention.

`mlm.py` supplies training-time MSA masking and loss internals. It is not a
separate inference API or a reason to pass a training-only argument to the
model.

`depth`, `heads`, `dim_head`, `max_seq_len`, `max_rel_dist`, `attn_dropout`,
and `ff_dropout` are safe constructor names because they appear in the
installed signature. The following README-only names were not present in that
signature and are not verified APIs here:

- `reversible`, `sparse_self_attn`
- `cross_attn_linear`, `cross_attn_kron_primary`, `cross_attn_kron_msa`,
  `cross_attn_compress_ratio`
- `use_conv`, `conv_seq_kernels`, `conv_msa_kernels`, `dilations`,
  `custom_block_types`, `msa_tie_row_attn`
- README-era structure/template names such as `structure_module_type`,
  `structure_module_dim`, `structure_module_refinement_iters`, `atoms`,
  `templates_seq`, `templates_coors`, and `templates_sidechains`
- `predict_real_value_distances`

`reversible.py` contains reusable reversible classes and `rotary.py` contains
rotary helpers, but neither is wired into the inspected public
`Alphafold2` constructor/forward path. Their presence is not evidence that
`reversible=True` or rotary configuration is supported. The repository's
`tests/test_attention.py` `test_embeddings` case passes `embedds`, but that
case does not establish that the unreachable `embedds` branch changes the
computation.
