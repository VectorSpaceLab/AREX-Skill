# Troubleshooting 2D Image Architectures

## Purpose

Use this reference when a fixed-size image classifier constructor or forward pass fails. The fixes target image-only `vit-pytorch` backbones and variants. If the failure involves variable-resolution lists, videos/3D/N-D tensors, pretraining losses, custom transformer wrappers, attention maps, or embeddings, route to the owning sub-skill named in `SKILL.md`.

## Start with the bundled smoke helper

Run a tiny deterministic check before scaling dimensions:

```bash
python scripts/smoke_image_architectures.py --case quick
python scripts/smoke_image_architectures.py --case errors
```

`--case quick` verifies representative logits shapes with CPU random tensors. `--case errors` intentionally checks the expected repair path for non-divisible patch sizes and invalid pooling choices.

## Image-size and patch-size divisibility errors

| Symptom or fragment | Likely cause | Repair |
|---|---|---|
| `Image dimensions must be divisible by the patch size.` | For patch-based families, `height % patch_height != 0` or `width % patch_width != 0`. | Choose an `image_size` and `patch_size` pair that divides exactly. For `32x32`, try `patch_size=4` or `8`; for `64x64`, try `patch_size=8` or `16`. If images are rectangular, pass tuples such as `image_size=(height, width)` and `patch_size=(patch_h, patch_w)` only for classes whose source supports `pair(...)` tuple handling. |
| Shape mismatch inside `einops` / `Rearrange` | The constructor passed, but an intermediate stage/window cannot divide the feature map. | Reduce to a known tiny pattern from `scripts/smoke_image_architectures.py`, then change one parameter at a time. For windowed or hierarchical families, check every downsampled stage, not only the original input. |
| `height ... and width ... must be divisible by window size ...` | Windowed attention family such as MaxViT, SepViT, RegionViT, CrossFormer, or similar cannot partition a feature map. | Pick an input size and window size compatible with all stages. Example: tiny MaxViT works with `64x64` and `window_size=2`; README-style `window_size=7` generally needs README-scale spatial sizes. |
| `height and width must be divisible by region patch size` | `RegionViT` requires divisibility by `local_patch_size * window_size` and by `local_patch_size`. | Compute `region_patch_size = local_patch_size * window_size` and make both height and width multiples of that value. |

Repair sequence for user code:

1. Print or inspect the image tensor shape: it must be `(batch, channels, height, width)`.
2. Match `channels` in the constructor to the tensor channel count when the class exposes `channels`; many models default to `3`.
3. For patch models, compute `height // patch_height` and `width // patch_width`; both divisions must be exact.
4. Use a tiny known-good constructor with the same family; then restore the user's `num_classes`, `channels`, and scale parameters gradually.

## Invalid pool choice or head assumptions

| Symptom or fragment | Likely cause | Repair |
|---|---|---|
| `pool type must be either cls (cls token) or mean (mean pooling)` | `pool` was not `cls` or `mean` for a base ViT-style constructor. | Use `pool='cls'` for CLS-token pooling or `pool='mean'` for mean pooling. Do not pass `avg`, `gap`, `token`, `none`, or booleans. |
| `__init__() got an unexpected keyword argument 'pool'` | The selected family hard-codes pooling and does not expose `pool`. | Remove `pool` and read the family row in `model-overview.md`. SimpleViT-style models usually mean-pool; many hierarchical models global-average-pool. |
| Forward returns a token sequence instead of logits | Some base ViT-style sources set `mlp_head=None` when `num_classes <= 0`. | For classification, set `num_classes` to a positive integer. If the user wants token features, route to the introspection/customization skill instead of treating it as a classifier-head issue. |
| Forward returns `(logits, distill_logits)` | `LeViT` was constructed with `num_distill_classes`. | For ordinary image classification, leave `num_distill_classes=None`. If the user is training a distillation objective, route to pretraining/adaptation. |

## Constructor mismatch across families

Most families do not share the base `ViT` signature. Do not mechanically copy `image_size`, `patch_size`, `dim`, `depth`, `heads`, and `mlp_dim` across the catalog.

| Failed family | Common wrong assumption | Correct pattern |
|---|---|---|
| `CCT` | Passing `patch_size` or expecting plain token patching. | Use convolutional tokenizer parameters such as `img_size`, `embedding_dim`, `n_conv_layers`, `kernel_size`, `stride`, `pooling_*`, plus transformer kwargs `num_layers`, `num_heads`, `mlp_ratio`, `num_classes`, and `positional_embedding`. |
| `CrossViT` | Passing one `patch_size` and one `dim`. | Use `sm_dim`, `sm_patch_size`, `sm_enc_*` and `lg_dim`, `lg_patch_size`, `lg_enc_*`, plus cross-attention parameters. |
| `PiT`, `TwinsSVT`, `RegionViT`, `CrossFormer`, `ScalableViT`, `SepViT`, `MaxViT`, `NesT` | Treating stage depth/head/dim values as one scalar in every context. | These families use tuple or stage-prefixed parameters. Align tuple lengths with the number of stages and keep intermediate feature-map divisibility in mind. |
| `MobileViT` | Supplying base ViT arguments. | Use `MobileViT(image_size=(h, w), dims=[...3 values...], channels=[...staged channel list...], num_classes=..., depths=(...3 values...))`. |
| Normalized/look/rotary/detpool variants | Importing `ViT` from every module. | Use exact class names: `nViT`, `LookViT`, `RvT`, and `ViTDetPool`. |
| QK-norm / relative-position / specialized-CLS / value-residual variants | Importing nonexistent plain `vit_with_*` modules. | In this snapshot, use `simple_vit_with_qk_norm`, `simple_vit_with_relative_proj_pos_bias`, `simple_vit_with_specialized_cls`, and `simple_vit_with_value_residual`. |

