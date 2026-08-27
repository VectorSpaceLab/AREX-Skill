# Residual Quantizers API Reference

This reference covers the residual codebook APIs owned by this sub-skill: `ResidualVQ` and `GroupedResidualVQ`. It intentionally excludes residual scalar (`ResidualFSQ`, `GroupedResidualFSQ`), residual lookup-free (`ResidualLFQ`, `GroupedResidualLFQ`), and residual SimVQ APIs.

## Imports

```python
from vector_quantize_pytorch import ResidualVQ, GroupedResidualVQ
```

## `ResidualVQ`

### Constructor signature

```python
ResidualVQ(
    *,
    dim,
    num_quantizers: int | None = None,
    codebook_size: int | tuple[int, ...],
    codebook_dim=None,
    shared_codebook=False,
    diveq=False,
    heads=1,
    quantize_dropout=False,
    quantize_dropout_cutoff_index=0,
    quantize_dropout_multiple_of=1,
    accept_image_fmap=False,
    implicit_neural_codebook=False,
    mlp_kwargs={},
    beam_size=None,
    eval_beam_size=None,
    beam_score_quantizer_weights: list[float] | None = None,
    quant_grad_frac=0.0,
    **vq_kwargs,
)
```

### Forward signature

```python
quantized, indices, commit_loss = residual_vq(
    x,
    mask=None,
    indices=None,
    return_all_codes=False,
    sample_codebook_temp=None,
    freeze_codebook=False,
    beam_size=None,
    rand_quantize_dropout_fixed_seed=None,
)
```

If `return_all_codes=True`, the normal return tuple is:

```python
quantized, indices, commit_loss, all_codes = residual_vq(x, return_all_codes=True)
```

If `indices` is supplied to `forward`, the module switches to target-index loss mode and returns:

```python
quantized, cross_entropy_loss = residual_vq(x, indices=saved_indices)
```

Target-index loss mode rejects dropped-out `-1` indices.

### Standard shape contract

For a default sequence input `x` with shape `(batch, sequence, dim)`:

| Value | Shape | Notes |
|---|---:|---|
| `quantized` | `(batch, sequence, dim)` | Same public feature dimension as input. If `codebook_dim != dim`, projections happen internally. |
| `indices` | `(batch, sequence, num_quantizers)` | Last axis is residual quantizer depth. Dropped training layers can be `-1` when `quantize_dropout=True`. |
| `commit_loss` | usually `(num_quantizers,)` in reduced modes; may include batch dimensions in non-reduced modes | Treat the last/only residual axis as one loss per quantizer layer. Check actual shape before reducing in a training objective. |
| `all_codes` | `(num_quantizers, batch, sequence, codebook_dim)` | Returned only with `return_all_codes=True`; these are pre-output-projection code vectors. |

For image feature maps with `accept_image_fmap=True`, the package accepts image-like tensors and index shapes with spatial dimensions before the final quantizer axis. Do not pass `indices` into `forward` at the same time as `accept_image_fmap=True`; use `get_output_from_indices` for reconstruction.

### Core parameters

| Parameter | Purpose | Operational guidance |
|---|---|---|
| `dim` | Public input/output feature width. | Must match the last feature dimension for sequence input. |
| `num_quantizers` | Residual depth. | Required unless `codebook_size` is a tuple; then depth can be inferred from tuple length. |
| `codebook_size` | Number of codes per residual layer. | Integer repeats the same size for every layer. Tuple gives layer-specific sizes, e.g. `(5, 128, 256)` creates three residual layers if `num_quantizers` is omitted. |
| `codebook_dim` | Internal code vector width. | Defaults to `dim`. If smaller/larger than `dim`, `ResidualVQ` adds input/output projections. |
| `heads` | Passed in signature but constrained. | `ResidualVQ` asserts `heads == 1`; use base `VectorQuantize` if multi-headed codes are needed. |
| `mask` | Optional boolean mask over sequence positions. | Masked positions are excluded from VQ updates/loss aggregation by the underlying VQ layers. |
| `freeze_codebook` | Per-forward codebook-update switch. | Useful for shape/reconstruction checks in training mode, or when generating deterministic index evidence without EMA mutation. |

### Reconstruction helpers

```python
reconstructed = residual_vq.get_output_from_indices(indices)
all_codes = residual_vq.get_codes_from_indices(indices)
```

- `get_output_from_indices` sums per-layer code vectors and applies the output projection, returning the public `dim` shape.
- `get_codes_from_indices` returns layer-wise codes before summation/projection.
- Indices must come from the same model state. Save the model state dict and codebooks together with any saved indices.
- If `quantize_dropout=True`, shorter/coarser index tensors can be padded internally, and `-1` marks skipped layers. Without dropout enabled, shorter index tensors are invalid.

### Shared and stochastic codebooks

