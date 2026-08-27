# Model Overview for 2D Image Architectures

## Purpose

Read this when selecting a `vit-pytorch` image classification backbone for fixed-size image tensors. The guidance is distilled from README examples, source constructors, installed signature inspection, and tiny CPU smoke checks. It is self-contained: future agents can pick a model family from this generated skill tree.

## Hard boundary

This sub-skill covers models whose normal forward input is a single image tensor shaped `(batch, channels, height, width)` and whose normal output is logits shaped `(batch, num_classes)`. If the user asks for image lists, grouped variable-resolution packing, 1D/3D/N-D/video tensors, self-supervised losses, distillation wrappers, attention maps, embeddings, or external custom transformer wrappers, route to the sibling sub-skill named in `SKILL.md` instead of stretching this catalog.

## Quick selection map

| User goal | Start with | Why | Constructor notes |
|---|---|---|---|
| Plain baseline with learned positional embeddings and optional dropout | `from vit_pytorch import ViT` or `from vit_pytorch.vit import ViT` | Closest to the original ViT API; installed signature includes `pool='cls'`, `dropout`, and `emb_dropout`. | Requires exact image/patch divisibility. Valid pool values are `cls` and `mean`. Positive `num_classes` returns logits; non-positive `num_classes` returns token features in this source snapshot. |
| Simpler baseline with mean pooling | `from vit_pytorch import SimpleViT` or `from vit_pytorch.simple_vit import SimpleViT` | Uses fixed 2D sinusoidal positions, mean pooling, no dropout constructor arguments; good baseline when the user does not need CLS-token behavior. | `dim` must be a multiple of 4 for sinusoidal position embeddings. No `pool`, `dropout`, or `emb_dropout` constructor parameters. |
| Deeper plain transformer | `from vit_pytorch.deepvit import DeepViT` | Re-attention / talking-heads style variant for deeper ViTs while keeping the plain image classifier API. | Same patch divisibility and `pool` rules as base `ViT`; tune `depth` deliberately rather than copying large README settings. |
| Layer-scaled CLS-attention variant | `from vit_pytorch.cait import CaiT` | Separates patch-to-patch depth from CLS-attention depth and adds layer dropout. | Requires `depth` and `cls_depth`; no `pool` argument. Use tiny `depth=1`, `cls_depth=1` first for shape checks. |
| Overlapping tokenization | `from vit_pytorch.t2t import T2TViT` | Token-to-token front end unfolds/downsamples before the transformer. | Uses `image_size` and `t2t_layers` instead of a simple `patch_size` argument. Can accept a custom `transformer`, but custom wrappers should be routed elsewhere. |
| Compact / small-data baseline | `from vit_pytorch.cct import CCT` or `cct_2`, `cct_4`, `cct_6`, `cct_7`, `cct_8`, `cct_14`, `cct_16` | Convolutional tokenizer plus sequence pooling; often a safer small-image baseline than a huge vanilla ViT. | `CCT(img_size=..., embedding_dim=..., n_conv_layers=..., kernel_size=..., stride=..., num_layers=..., num_heads=..., mlp_ratio=..., num_classes=..., positional_embedding='learnable'|'sine'|'none')`. `img_size` may be an int or `(height, width)`. |
| Two image scales with cross attention | `from vit_pytorch.cross_vit import CrossViT` | Processes small-patch and large-patch streams, then cross-attends between them. | Uses `sm_*` and `lg_*` parameter groups; do not pass base `ViT`'s `patch_size`. Both patch sizes must divide `image_size`. |
| Token downsampling with pooling | `from vit_pytorch.pit import PiT` | Depth-wise convolutional token pooling between stages. | `depth` must be a tuple of stage depths. `patch_size` must divide `image_size`; the implementation unfolds with stride `patch_size // 2`, so very small patch sizes can be unusual. |
| Fast convolutional stem / staged architecture | `from vit_pytorch.levit import LeViT` | Convolutional embedding, staged dimensions, relative-position style attention, batchnorm-heavy design. | `dim`, `depth`, and `heads` can be scalars or tuples matching `stages`. If `num_distill_classes` is set, forward returns `(logits, distill_logits)` instead of one logits tensor. |
| Convolutional vision transformer | `from vit_pytorch.cvt import CvT` | Three staged convolution/attention blocks with convolutional QKV projections. | Uses prefixed stage parameters such as `s1_emb_dim`, `s1_depth`, `s2_*`, `s3_*`; no `image_size` constructor argument. |
| Local/global attention without shifted windows | `from vit_pytorch.twins_svt import TwinsSVT` | Stage-wise local and global attention plus positional encoding generator. | Uses `s1_*` through `s4_*` stage parameters. Patch and local patch sizes must divide intermediate feature maps. |
| Regional tokens and local windows | `from vit_pytorch.regionvit import RegionViT` | Divides the image into local tokens plus regional tokens. | Requires input height and width divisible by `local_patch_size * window_size`; `dim` and `depth` must be length-4 tuples or scalar-expanded in the source. |
| Alternating local/global windows | `from vit_pytorch.crossformer import CrossFormer` | Cross-scale embeddings plus local/global attention windows. | Uses tuple parameters for stage dims, depths, global windows, kernel sizes, and strides. Tiny shapes are possible, but dimensions must avoid zero-width grouped convolutions. |
| Scalable attention and interactive windows | `from vit_pytorch.scalable_vit import ScalableViT` | Staged Bytedance-style SSA/IWSA design for efficient local/global trade-offs. | Required parameters are `num_classes`, `dim`, `depth`, `heads`, and `reduction_factor`; tuple lengths should match stages. Window settings must fit the downsampled feature maps. |
| Depthwise separable self-attention | `from vit_pytorch.sep_vit import SepViT` | Bytedance-style depthwise-pointwise attention in staged feature maps. | Source signature accepts `window_size`, but the current transformer path uses the internal default window size in its attention block. Use README-scale shapes or verify carefully before promising unusual tiny window settings. |
| Hybrid convolution/block/grid attention | `from vit_pytorch.max_vit import MaxViT` | MBConv stem plus block and grid attention; useful when the user wants convolutional inductive bias. | No `image_size` constructor arg. Input spatial dimensions must stay divisible by `window_size` after staged downsampling. For tiny smoke checks, `64x64` with `window_size=2` works better than the README's large `window_size=7`. |
| Nested local hierarchy | `from vit_pytorch.nest import NesT` | Local block attention aggregated through hierarchies. | Constructor uses `image_size`, `patch_size`, `num_hierarchies`, and `block_repeats`; keep tuple lengths aligned. |
| Mobile-friendly model | `from vit_pytorch.mobile_vit import MobileViT` | MobileNetV2-style blocks plus transformer blocks. | Requires `image_size=(h, w)`, `dims` length 3, `channels` list long enough for all staged channels, and `depths` length 3. Set `.eval()` for tiny batch-1 smoke tests because BatchNorm layers are present. |
| Cross-covariance attention | `from vit_pytorch.xcit import XCiT` | Attention across feature dimensions plus local patch interaction. | Similar shape discipline to base ViT, but `local_patch_kernel_size` must be odd. Constructor requires `cls_depth`. |
| High-resolution attention search variant | `from vit_pytorch.jet_vit import JetViT` | Lets each layer use full, window, or linear attention choices (`FA`, `WA`, `LA`). | `attn_layers` length must match `depth`. For deterministic inference pass a list like `['FA', 'LA', ...]`; for search stages pass tuples such as `('WA', 'LA')`. |
| Mid-2020s ViT update | `from vit_pytorch.vit_5 import ViT` | RMSNorm, QK norm, LayerScale, register tokens, and 2D axial RoPE. | Requires exact image/patch divisibility. Keep `dim_head` even for RoPE-style rotation; `num_registers` controls register tokens. |

