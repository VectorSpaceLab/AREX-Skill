# Lookup-Free and Latent API Reference

This reference covers the public classes owned by the `lookup-free-and-latent` sub-skill. Import them from `vector_quantize_pytorch` unless noted otherwise:

```python
from vector_quantize_pytorch import (
    LFQ,
    ResidualLFQ,
    GroupedResidualLFQ,
    LatentQuantize,
    BinaryMapper,
    EvoLFQ,
)
```

## Tensor-layout summary

| Class | Expected input layout | Quantized output layout | Index layout |
|---|---|---|---|
| `LFQ` | Sequence `(batch, seq, dim)`; image `(batch, dim, height, width)`; video `(batch, dim, time, height, width)`. For rank >= 4 it defaults to channel-first unless `channel_first` overrides. | Same as input. | Sequence `(batch, seq)` or `(batch, seq, num_codebooks)`; image/video spatial dimensions with optional final `num_codebooks`. |
| `ResidualLFQ` | Sequence `(batch, seq, dim)` after optional projection. | Same as input. | `(batch, seq, num_quantizers)`. |
| `GroupedResidualLFQ` | Sequence `(batch, seq, dim)` by default; image `(batch, dim, height, width)` when `accept_image_fmap=True`. | Same as input. | `(groups, batch, seq_or_spatial..., num_quantizers)`. |
| `LatentQuantize` | Channel-first family: `(batch, dim, ...)`, including image/video/series. For a sequence represented as `(batch, seq, dim)`, transpose to `(batch, dim, seq)` first. | Same as input. | Spatial/series axes with optional final `num_codebooks`. |
| `BinaryMapper` | Arbitrary leading dimensions ending in `bits`: `(..., bits)`. | One-hot `(..., 2 ** bits)`. | Optional `(...)`. |
| `EvoLFQ` | Whatever the supplied encoder accepts. Encoder output must be `(batch, dim)` or `(batch, seq, dim)` compatible with its LFQ bottleneck. | Decoder output. | LFQ indices, squeezed for 2D encoder latents. |

## `LFQ`

Signature:

```python
LFQ(
    *,
    dim=None,
    codebook_size=None,
    entropy_loss_weight=0.1,
    commitment_loss_weight=0.0,
    diversity_gamma=1.0,
    straight_through_activation=nn.Identity(),
    num_codebooks=1,
    keep_num_codebooks_dim=None,
    codebook_scale=1.0,
    frac_per_sample_entropy=1.0,
    has_projections=None,
    projection_has_bias=True,
    soft_clamp_input_value=None,
    cosine_sim_project_in=False,
    cosine_sim_project_in_scale=None,
    channel_first=None,
    experimental_softplus_entropy_loss=False,
    entropy_loss_offset=5.0,
    spherical=False,
    force_quantization_f32=True,
    orthogonal_rotation=False,
)
```

Forward:

```python
quantized, indices, aux_loss = lfq(x, inv_temperature=100.0, mask=None)
(ret, breakdown) = lfq(x, return_loss_breakdown=True, mask=mask)
```

Important fields and constraints:

- Either `dim` or `codebook_size` must be supplied.
- `codebook_size` must be a power of two. `codebook_dim = log2(codebook_size)`.
- Internal binary width is `codebook_dim * num_codebooks`.
- If `dim != codebook_dim * num_codebooks`, LFQ creates input/output projections unless `has_projections` overrides that behavior.
- With `num_codebooks > 1`, `keep_num_codebooks_dim` must remain true. The returned `indices` carry a final `num_codebooks` dimension.
- `entropy_loss_weight` scales the per-sample entropy minus diversity entropy term; `commitment_loss_weight` separately scales commitment loss.
- `return_loss_breakdown=True` returns `(Return(quantized, indices, aux_loss), LossBreakdown(per_sample_entropy, batch_entropy, commitment))`.
- `indices_to_codes(indices, project_out=True)` reconstructs quantized values from indices. Exact equality is expected when using the same module state and deterministic projections.

Mask behavior:

- `mask` is only used in the training-time entropy/commitment loss calculation.
- For sequence inputs, pass a boolean mask shaped like `(batch, seq)`.
- For image/video inputs, the implementation accepts masks that broadcast to the flattened token axes used by the quantizer. Test small masks before relying on a complex spatial mask.

## `ResidualLFQ`

Signature:

```python
ResidualLFQ(
    *,
    dim,
    num_quantizers,
    codebook_size,
    quantize_dropout=False,
    quantize_dropout_cutoff_index=0,
    quantize_dropout_multiple_of=1,
    soft_clamp_input_value=None,
    **lfq_kwargs,
)
```

Forward:

```python
quantized, indices, losses = residual_lfq(x, mask=None)
quantized, indices, losses, all_codes = residual_lfq(x, return_all_codes=True)
reconstructed = residual_lfq.get_output_from_indices(indices)
```

Notes:

