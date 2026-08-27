# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| padded positions show up as `-1` in `indices` | `mask` or `lens` was applied | This is expected. Strip padded positions before reconstruction or metrics. |
| quantized padding is all zeros | `return_zeros_for_masked_padding=True` | Leave it on for safe padded outputs, or disable it if you need the original input to remain visible at masked tokens. |
| shape or rearrange errors | input layout does not match the selected mode | Default is `(B, N, D)`. Use `channel_last=False` for `(B, D, N)`, `accept_image_fmap=True` for `(B, C, H, W)`, and `accept_3d_fmap=True` for `(B, C, D, H, W)`. |
| `mask` and `lens` both fail | both were passed | Use only one. `lens` is just a convenience wrapper for a sequence mask. |
| reconstruction from recorded indices does not match | the codebook changed after the indices were captured | Compare in `eval()` or with `freeze_codebook=True` if you need a stable round trip. |
| `update_ema_indices` seems to do nothing | the wrong index shape was passed, or `topk` output was not reduced first | Pass a single index tensor and use `indices[..., 0]` for top-k smoke paths. |
| top-k forward never updates the codebook | `topk` disables the automatic EMA path | Call `update_ema_indices` yourself if you want a manual count update. |
| counts update but the codebook vectors do not refresh | `manual_ema_update=True` defers the embed refresh | Leave `manual_ema_update=False` for the usual path, or refresh explicitly in the codebook workflow that owns the deferred update. |
| codebook dimension looks wrong | `codebook_dim` is an internal latent size, not the final output size | Remember that the module projects in and out around the codebook. The final output still uses `dim`. |
| multi-head outputs have an extra index axis | `heads > 1` | This is expected. Check whether the codebooks are shared or per-head before interpreting the indices. |
| `directional_reparam` assertion fires | stale-code replacement is off | Set `threshold_ema_dead_code` to a positive value. |
| FVQ bridge import or init fails | the optional bridge dependency is missing or the config is not learnable | Install the optional bridge dependency and use `learnable_codebook=True` with EMA off. |
| `RandomProjectionQuantizer` returns an index tensor, not a quantized tensor | that is the intended API | Call it without `indices` to get codes; pass `indices` to get the loss. |
| distributed sync behavior looks inconsistent | `sync_codebook` follows the distributed runtime by default | Leave the default in DDP, or force a local/global choice only when you know why. |
