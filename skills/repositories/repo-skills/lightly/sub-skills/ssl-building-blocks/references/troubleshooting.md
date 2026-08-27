# Troubleshooting

Use this as the first-pass checklist when a Lightly component stack fails.
Most issues reduce to a shape mismatch, a missing optional extra, or a distributed flag used in a single-process run.

| Symptom | Likely cause | Fix |
|---|---|---|
| `mat1 and mat2 shapes cannot be multiplied` or similar shape errors in a head | Backbone feature width does not match the projection/prediction head `input_dim` | Inspect a tiny forward pass, then set the head input width to the backbone output width instead of forcing the loss to compensate. |
| `too many values to unpack`, `expected 2 views`, or unexpected list lengths | The transform family and the loss family do not agree on arity | Two-view methods usually want SimCLR/BYOL/SimSiam/MoCo/VICReg-style views; DINO/SwaV/MSN/iBOT-style methods need multi-crop outputs; MAE-style methods often return a single view or masks. |
| Loss becomes `nan` or `inf` | Bad synthetic input, an aggressive temperature, or an invalid normalization path | Start from the default loss settings, verify `torch.isfinite(...)` on the synthetic tensors, and shrink the problem to a minimal two-sample smoke. |
| `gather_distributed=True` fails or hangs | `torch.distributed` is unavailable or not initialized | Keep `gather_distributed=False` for single-process smoke checks. Only enable it after the distributed process group is ready. |
| Memory bank behavior looks inconsistent | The bank size was passed as a bare integer or the feature width does not match the bank | Prefer `size=(num_entries, feature_dim)` for memory banks and keep the feature width identical to the head output width. |
| `lightly.models.modules` is missing TIMM/ViT helpers | Optional `lightly[timm]` support is not installed, or torchvision ViT support is unavailable | Install `lightly[timm]` when you need TIMM-backed MAE/I-JEPA/ViT helpers. Guard imports when the extra is optional. |
| Video folders are rejected or a video-specific error appears | Optional video support is missing | Install `lightly[video]` and the required video backend. If the task only needs image folders, keep the video branch out of scope. |
| Deprecated wrapper warnings appear from `lightly.models.*` | A legacy convenience wrapper is being used | Switch to explicit low-level composition with `lightly.data`, `lightly.transforms`, `lightly.loss`, and `lightly.models.modules`. |
| `dump()` refuses to export a dataset | The dataset still has transforms attached | Create a transformless dataset for export, or build a separate dataset object just for dumping. |
| `LightlyDataset` behaves like plain images when you expected video semantics | The directory does not contain videos, or the optional video branch is absent | Check the input folder contents and only expect video behavior when the video extra is installed. |
| The collate output has the wrong number of batches | A custom transform returns a different number of views than the collate or method expects | Check the transform arity first, then choose the collate helper that preserves that arity. |

## Fast triage order

1. Confirm the transform output length.
2. Confirm the head input width.
3. Confirm the loss receives tensors with the expected shape.
4. Confirm optional backends only when the method actually needs them.

## Smoke-script reminder

If you just need to check that the base component stack is wired correctly, use the bundled smoke script on synthetic data rather than reaching for a download-based example.
