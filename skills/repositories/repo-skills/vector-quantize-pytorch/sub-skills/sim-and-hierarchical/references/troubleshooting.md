# SimVQ and HierarchicalVQ Troubleshooting

## `channel_first` shape errors

Symptoms:

- `assert x.shape == quantized.shape` fails.
- `indices` has a surprising shape.
- Reconstruction helper returns channel-last vectors when the decoder expects channel-first feature maps.

Fixes:

- For sequence tensors `(batch, length, dim)`, keep `channel_first=False`.
- For image or spatial feature maps `(batch, channels, height, width)`, set `channel_first=True` on `SimVQ` and `ResidualSimVQ`.
- `HierarchicalVQ` is always channel-first image-map based. It asserts `x.ndim == 4`, `channels == dim`, and `accept_image_fmap=True`.
- Expected index shapes:
  - `SimVQ(channel_first=False)`: `(batch, ...)`, usually `(batch, length)`.
  - `SimVQ(channel_first=True)`: `(batch, ...)`, usually `(batch, height, width)`.
  - `ResidualSimVQ(channel_first=True, num_quantizers=Q)`: `(batch, height, width, Q)`.
  - `HierarchicalVQ(scales=(1, 2, 4))`: tuple/list of `(batch, 1, 1)`, `(batch, 2, 2)`, `(batch, 4, 4)`.

## Reconstruction is not close enough

Symptoms:

- `torch.allclose(quantized, sim_vq.indices_to_codes(indices))` fails.
- `torch.allclose(quantized, residual_sim_vq.get_output_from_indices(indices))` fails.
- Hierarchical reconstruction from index list has the wrong shape.

Fixes:

- Use the same module instance or restore the exact same model state. SimVQ indices depend on the frozen buffer and transform weights.
- Compare immediately after encoding before an optimizer step, EMA update, or codebook-changing operation.
- For `SimVQ`, a tolerance around `atol=1e-6` is typical in float32.
- For `ResidualSimVQ`, use a slightly looser tolerance such as `atol=1e-5` because multiple residual code tensors are summed.
- Disable quantize dropout or switch to eval mode for deterministic residual reconstruction. If dropout is enabled, preserve `-1` index entries so the helper can mask dropped quantizers.
- For `HierarchicalVQ`, remember that the forward path returns the reconstruction accumulated at the original input size, while `get_output_from_indices` reconstructs to `(scales[-1], scales[-1])`. Set `scales[-1]` equal to the full feature-map height/width when exact shape is required.

## Hierarchical scales fail or produce odd outputs

Symptoms:

- Constructor assertions about `scales` fail.
- `get_output_from_indices` returns `(batch, dim, scales[-1], scales[-1])` instead of the original feature-map shape.
- Index-list tensors have unexpected sizes.

Fixes:

- `scales` must be non-empty, sorted, positive integers.
- Use square latent feature maps when you need index-only reconstruction. The helper does not store the original non-square `height, width`; it uses the last scale.
- End the schedule at the latent feature-map size: for `4x4`, use `(1, 2, 4)`; for `7x7`, use `(1, 2, 4, 7)`; for `8x8`, use `(1, 2, 4, 8)`.
- Adaptive average pooling means scales do not have to divide the input size exactly, but a scale schedule that exceeds or omits the full latent size can make saved-index reconstruction hard to reason about.
- If a convolutional encoder changes image resolution, compute the latent size after all striding/pooling before choosing `scales`.

## Hierarchical index-list length mismatch

Symptoms:

- `get_output_from_indices` asserts that the input is a tuple/list.
- `get_output_from_indices` asserts that the list length equals `len(scales)`.
- A later decoder receives only one scale's codes.

Fixes:

- Do not stack or concatenate HierarchicalVQ indices into one tensor before reconstruction.
- Store the returned `index_list` as an ordered tuple/list, one tensor per scale.
- Preserve the exact order used by `scales`; coarse-to-fine order is part of the reconstruction contract.
- Verify:

```python
quantized, index_list, loss = hq(x)
assert isinstance(index_list, (tuple, list))
assert len(index_list) == len(hq.scales)
assert [idx.shape[-2:] for idx in index_list] == [(s, s) for s in hq.scales]
```

## Commitment loss is not finite or has the wrong shape

Symptoms:

- `torch.isfinite(commit_loss).all()` fails.
- Training code expects a scalar but receives a vector.
- Loss scale dominates the reconstruction objective.

Fixes:

- Check input tensors for NaN/Inf before quantization.
- `SimVQ` returns a scalar commitment loss.
- `ResidualSimVQ` returns per-quantizer losses, usually shape `(num_quantizers,)`; reduce with `.sum()` or `.mean()` before combining with scalar losses.
- `HierarchicalVQ` returns the mean of per-scale commitment losses.
- For tiny synthetic HierarchicalVQ checks, set `kmeans_init=False`, lower `codebook_size`, and set `threshold_ema_dead_code=0` to avoid data-dependent initialization or stale-code replacement overwhelming a small batch.
- Tune `commitment_weight`, `input_to_quantize_commit_loss_weight`, or the downstream multiplier when training diverges.

## Frozen or implicit codebook confusion

Symptoms:

- Updating only the codebook buffer does not improve results.
- Saved indices decode differently after reinitializing a model.
- A custom transform raises matrix shape errors.

Fixes:

- In `SimVQ`, the registered frozen codebook is a buffer. The effective codebook is `codebook_transform(frozen_codebook)`.
- The transform module is the learned part unless you freeze its parameters yourself.
- `frozen_codebook_dim` must match the transform input dimension; the transform output dimension must equal `dim`.
- `init_fn` initializes the frozen buffer at construction. It is not called during every forward pass.
- Save the full model state if you plan to store and decode indices later.

## `ResidualSimVQ` constructor assertions

Symptoms:

- Construction fails when `heads` is greater than one.
- Reconstruction from shorter index tensors asserts.

Fixes:

- Keep `heads=1`; multi-headed residual SimVQ is explicitly unsupported.
- If you need multi-headed classic residual quantization, route to the classic residual quantizer sub-skill instead.
- Passing shorter residual index tensors is only supported with quantize dropout enabled. Otherwise provide the full final quantizer axis of length `num_quantizers`.

## `HierarchicalVQ.forward(indices=...)` assertion

Symptoms:

- Calling `hq(x, indices=saved_indices)` fails with `reconstruction-from-indices path not implemented in forward`.

Fix:

- Encode with `hq(x)` and reconstruct saved indices with `hq.get_output_from_indices(index_list)`.
- If a training loop needs teacher-forced or externally supplied indices, implement that outside this helper or route to lower-level `VectorQuantize` APIs.

## `quant_resi` and `share_quant_resi` surprises

Symptoms:

- Changing `quant_resi` changes reconstruction even with the same indices.
- Different scale levels seem to share or not share the same residual transform.

Fixes:

- `quant_resi` is the residual-mixing ratio for a 3x3 convolutional transform applied after upsampling each scale's codes. Near zero behaves close to identity.
- `share_quant_resi=1` uses one shared transform for all scales.
- `share_quant_resi<=0` uses one transform per scale.
- `share_quant_resi>1` creates a limited set of transforms and maps scale positions across that set.
- Because these transforms are learned parameters, saved indices require the matching trained `HierarchicalVQ` state for faithful decoding.
