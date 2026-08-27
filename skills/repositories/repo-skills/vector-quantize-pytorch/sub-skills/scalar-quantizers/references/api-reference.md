# Scalar Quantizer API Reference

This reference covers scalar-discretization classes exported by `vector_quantize_pytorch`: `FSQ`, `FSP`, `ResidualFSQ`, and `GroupedResidualFSQ`. These classes discretize scalar coordinates rather than learning a nearest-neighbor codebook.

## Shared concepts

### `levels` and codebook dimension

`levels` is a list or tuple of bin counts, one per scalar coordinate. Its length is the scalar `codebook_dim`.

- Flat codebook size is the product of all levels, e.g. `[8, 5, 5, 5]` has `8 * 5 * 5 * 5 = 1000` possible flat indices.
- Flat indices use mixed-radix encoding: the first coordinate is multiplied by `1`, the second by `levels[0]`, the third by `levels[0] * levels[1]`, and so on. For `[8, 5, 5, 5]`, level indices `[7, 4, 4, 4]` encode to `999`.
- `dim` is the input/output feature dimension. When it differs from the scalar codebook dimension, the module inserts learned linear projections around the scalar quantizer.

### Layout conventions

- Sequence tensors usually use `(batch, sequence, dim)`.
- Channel-first image or feature-map tensors use `(batch, channels, *spatial)`.
- Index tensors omit the feature dimension and may add codebook or residual axes depending on the class.

### Reconstruction checks

- Use exact equality only for deterministic FSQ cases without projection, quantization noise, or low-precision effects.
- Use `torch.allclose` for projected layers, FSP, low precision, autocast, and residual workflows.
- FSP training with stochastic perturbation can produce outputs that intentionally do not reconstruct from indices; switch to `.eval()` or use `quantize_rate=1.0` when checking index roundtrips.

## `FSQ`

Constructor:

```python
FSQ(
    levels: list[int] | tuple[int, ...],
    dim: int | None = None,
    num_codebooks=1,
    keep_num_codebooks_dim: bool | None = None,
    scale: float | None = None,
    allowed_dtypes: tuple[torch.dtype, ...] = (torch.float32, torch.float64),
    channel_first=False,
    projection_has_bias=True,
    return_indices=True,
    force_quantization_f32=True,
    preserve_symmetry=False,
    noise_dropout=0.0,
    bound_hard_clamp=False,
    orthogonal_rotation=False,
)
```

Forward:

```python
quantized, indices = fsq(z)
```

### Core behavior

- `codebook_dim = len(levels)`.
- `effective_codebook_dim = codebook_dim * num_codebooks`.
- Default `dim` is `effective_codebook_dim`.
- If `dim != effective_codebook_dim`, `project_in` and `project_out` are learned linear layers; otherwise they are identity modules.
- `return_indices=True` registers an implicit codebook and exposes `codebook_size = prod(levels)`. With `return_indices=False`, forward still returns a two-tuple but the second value is `None`.
- `num_codebooks > 1` requires keeping the codebook axis in the index tensor. The default `keep_num_codebooks_dim` becomes `True` when `num_codebooks > 1`.

### Input and output shapes

| Setup | Input shape | `quantized` shape | `indices` shape |
|---|---:|---:|---:|
| Sequence, one codebook | `(B, N, dim)` | `(B, N, dim)` | `(B, N)` |
| Sequence, `num_codebooks=C` | `(B, N, dim)` | `(B, N, dim)` | `(B, N, C)` |
| Channel-first sequence, `channel_first=True` | `(B, dim, N)` | `(B, dim, N)` | `(B, N)` or `(B, N, C)` |
| 4D+ feature map | `(B, dim, *spatial)` | same as input | `(B, *spatial)` or `(B, *spatial, C)` |
| `return_indices=False` | any valid input | same as input | `None` |

FSQ treats any 4D or higher tensor as a channel-first feature map. Set `channel_first=True` when a lower-rank tensor, such as `(B, dim, N)`, should also be interpreted as channel-first.