| Parameter | Effect |
|---|---|
| `shared_codebook=True` | All residual layers share the first layer's codebook. The codebook size must be uniform across layers. EMA / in-place optimizer updates are manually coordinated at the end of the stack. |
| `stochastic_sample_codes=True` | Underlying VQ layers sample codes stochastically during training rather than always taking nearest neighbors. |
| `sample_codebook_temp` | Controls stochastic sampling temperature. A temperature of `0` behaves like deterministic nearest-code selection; higher values sample more. It can be set in the constructor or overridden per forward call. |

`shared_codebook=True` plus `stochastic_sample_codes=True` is the RQ-VAE-style pattern. Do not combine `shared_codebook=True` with non-uniform tuple codebook sizes.

### Quantize dropout

| Parameter | Effect |
|---|---|
| `quantize_dropout=True` | During training, randomly stops after a residual layer and fills later layer indices with `-1`. It is disabled when the module is in eval mode. |
| `quantize_dropout_cutoff_index` | Earliest residual layer allowed as the dropout cutoff. Must be non-negative. |
| `quantize_dropout_multiple_of` | Rounds the sampled cutoff to a structured multiple, as used in codec-style dropout. |
| `rand_quantize_dropout_fixed_seed` | Per-forward deterministic seed for reproducible dropout across grouped sub-quantizers or tests. |

Training dropout is for robustness to fewer fine quantizers. Generate reconstruction targets or cross-entropy targets in eval mode unless the workflow explicitly handles `-1` as skipped layers.

### Beam search

| Parameter | Effect |
|---|---|
| `beam_size` | Enables residual beam search when greater than `1`; each layer considers top-k candidates. |
| `eval_beam_size` | Beam size to use in eval mode; may be larger than training beam size. It can only be set if `beam_size` is also set. |
| `beam_score_quantizer_weights` | Per-layer score weights; length must equal `num_quantizers`. |
| forward `beam_size=` | Overrides the constructor beam setting for that call. |

Beam search expands candidate tensors across sequence positions and residual layers. It can improve residual choices, but memory/time scale with beam size, codebook size, sequence length, and residual depth.

### DiVeQ and implicit neural codebooks

| Parameter | Effect | Consequence |
|---|---|---|
| `diveq=True` | Uses differentiable vector quantization via directional reparameterization. | Disables EMA updates, makes codebooks learnable, disables route-gradients-to-input, and sets commitment weight to `0`. Optimize codebook parameters by gradient descent instead of expecting EMA/auxiliary commitment losses to drive updates. |
| `implicit_neural_codebook=True` | Uses MLP-transformed implicit codebooks conditioned on the current quantized output. | Sets learnable codebooks and disables EMA. Optional `mlp_kwargs` controls the residual MLP stack. This path is heavier and should be validated with small tensors first. |
| `quant_grad_frac` | Controls how much gradient from later residual layers flows through previous quantized outputs. | Ignored for `diveq=True`, where it is forced to `1.0`. |

`diveq=True` and EMA updating are mutually exclusive.

## `GroupedResidualVQ`

### Constructor signature

```python
GroupedResidualVQ(
    *,
    dim,
    groups=1,
    accept_image_fmap=False,
    **kwargs,
)
```

All extra keyword arguments are forwarded to one `ResidualVQ` per group.

### Forward signature

```python
quantized, indices, commit_loss = grouped_vq(
    x,
    indices=None,
    return_all_codes=False,
    sample_codebook_temp=None,
    freeze_codebook=False,
    mask=None,
)
```

With `return_all_codes=True`:

```python
quantized, indices, commit_loss, per_group_all_codes = grouped_vq(
    x,
    return_all_codes=True,
)
```

### Grouped shape contract

For default sequence input `x` with shape `(batch, sequence, dim)`:

| Value | Shape | Notes |
|---|---:|---|
| `quantized` | `(batch, sequence, dim)` | Concatenation of per-group quantized chunks. |
| `indices` | `(groups, batch, sequence, num_quantizers)` | First axis identifies the feature group. Pass this full grouped tensor to `get_output_from_indices`. |
| `commit_loss` | commonly `(groups, num_quantizers)` after reduction | First axis identifies the group. |
| `per_group_all_codes` | tuple length `groups`; each tensor `(num_quantizers, batch, sequence, dim // groups)` | Returned only with `return_all_codes=True`. The forward return is a tuple of per-group tensors, not one stacked tensor. |

### Group constraints

- `dim % groups == 0` is required.
- With default sequence input, groups split the last feature dimension.
- With `accept_image_fmap=True`, groups split the channel dimension instead.
- Grouped reconstruction is:

```python
reconstructed = grouped_vq.get_output_from_indices(indices)
```

The `indices` tensor must keep the leading group axis. Accidentally transposing to `(batch, groups, sequence, num_quantizers)` will pair groups with the wrong residual VQ instances.