## Image-only variants and exact import names

| Variant request | Import/class to try first | Notes |
|---|---|---|
| Patch dropout | `from vit_pytorch.vit_with_patch_dropout import ViT` or `from vit_pytorch.simple_vit_with_patch_dropout import SimpleViT` | `patch_dropout` must satisfy `0 <= patch_dropout < 1`; dropout is active only in training mode. |
| Patch merger | `from vit_pytorch.vit_with_patch_merger import ViT, PatchMerger` | `patch_merge_layer` is effectively a 1-based layer choice converted internally to zero-based; `PatchMerger(dim, num_tokens_out)` maps `(batch, tokens, dim)` to `(batch, num_tokens_out, dim)`. |
| QK norm | `from vit_pytorch.simple_vit_with_qk_norm import SimpleViT` | In this snapshot, the QK-norm variant is a SimpleViT module, not a plain `vit_with_qk_norm` module. |
| Relative projected position bias | `from vit_pytorch.simple_vit_with_relative_proj_pos_bias import SimpleViT` | Adds `num_distance_basis` and `max_dist`; `dim` must be divisible by 4. |
| Specialized CLS | `from vit_pytorch.simple_vit_with_specialized_cls import SimpleViT` | Adds `specialize_qkv_depth`; uses CLS pooling instead of the ordinary SimpleViT mean pooling. |
| Value residual | `from vit_pytorch.simple_vit_with_value_residual import SimpleViT` | SimpleViT-style constructor with value residual behavior. |
| KEEL post-LN | `from vit_pytorch.vit_with_keel_post_ln import ViT` | Plain ViT-style constructor plus `keel_residual_scale`; supports `pool='cls'|'mean'`. |
| Normalized ViT | `from vit_pytorch.normalized_vit import nViT` | Class name is `nViT`, not `ViT`; constructor adds `residual_lerp_scale_init`. |
| Local ViT | `from vit_pytorch.local_vit import LocalViT` | Plain image constructor with local feed-forward/convolutional inductive bias. |
| LookViT | `from vit_pytorch.look_vit import LookViT` | Class name is `LookViT`; includes high-resolution patch and cross-attention parameters. |
| Rotary ViT | `from vit_pytorch.rvt import RvT` | Class name is `RvT`; optional `use_rotary`, `use_ds_conv`, and `use_glu` flags. |
| Detection-pooling ViT | `from vit_pytorch.vit_detpool import ViTDetPool` | Accepts optional `object_mask` or `mask_generator` and pools masked tokens; still a 2D image classifier when the user wants image-mask-aware pooling. |
| Register-token SimpleViT | `from vit_pytorch.simple_vit_with_register_tokens import SimpleViT` | Adds `num_register_tokens`; remains mean-pooled classifier. |
| Flash-attention SimpleViT | `from vit_pytorch.simple_flash_attn_vit import SimpleViT` | Uses PyTorch scaled-dot-product attention when `use_flash=True`; see troubleshooting before setting `use_flash=False`. |

