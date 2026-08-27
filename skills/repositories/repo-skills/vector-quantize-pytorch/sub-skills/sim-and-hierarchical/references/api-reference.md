# SimVQ and HierarchicalVQ API Reference

This reference covers the vector-quantize-pytorch APIs owned by this sub-skill: `SimVQ`, `ResidualSimVQ`, and `HierarchicalVQ`. All examples assume the package is installed and importable.

```python
from vector_quantize_pytorch import SimVQ, ResidualSimVQ, HierarchicalVQ
```

## Family selection

| Need | Use | Main layout | Reconstruction helper |
|---|---|---|---|
| One implicit/frozen codebook transformed into the model dimension | `SimVQ` | channel-last by default; channel-first if requested | `indices_to_codes(indices)` |
| Multiple residual SimVQ layers | `ResidualSimVQ` | same as `SimVQ` | `get_output_from_indices(indices)` |
| Multi-scale image feature-map quantization | `HierarchicalVQ` | always `(batch, channels, height, width)` | `get_output_from_indices(index_list)` |

## `SimVQ`

Constructor signature:

```python
SimVQ(
    dim,
    codebook_size,
    codebook_transform=None,
    init_fn=identity,
    channel_first=False,
    rotation_trick=True,
    input_to_quantize_commit_loss_weight=0.25,
    commitment_weight=1.0,
    frozen_codebook_dim=None,
)
```

Forward and helper:

```python
quantized, indices, commit_loss = sim_vq(x)
codes = sim_vq.indices_to_codes(indices)
```

### Shape contract

- With `channel_first=False` (default), `x` is shaped `(batch, ..., dim)`; for a sequence this is commonly `(batch, length, dim)`. `quantized` has the same shape and `indices` is `(batch, ...)`.
- With `channel_first=True`, `x` is shaped `(batch, dim, ...)`; for an image feature map this is commonly `(batch, dim, height, width)`. `quantized` has the same shape and `indices` is `(batch, ...)`, for example `(batch, height, width)`.
- `commit_loss` is a scalar tensor multiplied by `commitment_weight`.

### Implicit/frozen codebook semantics

`SimVQ` stores a frozen random codebook buffer and transforms it through `codebook_transform` to obtain the effective codebook used for nearest-neighbor lookup.

- If `codebook_transform=None`, the module creates `nn.Linear(frozen_codebook_dim, dim, bias=False)`.
- `frozen_codebook_dim` defaults to `dim`; set it when the frozen codebook dimension differs from the model dimension.
- A custom `codebook_transform` must map from `frozen_codebook_dim` to `dim`.
- `init_fn` is applied to the frozen codebook tensor at construction time; use it for uniform/orthogonal/custom initialization of the frozen buffer.
- The frozen buffer itself is not learned, but the transform module can have learned parameters.
- Saving only the integer `indices` is not enough to recover old vectors unless the same trained transform and frozen buffer are restored.

### Rotation trick and losses

- `rotation_trick=True` applies the rotation-trick straight-through estimator while preserving the selected code values in the forward pass.
- `rotation_trick=False` uses a simpler straight-through path.
- The commitment objective combines distance from input to quantized vector plus a lower-weighted input-to-quantize term. Tune `input_to_quantize_commit_loss_weight` and `commitment_weight` with the downstream reconstruction loss.

## `ResidualSimVQ`

Constructor signature:

```python
ResidualSimVQ(
    *,
    dim,
    num_quantizers,
    codebook_size,
    heads=1,
    quantize_dropout=False,
    quantize_dropout_cutoff_index=0,
    quantize_dropout_multiple_of=1,
    channel_first=False,
    rotation_trick=True,
    **sim_vq_kwargs,
)
```

Forward and helper:

```python
quantized, indices, losses = residual_sim_vq(x)
quantized, indices, losses, all_codes = residual_sim_vq(x, return_all_codes=True)
reconstructed = residual_sim_vq.get_output_from_indices(indices)
```

### Important constraints

- `heads` must be `1`; the implementation asserts that residual SimVQ is not compatible with multi-headed codes.
- `**sim_vq_kwargs` are forwarded to every internal `SimVQ` layer. This includes `codebook_transform`, `init_fn`, `input_to_quantize_commit_loss_weight`, `commitment_weight`, and `frozen_codebook_dim`.
- If you pass a stateful custom `codebook_transform`, remember that it is forwarded as provided. Use a deliberate sharing strategy, or build a custom stack manually if each residual layer needs an independently constructed transform.

