# Scalar Quantizer Troubleshooting

Use this guide for FSQ, FSP, ResidualFSQ, and GroupedResidualFSQ failures involving return tuples, shapes, indices, projections, activation/norm options, dtype/autocast, and reconstruction checks.

## Quick diagnosis table

| Symptom | Likely cause | Fix |
|---|---|---|
| `ValueError: too many values to unpack` or `not enough values to unpack` | Confusing FSQ and FSP return tuples | FSQ and residual FSQ return two values by default. FSP returns four values: `quantized, indices, norm_loss, other_info`. |
| `indices is None` or `indices_to_codes` assertion | `FSQ(return_indices=False)` was used | Keep `return_indices=True` for workflows that need `indices_to_codes`, storage, or tokenization. |
| `expected dimension of ... but found dimension ...` | `dim`, `levels`, `num_codebooks`, or tensor layout does not match the class shape contract | Recompute expected feature dimension: FSQ default is `len(levels) * num_codebooks`; FSP default is `len(levels)`; residual wrappers use outer `dim`. Set `channel_first` or reshape tensors as needed. |
| Projection error like `mat1 and mat2 shapes cannot be multiplied` | The feature dimension that reaches a `Linear` projection is not the configured `dim` | Check whether the tensor is channel-last or channel-first. For images with FSP use `channel_first=True`; for grouped image residuals consider flattening to sequence layout. |
| FSP constructor assertion for `act_name` | Unsupported CDF activation | Use one of `tanh`, `sigmoid`, `normal`, `laplace`, or `cauchy`. |
| FSP constructor assertion for `vector_norm` | Unsupported norm preset | Use one of `none`, `var`, `kurt`, `var_tanh`, `var_sigmoid`, or `var_laplace`. |
| FSP constructor assertion for `quantize_rate` | Rate outside `[0, 1]` | Clamp or validate the configured rate before constructing FSP. |
| FSP train output does not equal `indices_to_codes(indices)` | Training perturbation is active | Switch to `.eval()` for deterministic quantization, or set `quantize_rate=1.0` for no stochastic perturbation during training checks. |
| Reconstruction exact equality fails with projections or low precision | Floating-point projection/autocast differences | Use `torch.allclose(..., atol=1e-5)` or a looser tolerance such as `1e-4` for projected FSP. |
| FSQ assertion when a level equals `2` | Symmetry preservation is required for two-level scalar bins | Set `preserve_symmetry=True` or use levels greater than `2`. |
| FSQ assertion with `noise_dropout > 0` | Noise dropout requires symmetry-preserving quantization | Set `preserve_symmetry=True`, or disable `noise_dropout`. |
| Warning about `orthogonal_rotation` and asymmetric levels | Rotation is intended for symmetric level lists | Prefer symmetric levels such as `[4, 4, 4, 4]` when using `orthogonal_rotation=True`, or leave rotation off. |
| ResidualFSQ construction assertion involving `soft_clamp_input_value` | `bound_hard_clamp=True` auto-derives soft clamp values and forbids a manual value | Either omit `soft_clamp_input_value`, or set `bound_hard_clamp=False` before supplying a custom clamp value. |
| Residual indices contain `-1` | Quantize dropout skipped later residual stages during training | This is expected with `quantize_dropout=True`. For deterministic reconstruction checks use eval mode; for coarse reconstruction ensure the model was configured with quantize dropout. |
| `GroupedResidualFSQ` assertion on `dim % groups` | Feature dimension cannot be split evenly | Choose a group count that divides `dim`, or add a projection before the grouped quantizer. |
| Grouped image-map path fails with axis-size/projection error | `accept_image_fmap=True` changes the split axis but inner residual shape handling can still be fragile | Flatten NCHW to `(B, H*W, C)`, run `GroupedResidualFSQ(accept_image_fmap=False)`, then reshape back. |

## Return tuple confusion

Keep the unpacking explicit:

```python
# FSQ
quantized, indices = fsq(x)

# ResidualFSQ / GroupedResidualFSQ by default
quantized, indices = residual(x)

# ResidualFSQ / GroupedResidualFSQ with all codes
quantized, indices, all_codes = residual(x, return_all_codes=True)

# FSP
quantized, indices, norm_loss, other_info = fsp(x)
```

If an FSP module is inserted into a generic `torch.nn.Sequential`, the next layer will receive a tuple rather than a tensor. Wrap it or unpack it manually before passing `quantized` onward.

## Levels, dimensions, and projection shape checks

Before constructing the module, write down the intended feature dimension:

```python
codebook_dim = len(levels)
```

Then apply class-specific rules:

- FSQ without `dim`: input feature dimension must be `len(levels) * num_codebooks`.
- FSQ with `dim`: input/output dimension is `dim`; internal scalar dimension is `len(levels) * num_codebooks`.
- FSP without `dim`: input feature dimension must be `len(levels)`.
- FSP with `dim`: input/output dimension is `dim`; internal scalar dimension is `len(levels)`.
- ResidualFSQ without `dim`: input feature dimension is `len(levels)`.
- ResidualFSQ with `dim`: input/output dimension is `dim`; internal residual scalar dimension is `len(levels)`.
- GroupedResidualFSQ: `dim` must be divisible by `groups`, and each group receives `dim // groups` features.

If a projection error appears, inspect the actual last dimension for sequence tensors or the channel dimension for channel-first tensors.

## Channel-first and image-layout fixes

FSQ:

- 4D+ inputs are treated as channel-first feature maps.
- Set `dim` equal to the channel count.
- Set `channel_first=True` for lower-rank channel-first tensors such as `(B, D, N)`.

FSP:

- Set `channel_first=True` for NCHW image inputs.
- Without `channel_first=True`, FSP expects the final axis to be the feature dimension.

ResidualFSQ:

- Set `is_channel_first=True` when the feature dimension is the channel axis.
- For unfamiliar high-rank layouts, flatten spatial axes to a sequence first, verify shapes, then reshape back.

GroupedResidualFSQ:

- Standard sequence layout `(B, N, D)` is the safest path.
- For NCHW tensors, a robust workaround is `x.permute(0, 2, 3, 1).reshape(B, H*W, C)`, quantize as a sequence, then reshape back.

## Index roundtrip pitfalls

### FSQ with no returned indices

```python
fsq = FSQ([8, 5, 5, 5], return_indices=False)
quantized, indices = fsq(x)
assert indices is None
```

This is correct behavior. Use `return_indices=True` if tokens or reconstruction from tokens are part of the workflow.

### FSP training perturbation

```python
fsp = FSP([8, 5, 5, 5], quantize_rate=0.0)
fsp.train()
quantized, indices, *_ = fsp(x)
# quantized may not equal fsp.indices_to_codes(indices)
```

In eval mode, the same class should be deterministic:

```python
fsp.eval()
quantized, indices, *_ = fsp(x)
assert torch.allclose(quantized, fsp.indices_to_codes(indices), atol=1e-5)
```

### Exact vs approximate reconstruction

Use exact equality only for deterministic FSQ without projections:

```python
assert torch.equal(quantized, fsq.indices_to_codes(indices))
```

Use allclose for projected or precision-sensitive workflows:

```python
assert torch.allclose(quantized, recovered, atol=1e-4)
```

## Dtype and autocast caveats

- FSQ defaults to doing the quantization step in float32 when the original dtype is outside its allowed dtype tuple. It casts codes back afterward, but numerical equality can still be dtype-sensitive.
- FSP uses `torch.finfo(z.dtype).eps` by default. Very low precision and inverse CDF mode can be sensitive near probability boundaries; pass a stable `eps` or run the quantizer in float32 if NaNs appear.
- When using autocast, check both the quantized tensor dtype and index validity:

```python
assert quantized.dtype == x.dtype
assert indices.dtype in (torch.int32, torch.int64)
assert torch.isfinite(quantized).all()
assert (indices >= 0).all()
```

## Activation and norm selection

Start conservative:

- `act_name="tanh"` and `vector_norm="var_tanh"` match FSP defaults.
- `act_name="normal"`, `vector_norm="none"` is useful for minimal shape/debug checks.
- Use `vector_norm="none"` when you only need the perturbation/roundtrip behavior and do not want an auxiliary statistical loss.

If `need_inv_act=True`, test with float32 first. Inverse CDFs can magnify values near `0` or `1`; FSP clamps with `eps`, but low precision can still reduce stability.

## Residual and grouped residual caveats

- Use `.eval()` for deterministic residual reconstruction from indices.
- If `quantize_dropout=True`, expect `-1` in skipped residual stages during gradient-enabled training. Store enough metadata to know whether an index tensor is full-depth or dropout-coarse.
- `return_all_codes=True` on `ResidualFSQ` returns an all-codes tensor shaped like `(num_quantizers, batch, sequence, len(levels))` for sequence inputs.
- `return_all_codes=True` on grouped residual workflows exposes per-group all-code structures; inspect shapes before assuming a single flat tensor.
- When groups are used, save the `groups`, `levels`, `num_quantizers`, and `dim` settings alongside indices. Grouped indices are not interchangeable with ungrouped residual indices.