If an import named by a paper or old snippet is missing, inspect the installed module namespace and prefer the class names above. Do not invent a nonexistent plain `vit_with_qk_norm`, `vit_with_relative_proj_pos_bias`, `vit_with_specialized_cls`, or `vit_with_value_residual` import in this snapshot.

## Tiny constructor patterns

Use these patterns to repair user code before scaling up. They deliberately use small tensors and few layers.

```python
import torch
from vit_pytorch import ViT, SimpleViT

num_classes = 7
img = torch.randn(1, 3, 32, 32)

vit = ViT(image_size=32, patch_size=8, num_classes=num_classes,
          dim=32, depth=1, heads=2, dim_head=16, mlp_dim=64)
assert vit(img).shape == (1, num_classes)

simple = SimpleViT(image_size=32, patch_size=8, num_classes=num_classes,
                   dim=32, depth=1, heads=2, dim_head=16, mlp_dim=64)
assert simple(img).shape == (1, num_classes)
```

For a small-memory comparison across families, run the bundled helper instead of hand-copying all snippets:

```bash
python scripts/smoke_image_architectures.py --case quick
python scripts/smoke_image_architectures.py --case extended
```

The helper covers baseline, compact, multi-scale, patch-merger, mobile, modern, and selected windowed models with reduced dimensions and CPU random tensors.

## Selection guidance for 32x32 or 64x64 users

1. Start with `ViT`, `SimpleViT`, and `CCT` as the baseline comparison. They are easiest to shrink safely.
2. For tiny images or small datasets, prefer `CCT`, `vit_for_small_dataset.ViT`, `SimpleViT`, or small `MobileViT` over large hierarchical defaults.
3. Use `patch_size=4` or `8` for `32x32` images. Larger patches such as `32` collapse tiny images into too few tokens and are usually only appropriate for README-scale `224x224` or `256x256` inputs.
4. Keep `dim`, `depth`, `heads`, and `mlp_dim` small while validating shape. Scale one axis at a time after a smoke pass.
5. For hierarchical/window models, prefer `64x64` smoke inputs and small window sizes when the source actually honors `window_size`. If the model has hard-coded stage/window assumptions, use the smallest verified shape or choose a more flexible family.
6. Treat all README examples as architectural demonstrations, not mandatory dimensions. Full README settings such as `dim=1024`, `depth=6`, `heads=16`, and `mlp_dim=2048` are unnecessary for constructor repair and can exhaust memory on CPU.

## Classifier-head and output rules

- Positive `num_classes` means the expected output is logits shaped `(batch, num_classes)`.
- Base `ViT`-style modules with `pool` accept only `pool='cls'` or `pool='mean'`.
- SimpleViT-style modules usually hard-code mean pooling and expose no `pool` argument.
- `simple_vit_with_specialized_cls.SimpleViT` is an exception: it is a SimpleViT-family variant using specialized CLS behavior.
- `LeViT` returns a tuple only if `num_distill_classes` is supplied; leave it unset for ordinary classification logits.
- If the user intentionally wants token sequences, embeddings, or attention maps rather than logits, route away from this sub-skill.

## Verification anchor

The native baseline candidate is the repo's plain `ViT` forward shape test. This sub-skill's bundled smoke helper adapts that pattern and README snippets into tiny CPU checks so future agents can verify common constructors without downloads, credentials, or training loops.