### Shape contract

For `num_quantizers = Q`:

- `quantized` has the same shape as `x`.
- With `channel_first=False`, sequence indices are shaped `(batch, ..., Q)`, for example `(batch, length, Q)`.
- With `channel_first=True`, image indices are shaped `(batch, height, width, Q)`.
- `losses` is stacked across quantizers, normally shape `(Q,)` when each internal loss is scalar. Reduce it with `.sum()` or `.mean()` before combining with a scalar reconstruction objective.
- With `return_all_codes=True`, `all_codes` is shaped `(Q, batch, ..., dim)` for channel-last inputs and `(Q, batch, dim, ...)` for channel-first inputs.

### Quantize dropout and reconstruction

`quantize_dropout=True` only affects training and only when `num_quantizers > 1`.

- Dropped quantizer slots emit index value `-1` and zero loss.
- `get_output_from_indices` masks `-1` slots back to zero-valued residual contributions.
- If you pass fewer quantizer columns than `num_quantizers`, the helper pads the missing columns only when quantize dropout is enabled; otherwise it asserts.
- For deterministic reconstruction tests, disable quantize dropout or switch to evaluation mode before encoding.

## `HierarchicalVQ`

Constructor signature:

```python
HierarchicalVQ(
    *,
    dim,
    codebook_size,
    scales,
    decay=0.99,
    commitment_weight=1.0,
    rotation_trick=False,
    kmeans_init=True,
    kmeans_iters=10,
    threshold_ema_dead_code=2,
    stochastic_sample_codes=False,
    sample_codebook_temp=0.1,
    orthogonal_reg_weight=0.0,
    orthogonal_reg_max_codes=128,
    orthogonal_reg_active_codes_only=False,
    quant_resi=0.5,
    share_quant_resi=1,
    accept_image_fmap=False,
)
```

Forward and helper:

```python
reconstruction, index_list, commit_loss = hq(x)
reconstructed_from_indices = hq.get_output_from_indices(index_list)
```

### Required layout and scale contract

- `accept_image_fmap=True` is required; construction asserts otherwise.
- `x` must be a 4-D image feature map `(batch, channels, height, width)`.
- `channels` must equal `dim`.
- `scales` must be a non-empty sorted sequence of positive integers.
- Each scale quantizes an adaptive-average-pooled residual at `(scale, scale)`.
- The forward pass upsamples every scale contribution back to the input feature-map size before accumulating the reconstruction.
- For `get_output_from_indices`, pass a tuple or list with exactly `len(scales)` tensors. The helper reconstructs to `(batch, dim, scales[-1], scales[-1])`, so choose `scales[-1]` to match the full feature-map size when you need index-only reconstruction to match the original forward output shape.

### Return contract

- `reconstruction` has the same shape as `x` in the forward path.
- `index_list` is a tuple of per-scale index tensors. For `scales=(1, 2, 4)`, the shapes are usually `[(batch, 1, 1), (batch, 2, 2), (batch, 4, 4)]`.
- `commit_loss` is the mean of the per-scale commitment losses.
- `forward(indices=...)` is not implemented; use `get_output_from_indices(index_list)` for reconstruction from saved indices.

### Residual transform options

`HierarchicalVQ` adds an internal 2-D residual transform after upsampling each scale contribution.

- `quant_resi` controls the residual mixing ratio. Near zero behaves like identity; larger values mix in a learned 3x3 convolution.
- `share_quant_resi=1` shares one residual transform across all scales.
- `share_quant_resi<=0` creates one residual transform per scale.
- `share_quant_resi>1` creates up to that many residual transforms and maps scale positions across them.

### Underlying codebook options

`HierarchicalVQ` wraps `VectorQuantize` internally with `accept_image_fmap=True`. Constructor options such as `decay`, `kmeans_init`, `threshold_ema_dead_code`, `stochastic_sample_codes`, `sample_codebook_temp`, `orthogonal_reg_weight`, and `rotation_trick` are passed to that internal VQ module. For tiny CPU smoke tests, `kmeans_init=False` and `threshold_ema_dead_code=0` avoid data-dependent codebook initialization and stale-code replacement on very small batches.