### Index helpers

```python
level_indices = fsq.indices_to_level_indices(indices)
indices = fsq.codes_to_indices(codes)
codes = fsq.indices_to_codes(indices)
```

- `indices_to_level_indices(indices)` decodes flat indices to per-level coordinates with final dimension `codebook_dim`.
- `codes_to_indices(codes)` expects normalized scalar codes with final dimension `codebook_dim`.
- `indices_to_codes(indices)` applies inverse scaling, optional inverse orthogonal rotation, codebook-axis flattening, `project_out`, and channel-first restoration. It requires non-`None` indices.

### Important options

- `preserve_symmetry=True` uses symmetry-preserving scalar bins. It is required when any level equals `2`; otherwise construction asserts.
- `noise_dropout > 0` is only valid with `preserve_symmetry=True`; it adds training-time random scalar offsets after quantization.
- `bound_hard_clamp=True` clamps to `[-1, 1]` instead of using tanh-style bounding. This is mainly useful when an upstream residual path already soft-clamps values.
- `orthogonal_rotation=True` rotates scalar coordinates before quantization and rotates codes back after quantization. It is intended for symmetric levels; asymmetric levels may warn because utilization can be harder to reason about.
- `force_quantization_f32=True` casts unsupported quantization dtypes to float32 inside the quantization step and casts codes back to the original dtype after quantization.

## `FSP`

Constructor:

```python
FSP(
    levels: list[int] | tuple[int, ...],
    dim: int | None = None,
    channel_first=False,
    projection_has_bias=True,
    act_name="tanh",
    quantize_rate=0.0,
    need_inv_act=False,
    vector_norm="var_tanh",
)
```

Forward:

```python
quantized, indices, norm_loss, other_info = fsp(z, eps=None)
```

### Core behavior

- `codebook_dim = len(levels)` and default `dim = codebook_dim`.
- If `dim != codebook_dim`, `project_in` and `project_out` are learned linear projections.
- `act_name` chooses a CDF-like activation that maps scalars to `(0, 1)` before binning.
- `quantize_rate` must be between `0.0` and `1.0`. In training mode, values below `1.0` mix stochastic perturbation with bin-center quantization. In eval mode, FSP behaves as if `quantize_rate=1.0` for deterministic quantization.
- `vector_norm` adds a statistical regularization loss returned as `norm_loss`; choose `"none"` for a zero regularizer.
- `need_inv_act=True` applies the inverse CDF to bin centers; otherwise FSP rescales bin centers with a fixed variance-normalizing constant.

### Valid choices

`act_name` choices:

- `"tanh"`
- `"sigmoid"`
- `"normal"`
- `"laplace"`
- `"cauchy"`

`vector_norm` choices:

- `"none"`
- `"var"`
- `"kurt"`
- `"var_tanh"`
- `"var_sigmoid"`
- `"var_laplace"`

### Input and output shapes

| Setup | Input shape | `quantized` shape | `indices` shape |
|---|---:|---:|---:|
| Sequence | `(B, N, dim)` | `(B, N, dim)` | `(B, N)` |
| Projected sequence | `(B, N, dim)` where `dim != len(levels)` | `(B, N, dim)` | `(B, N)` |
| Channel-first image, `channel_first=True` | `(B, dim, H, W)` | `(B, dim, H, W)` | `(B, H, W)` |

Unlike FSQ, FSP only treats NCHW-style inputs as channel-first when `channel_first=True` is set.

### Return tuple

- `quantized`: same shape and dtype as the input in supported precision modes.
- `indices`: flat mixed-radix indices, usually `torch.int32`.
- `norm_loss`: scalar tensor from the selected `vector_norm` preset.
- `other_info`: dictionary containing at least `level_indices` and `norm_info`; in stochastic training it can also include `p_accept_prob`.

### Index helpers

```python
flat = fsp.level_indices_to_indices(level_indices)
level_indices = fsp.indices_to_level_indices(flat)
act_values = fsp.indices_to_act_value(flat)
codes = fsp.indices_to_codes(flat, eps=1e-6)
```