- Each residual layer is an `LFQ` layer. The first layer uses `codebook_scale=1`, then scales down by powers of two.
- The module projects from `dim` to `log2(codebook_size)` when needed, applies all LFQ residual layers there, and projects back.
- `indices` stack along the final dimension: `(batch, seq, num_quantizers)`.
- `losses` stack one auxiliary loss per quantizer: shape `(num_quantizers,)` for common sequence inputs.
- If quantize dropout is active during training, later dropped quantizer indices are filled with `-1`. `get_output_from_indices` can reconstruct from such dropout-aware indices.

## `GroupedResidualLFQ`

Signature:

```python
GroupedResidualLFQ(*, dim, groups=1, accept_image_fmap=False, **residual_lfq_kwargs)
```

Forward:

```python
quantized, indices, losses = grouped_lfq(x, mask=None)
quantized, indices, losses, all_codes = grouped_lfq(x, return_all_codes=True)
reconstructed = grouped_lfq.get_output_from_indices(indices)
```

Notes:

- `dim` must be divisible by `groups`.
- The feature axis is split into `groups`, and each group owns a separate `ResidualLFQ` with `dim_per_group = dim // groups`.
- Default sequence mode splits along the last axis. With `accept_image_fmap=True`, it splits channel-first image features along axis 1.
- `indices` and `losses` are stacked with the group axis first.

## `LatentQuantize`

Signature:

```python
LatentQuantize(
    levels,
    dim,
    commitment_loss_weight=0.1,
    quantization_loss_weight=0.1,
    num_codebooks=1,
    codebook_dim=-1,
    keep_num_codebooks_dim=None,
    optimize_values=True,
    in_place_codebook_optimizer=None,
)
```

Forward:

```python
quantized, indices, loss = latent_quantizer(z)
codes = latent_quantizer.indices_to_codes(indices, project_out=True)
```

Important fields and constraints:

- `levels` can be a list/tuple giving one level count per latent codebook dimension, or an int repeated across `codebook_dim`.
- If `levels` is an int, set `codebook_dim` to a positive integer. Omitting it raises during construction because the scalar level cannot be repeated across an unknown codebook dimension.
- If `levels` is a list, `codebook_dim` defaults to `len(levels)`.
- Internal width is `codebook_dim * num_codebooks`. If `dim` differs from that width, LatentQuantize creates input/output projections.
- With `num_codebooks > 1`, `keep_num_codebooks_dim` must remain true and the returned `indices` keep a final `num_codebooks` dimension.
- `optimize_values=True` stores per-latent code values as learnable parameters. `optimize_values=False` uses fixed tensors.
- The current implementation's in-place optimizer branch expects an internal `optimize_values` attribute but does not set it during construction. Avoid `in_place_codebook_optimizer` unless the installed package version has corrected that behavior.
- `indices_to_codes` returns channel-first layout `(batch, dim, ...)` after optional projection.

## `BinaryMapper`

Signature:

```python
BinaryMapper(bits=1, kl_loss_threshold=log(2), deterministic_on_eval=False)
```

Forward:

```python
one_hot, aux_loss = mapper(logits)
one_hot, indices, aux_loss = mapper(logits, return_indices=True)
```

Options:

- `logits` must end with exactly `bits` channels.
- `temperature` rescales logits before Bernoulli sampling.
- `straight_through` defaults to training mode and adds a differentiable soft probability path to one-hot samples.
- `calc_aux_loss` defaults to training mode. Set it explicitly when evaluating auxiliary KL behavior.
- `deterministic` overrides random Bernoulli sampling; `deterministic_on_eval=True` enables deterministic sampling automatically in eval mode.
- `reduce_aux_kl_loss=False` returns an auxiliary loss over the leading dimensions instead of a scalar mean.
- `log_prob(logits, indices=...)` or `log_prob(logits, one_hot=...)` computes joint log probability for sampled codes.

## `EvoLFQ`

Signature:

```python
EvoLFQ(
    encoder,
    decoder,
    lfq=None,
    *,
    dim=None,
    codebook_size=None,
    num_codebooks=1,
    pop_size=64,
    mutation_rate=0.02,
    tournament_size=2,
    elitism_count=1,
    generations=50,
    **lfq_kwargs,
)
```

Forward:

```python
reconstructed, indices, aux_loss = evo_lfq(x)
```

Wrapper contract:

- Supply either an existing `LFQ` instance or enough `dim` / `codebook_size` / `num_codebooks` information for EvoLFQ to build one.
- `pop_size` must be greater than `elitism_count`.
- The encoder output must be accepted by the LFQ bottleneck:
  - `(batch, dim)` is temporarily reshaped to `(batch, 1, dim)` and squeezed back after quantization.
  - `(batch, seq, dim)` is passed through as a sequence.
- The decoder receives the quantized latent tensor after any 2D squeeze. Its input shape must match the encoder latent shape, not the original input.
- `encode(x)` returns binary bits from the LFQ bottleneck; `decode_bits(bits)` maps binary bits through `lfq.indices_to_codes` and then the decoder.
- `evolve(...)` is a generator over genetic-search results. Use very small `pop_size` and `generations` for smoke tests; full evolution is a training/search workload, not a basic API check.
