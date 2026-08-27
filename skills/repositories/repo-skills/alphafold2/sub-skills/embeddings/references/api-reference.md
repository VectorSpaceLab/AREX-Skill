# Embedding API reference

This reference describes the 0.4.32 package source. The implementation uses the
spelling `embedds` for the core precomputed-input argument and
`embedd_project` for its projection layer. Import the wrappers from their
module rather than the package root:

```python
from alphafold2_pytorch.embeds import (
    ESMEmbedWrapper,
    MSAEmbedWrapper,
    ProtTranEmbedWrapper,
)
```

## Constants and model identifiers

| Constant | Exact value | Consumer |
|---|---:|---|
| `MSA_EMBED_DIM` | `768` | MSA Transformer wrapper input width |
| `MSA_MODEL_PATH` | `["facebookresearch/esm", "esm_msa1_t12_100M_UR50S"]` | Positional arguments to `torch.hub.load` |
| `ESM_EMBED_DIM` | `1280` | ESM-1b wrapper input width |
| `ESM_MODEL_PATH` | `["facebookresearch/esm", "esm1b_t33_650M_UR50S"]` | Positional arguments to `torch.hub.load` |
| `PROTTRAN_EMBED_DIM` | `1024` | ProtBERT wrapper input width |
| `NUM_EMBEDDS_TR` | `1280` | Default `Alphafold2(num_embedds=...)` |
| `NUM_EMBEDDS_T5` | `1024` | T5-related constant; not used by the three wrappers |

`ProtTranEmbedWrapper` uses `Rostlab/prot_bert` in both
`AutoTokenizer.from_pretrained(..., do_lower_case=False)` and
`AutoModel.from_pretrained(...)`.

## Shared tensor contract

The wrappers accept integer tokens in the package's SidechainNet vocabulary.
The repository examples generate token ids in `[0, 21)`. Use:

| Value | Shape | Notes |
|---|---|---|
| `seq` | `(B, N)` | Primary sequence token ids |
| `msa` | `(B, M, N)` | MSA row token ids |
| `mask` | `(B, N)` | Boolean sequence mask, normally passed through `**kwargs` |
| `msa_mask` | `(B, M, N)` | Boolean MSA mask |
| `seq_embed` | `(B, N, D)` | Already projected to `D == Alphafold2.dim` |
| `msa_embed` | `(B, M, N, D)` | Already projected to `D == Alphafold2.dim` |
| core `embedds` | `(B, M, N, E)` | `E == num_embedds`; default `E=1280` |

The core asserts that `seq.shape[-1] == msa.shape[-1]`. This supersedes the
older README comment that an MSA may have a different width. Masks select valid
positions; they do not reconcile residue axes or feature widths.

Every wrapper returns exactly what its wrapped `Alphafold2.forward` returns.
For the ordinary distogram path that is a `ReturnValues` object with
`.distance` shaped `(B, N, N, 37)`.

## Projection behavior

| Path | Projection |
|---|---|
| `MSAEmbedWrapper` | `Linear(768, D)` unless `D == 768`, then `Identity()` |
| `ESMEmbedWrapper` | `Linear(1280, D)` unless `D == 1280`, then `Identity()` |
| `ProtTranEmbedWrapper` | Always `Linear(1024, D)`, including when `D == 1024` |
| Core `embedds` | Always `Linear(num_embedds, D)` as `embedd_project` |

Set `num_embedds` to the actual last dimension of core precomputed features.
Changing `dim` does not change the required input width; it changes the
projection output and trunk width. Do not silently truncate or pad channels.
Wrapper projections and `embedd_project` are separate parameter sets.

## `ProtTranEmbedWrapper`

```python
ProtTranEmbedWrapper(*, alphafold2)
forward(seq, msa, msa_mask=None, **kwargs)
```

Construction imports `AutoTokenizer` and `AutoModel`, creates
`Linear(1024, alphafold2.dim)`, and immediately calls `from_pretrained` twice
for `Rostlab/prot_bert`. There is no deferred-load or local-only constructor
option.

Forward behavior:

1. Read `M = msa.shape[1]` and flatten `msa` from `(B, M, N)` to `(B*M, N)`.
2. Call `get_prottran_embedd` once for `seq` and once for the flattened MSA.
3. Convert ids to space-separated amino-acid strings, replacing `U`, `Z`, `O`,
   and `B` with `X`.
4. Each helper call constructs a Transformers `feature-extraction` pipeline,
   takes the model output after the leading special token, and retains `N`
   residue positions.