When repairing a constructor mismatch, first check `model-overview.md` for the exact import and signature shape, then run a tiny constructor from the smoke helper or adapt its parameters.

## Memory-heavy defaults copied from README examples

README snippets often demonstrate paper-scale or ImageNet-scale models: `image_size=224` or `256`, `dim=512` to `1024`, `depth=6` or more, many heads, and `mlp_dim=2048` or `3072`. These are not necessary for API repair.

Safe downscaling rules:

- Use `batch=1`, `num_classes=2` to `10`, `dim=32` or `64`, `depth=1`, `heads=2`, `dim_head=16`, and `mlp_dim=64` or `128` for patch-based smoke tests.
- Keep the number of tokens manageable: `(image_size // patch_size) ** 2` for square patch models. On `32x32`, `patch_size=8` gives 16 tokens; `patch_size=4` gives 64 tokens.
- For SimpleViT and SimpleViT-style variants, keep `dim` divisible by 4. Avoid `dim=4` because sinusoidal embedding construction divides by `dim // 4 - 1`; use at least `dim=8`, usually `32`.
- For hierarchical families, shrink `depth` before shrinking required spatial size. Some windowed implementations need specific spatial multiples even with tiny `dim`.
- Call `.eval()` during smoke checks for models with BatchNorm layers, especially `MobileViT` and convolution-heavy families with batch size 1.
- Do not run training loops or download datasets while debugging constructor shapes.

## Variant-specific pitfalls

### Patch dropout

- `patch_dropout` must be `0 <= patch_dropout < 1`.
- Patch dropout has no effect in `.eval()` mode and is active in `.train()` mode.
- If the user expects deterministic training outputs, set seeds and consider disabling patch dropout for debugging.

### Patch merger

- `vit_with_patch_merger.ViT` uses `patch_merge_layer` to choose where token reduction happens. Internally it subtracts 1, so `patch_merge_layer=1` merges after the first transformer layer.
- `patch_merge_num_tokens` should be smaller than or equal to the pre-merge patch-token count for an intuitive reduction, although the module can produce the requested number of learned query outputs.
- Standalone `PatchMerger(dim, num_tokens_out)` expects input shaped `(batch, tokens, dim)` and returns `(batch, num_tokens_out, dim)`.

### SimpleViT-style sin/cos variants

- `SimpleViT`, QK-norm, relative projected position bias, value residual, patch dropout, register-token, sparse-gating, and flash variants require `dim % 4 == 0` for 2D sinusoidal position embeddings.
- If the user sees `feature dimension must be multiple of 4 for sincos emb`, change `dim` to 32/64/128 before modifying heads or patch size.

### Flash-attention SimpleViT

- `simple_flash_attn_vit.SimpleViT` uses PyTorch scaled-dot-product attention when `use_flash=True`. The package requires PyTorch 2.4 in this snapshot, so the version gate is satisfied in the verified environment.
- On CPU, `use_flash=True` still routes through PyTorch SDPA-compatible code and may emit a deprecation warning from PyTorch's `sdp_kernel` context manager; that warning is not a shape failure.
- In this source snapshot, setting `use_flash=False` reaches a fallback branch that calls `einsum` without importing it, causing `NameError: name 'einsum' is not defined`. Use ordinary `SimpleViT` if the user wants to avoid SDPA, or keep `use_flash=True` for the flash variant.

### SepViT window size

- The constructor exposes `window_size`, but source inspection shows the staged transformer path does not pass that value into the `DSSA` attention constructor in this snapshot, so the internal default window size can still govern divisibility.
- If tiny non-README shapes fail with a window divisibility assertion, either use a verified shape or select another hierarchical family for small-memory experiments.

### MaxViT and other windowed models

- MaxViT has no `image_size` constructor argument; the error often appears only on the first forward pass.
- For tiny smoke tests, `MaxViT(num_classes=..., dim=16, dim_head=8, depth=(1,1,1,1), window_size=2)` with a `64x64` tensor is a known small pattern.
- If a README `window_size=7` fails on small inputs, do not blindly pad; choose a compatible image size or a smaller window where the source honors it.

### MobileViT

- Constructor asserts `len(dims) == 3` and `len(depths) == 3` and indexes a staged `channels` list. Use a complete channel list rather than a scalar.
- Use `.eval()` for batch-1 smoke tests to avoid BatchNorm training-mode issues.

## When to stop and route elsewhere

- Input is a list of images with different resolutions, or the user mentions NaViT grouping / nested tensors: route to `variable-shapes-video`.
- Input has shape `(batch, channels, frames, height, width)` or the user mentions 3D/ViViT/video/medical volumes: route to `variable-shapes-video`.
- The desired output is loss, reconstruction, distillation logits, teacher/student updates, or masked prediction: route to `pretraining-and-adaptation`.
- The desired output is attention maps, embeddings, hook cleanup, custom transformer injection, or external efficient-attention wrappers: route to `introspection-and-customization`.