`indices_to_codes` applies the same inverse activation or fixed rescaling path and `project_out` used by forward. Eval-mode outputs should roundtrip with `torch.allclose(quantized, fsp.indices_to_codes(indices), atol=...)`.

## `ResidualFSQ`

Constructor:

```python
ResidualFSQ(
    *,
    levels: list[int],
    num_quantizers,
    dim=None,
    is_channel_first=False,
    quantize_dropout=False,
    quantize_dropout_cutoff_index=0,
    quantize_dropout_multiple_of=1,
    soft_clamp_input_value: float | list[float] | Tensor | None = None,
    bound_hard_clamp=True,
    **kwargs,
)
```

Forward:

```python
quantized, indices = residual_fsq(x)
quantized, indices, all_codes = residual_fsq(x, return_all_codes=True)
```

### Core behavior

- Builds `num_quantizers` FSQ layers over residuals.
- Internally each FSQ layer uses `dim=len(levels)`, `preserve_symmetry=True`, and the configured `bound_hard_clamp`.
- If outer `dim != len(levels)`, ResidualFSQ learns `project_in` and `project_out` layers around the residual scalar stack.
- `codebook_size` is the product of `levels`; each residual stage uses the same scalar index range.
- With default `bound_hard_clamp=True`, `soft_clamp_input_value` is auto-derived from levels and must not be supplied at the same time.

### Shapes and helpers

| Setup | Input shape | `quantized` shape | `indices` shape | `all_codes` shape |
|---|---:|---:|---:|---:|
| Sequence | `(B, N, dim)` | `(B, N, dim)` | `(B, N, num_quantizers)` | `(num_quantizers, B, N, len(levels))` |
| Channel-first, `is_channel_first=True` | `(B, dim, *spatial_or_steps)` | same as input | quantizer axis is channel-first in returned indices | same semantic axes before output reconstruction |

Helpers:

```python
codes = residual_fsq.get_codes_from_indices(indices)
reconstructed = residual_fsq.get_output_from_indices(indices)
```

`get_output_from_indices` sums per-stage residual codes and applies `project_out`. In eval mode without dropout, it should reconstruct the forward output with exact equality or `torch.allclose`, depending on projection and dtype.

### Quantize dropout

When `quantize_dropout=True`, dropout only happens in training mode while gradients are enabled and `num_quantizers > 1`. Dropped stages are represented with `-1` indices. Reconstruction from a coarse index tensor is only supported when the model was configured with quantize dropout.

## `GroupedResidualFSQ`

Constructor:

```python
GroupedResidualFSQ(
    *,
    dim,
    groups=1,
    accept_image_fmap=False,
    **kwargs,
)
```

Forward:

```python
quantized, indices = grouped_residual_fsq(x)
quantized, indices, grouped_all_codes = grouped_residual_fsq(x, return_all_codes=True)
```

### Core behavior

- Requires `dim % groups == 0`.
- Splits the feature dimension into `groups`; each group owns a `ResidualFSQ(dim=dim // groups, **kwargs)`.
- `codebook_size` is inherited from the first group.
- `codebooks` stacks per-group residual scalar codebooks.

### Verified sequence shape contract

For standard sequence tensors with `accept_image_fmap=False`:

| Input | `quantized` | `indices` | Reconstruction |
|---|---|---|---|
| `(B, N, dim)` | `(B, N, dim)` | `(groups, B, N, num_quantizers)` | `grouped_residual_fsq.get_output_from_indices(indices)` returns `(B, N, dim)` |

### Image-map caution

`accept_image_fmap=True` changes the split dimension to channels for image-like tensors. In this package snapshot, this path is shape-fragile because the inner `ResidualFSQ` instances still need consistent channel-first handling. If it raises a projection or axis-size error for NCHW tensors, flatten the spatial map to a sequence, use `accept_image_fmap=False`, then reshape the quantized output back to image layout.