5. Project both 1024-wide results to `D`; reshape MSA output to `(B, M, N, D)`.
6. Call the wrapped model with `seq_embed`, `msa_embed`, `msa_mask`, and all
   remaining keyword arguments.

The wrapper itself does not assert equal sequence/MSA widths, but the wrapped
core does. It requires `msa`; the forward signature has no `msa=None` default.
Pretrained assets, pipeline behavior, and device handling remain external-model
requirements, not consequences of a successful package import.

## `MSAEmbedWrapper`

```python
MSAEmbedWrapper(*, alphafold2)
forward(seq, msa, msa_mask=None, **kwargs)
```

Construction immediately executes
`torch.hub.load("facebookresearch/esm", "esm_msa1_t12_100M_UR50S")`, stores the
returned model and alphabet batch converter, and creates the 768-to-`D`
projection.

The intended forward flow is:

1. Assert equal final widths for `seq` and `msa`.
2. Prepend `seq` as row 0, producing `(B, M+1, N)`.
3. Convert the integer rows and request representation layer 12.
4. Remove the leading model token, project to `D`, split row 0 as
   `seq_embed`, and use the remaining rows as `msa_embed`.
5. Forward both representations, `msa_mask`, and `**kwargs` to the core.

Two implementation defects affect this release:

- `get_msa_embedd(msa, ...)` assigns `device = seq.device`, but `seq` is not a
  helper parameter. A normal call can raise `NameError` before model inference.
- With `msa_mask`, the wrapper counts valid original MSA rows but uses that
  count to slice a tensor that already includes the prepended primary row. If
  all `M` rows are valid, it keeps only the sequence plus `M-1` MSA rows and
  pads one zero row. An all-padded MSA can slice away the primary row as well.

Treat this wrapper as source-described, not runtime-verified, until a reviewed
fix and an external-model validation cover both defects.

## `ESMEmbedWrapper`

```python
ESMEmbedWrapper(*, alphafold2)
forward(seq, msa=None, **kwargs)
```

Construction immediately executes
`torch.hub.load("facebookresearch/esm", "esm1b_t33_650M_UR50S")`, stores the
model and alphabet batch converter, and creates the 1280-to-`D` projection.
The intended flow requests layer 33 for `seq`, optionally flattens MSA rows for
the same model, projects both outputs, restores `(B, M, N, D)`, and forwards
them to the core. `msa_mask` has no named parameter but can be supplied through
`**kwargs`.

The checked source does not reach that intended flow unchanged:

- The wrapper calls `get_esm_embedd(..., device=device)`, but the helper has no
  `device` parameter. Forward therefore raises an unexpected-keyword
  `TypeError` before model inference.
- If that call mismatch is corrected, the helper adds a singleton MSA axis and
  returns `(B, 1, N, 1280)`. The wrapper passes this as a sequence embedding
  that the core expects as `(B, N, D)`. Its optional MSA reshape also expects a
  three-axis helper output and conflicts with the four-axis result.

Do not report this wrapper as operational based only on a successful hub load.

## `disable_token_embed` interaction

By default, the core combines external and token representations:

- sequence: `token_emb(seq) + seq_embed` when `seq_embed` exists;
- MSA: `token_emb(msa) + msa_embed`, then adds the sequence representation to
  every MSA row.

With `disable_token_embed=True`, `Alphafold2.forward` asserts immediately that
**both** `seq_embed` and `msa_embed` exist. The lower-level `embedds` argument
does not satisfy either assertion. An ESM call with `msa=None` also supplies no
MSA embedding and cannot satisfy this mode.

For precomputed features, either retain token embeddings while validating the
pipeline or explicitly project and pass both representation tensors. If one
external tensor stores the primary sequence as row 0, projecting it gives a
possible `seq_embed = projected[:, 0]`; confirm that row semantics before using
this convention.

## Core `embedds` control-flow limitation

`Alphafold2.__init__` creates `embedd_project = Linear(num_embedds, dim)`, and
the source contains an `elif exists(embedds)` branch intended to produce
`(B, M, N, D)` and default `msa_mask` to all true. However, `forward` first
turns `msa=None` into `seq[:, None, :]`. The preceding `if exists(msa)` branch
is therefore always selected: explicit MSA causes `embedds` to be ignored, and
omitted MSA is replaced before branch selection.

The bundled smoke validates the projection and consumes the projected tensor
through explicit `seq_embed`/`msa_embed`. It must not be cited as proof that an
unmodified 0.4.32 forward call consumed its direct `embedds` argument. Making
that branch functional requires a reviewed core change or adapter and belongs
with the [core model](../../core-model/SKILL.md).
