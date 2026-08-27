# Workflows

## 1) Minimal sequence VQ

Use this when you want the standard single-stage codebook path.

1. Start with `VectorQuantize(dim=D, codebook_size=K)`.
2. Feed a tensor shaped `(B, N, D)`.
3. Keep the module in training mode if you want EMA updates and commitment loss.
4. Switch to eval mode and call `get_output_from_indices(indices)` when you need a stable reconstruction check.

Tiny pattern:

```python
vq = VectorQuantize(dim=8, codebook_size=16)
quantized, indices, loss = vq(x)
vq.eval()
assert torch.allclose(vq.get_output_from_indices(indices), vq(x)[0])
```

## 2) Variable-length batches

Use `lens` when lengths are easier to supply than an explicit mask.

- `mask` and `lens` are mutually exclusive.
- Padded positions become zero in the quantized output by default.
- Padded positions become `-1` in the index tensor.
- Use the same mask again when calling `update_ema_indices`.

Best practice:

1. Build the mask once.
2. Quantize the full batch with the mask or `lens`.
3. Strip padded indices before any manual reconstruction or index-level metrics.

## 3) Image and 3D feature maps

Use the feature-map flags when the quantizer sits in an image or volume pipeline.

- Image tensor shape: `(B, C, H, W)` with `accept_image_fmap=True`.
- 3D tensor shape: `(B, C, D, H, W)` with `accept_3d_fmap=True`.
- Do not use `mask` with these modes.
- Multi-headed image tokenization returns an extra trailing head dimension in the indices.

Good checks:

- output shape matches the input shape
- index shape matches spatial layout
- `get_output_from_indices` round-trips in eval mode

## 4) Codebook-usage tuning

When a codebook collapses or wastes capacity, tune one knob at a time.

1. Try `kmeans_init=True` if the first batch should seed the codebook.
2. Reduce `codebook_dim` if the codebook is too expressive.
3. Turn on `use_cosine_sim=True` if normalized matching is wanted.
4. Set `threshold_ema_dead_code` to a positive value to recycle stale entries.
5. Add `orthogonal_reg_weight` or `codebook_diversity_loss_weight` only after a baseline smoke passes.
6. For multi-headed VQ, confirm whether heads should share a codebook or not before changing the projection shape.

## 5) Gradient estimator choice

Choose one estimator path at a time.

- If you want a plain STE baseline, set `rotation_trick=False` and `directional_reparam=False` explicitly.
- `rotation_trick=True` changes the backward geometry without changing the forward codebook lookup.
- `directional_reparam=True` is the more specialized reparameterized path and should be paired with stale-code replacement.

## 6) Top-k and manual EMA updates

Use `topk=1` when you want to inspect the nearest alternative code while keeping the workload tiny.

- Automatic EMA updates are skipped when `topk` is active.
- If you want to update counts anyway, call `update_ema_indices(x, indices[..., 0], mask=mask)` yourself.
- `manual_ema_update=True` only defers the internal codebook refresh; it does not replace the manual helper.
- Compare the top-1 slice against the standard forward path in a controlled smoke to verify routing.

## 7) RandomProjectionQuantizer

Use this when the quantizer should stay non-learned.

1. Construct `RandomProjectionQuantizer(dim=..., codebook_dim=..., codebook_size=...)`.
2. Call it once to get indices.
3. Pass target indices back in when you want the cross-entropy loss.

This path is useful for speech-style masked prediction experiments where the codebook is fixed.

## 8) FVQ bridge guidance

Use the bridge only when you explicitly need the transformer-assisted FVQ path.

- The bridge dependency is optional.
- The bridge path expects a learnable codebook.
- The bridge path does not use EMA-style codebook updates in the usual way.
- Keep a tiny CPU smoke around the bridge config before any larger training run.
