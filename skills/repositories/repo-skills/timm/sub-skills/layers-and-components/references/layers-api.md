# Layers API Reference

This reference summarizes the timm layer/component surface most useful for custom model work. Import from `timm.layers` unless a source comment explicitly says otherwise.

## Core Component Families

| Family | Common exports | Use for | Shape/layout notes |
| --- | --- | --- | --- |
| Patch embedding | `PatchEmbed`, `PatchEmbedWithSize`, `PatchEmbedInterpolator`, `resample_patch_embed` | ViT-style image-to-token projection and patch-kernel resizing | Input is `NCHW`. Default `flatten=True` returns `NLC`; `flatten=False` returns `NCHW`; `output_fmt='NHWC'` returns channel-last spatial output. |
| Classifier heads | `create_classifier`, `ClassifierHead`, `NormMlpClassifierHead`, `ClNormMlpClassifierHead` | Reusable global pool + dropout + final classifier or pre-logits head | `ClassifierHead` handles NCHW by default. `ClNormMlpClassifierHead` is for `NHWC`/`NLC`. `num_classes <= 0` makes the classifier identity. |
| Adaptive pooling | `SelectAdaptivePool2d`, `adaptive_avgmax_pool2d`, `select_adaptive_pool2d`, `AdaptiveAvgMaxPool2d` | Global avg/max/mixed pooling before heads | `pool_type=''` is identity. `catavgmax`/`fastcatavgmax` double channel features via `feat_mult() == 2`. Non-NCHW fast pooling requires `output_size=1`. |
| Drop regularizers | `DropPath`, `drop_path`, `DropBlock2d`, `drop_block_2d`, `calculate_drop_path_rates` | Stochastic depth and spatial block dropout | Drops only in training mode. `DropPath` masks per sample and broadcasts across remaining dimensions. |
| Norm layers | `LayerNorm`, `LayerNorm2d`, `RmsNorm`, `RmsNorm2d`, `GroupNorm`, fp32 variants, act variants | Transformer, ConvNet, and mixed precision normalization | `*2d` variants are for channel-first image tensors. `*Fp32` variants compute normalization in fp32 for numerical stability. |
| Activations | `create_act_layer`, `get_act_layer`, `get_act_fn`, activation classes | Configurable model blocks and MLPs | Empty string or `None` maps to no activation. Creation helpers handle classes, strings, and callables. |
| Attention / MLP | `Attention`, `AttentionRope`, `Attention2d`, `MultiQueryAttention2d`, `Mlp`, `GluMlp`, `SwiGLU`, `ConvMlp` | Transformer or ConvNet blocks | Token attention generally expects `NLC`; 2D attention expects `NCHW`. Match constructor `dim`/`in_features` to the final channel dimension. |
| Conv blocks | `ConvNormAct`, `ConvNormActAa`, `ConvBnAct`, `create_conv2d`, `create_norm_layer`, `create_norm_act_layer` | Concise conv-norm-act stems and stages | Most conv helpers use NCHW. Factory helpers accept string names and callables. |
| Positional embeddings | `resample_abs_pos_embed`, `build_sincos2d_pos_embed`, `RotaryEmbedding`, `RotaryEmbeddingCat`, `create_rope_embed` | ViT resizing and rotary/fourier position features | Match token/grid dimensions carefully; RoPE variants differ in concat/mixed behavior. |
| Format helpers | `Format`, `nchw_to`, `nhwc_to`, `get_channel_dim`, `get_spatial_dim` | Explicit layout conversion and layout-aware reductions | Use these helpers instead of hardcoding dimension numbers when supporting both NCHW and NHWC. |

## PatchEmbed Patterns

```python
from timm.layers import PatchEmbed

patch = PatchEmbed(img_size=32, patch_size=4, in_chans=3, embed_dim=64)
tokens = patch(images)  # [batch, 64 patches, 64 channels]
```

Important options:

| Option | Effect | Common pitfall |
| --- | --- | --- |
| `img_size` | Enables strict input-size checks and computes `grid_size`/`num_patches` | Passing a different image size with `strict_img_size=True` raises an assertion. |
| `strict_img_size=False` | Allows different sizes if divisible by patch size | Still requires height/width divisibility unless `dynamic_img_pad=True`. |
| `dynamic_img_pad=True` | Pads non-divisible images before projection | Output grid uses ceiling division; downstream positional embeddings may need resizing. |
| `flatten=True` | Converts projected NCHW grid to NLC tokens | Do not feed NLC directly to NCHW conv blocks. |
| `output_fmt='NHWC'` | Returns spatial channel-last output | Setting `output_fmt` disables flattening internally. |
| `set_input_size()` | Changes patch size and/or image size, resampling projection weights when patch size changes | Use for model surgery, then revalidate token count and positional embeddings. |

## Classifier and Pooling Patterns

```python
from timm.layers import ClassifierHead, SelectAdaptivePool2d

head = ClassifierHead(in_features=128, num_classes=10, pool_type='avg')
logits = head(feature_map)  # feature_map: [B, 128, H, W], logits: [B, 10]

pool = SelectAdaptivePool2d(pool_type='catavgmax', flatten=True)
features = pool(feature_map)  # [B, 256] because catavgmax doubles channels
```

Pool types:

| `pool_type` | Behavior | Flattened output for `[B, C, H, W]` |
| --- | --- | --- |
| `''` | Identity passthrough | `[B, C, H, W]` if `flatten=False`; flattened manually if requested |
| `avg` / `fast` / `fastavg` | Mean over spatial dimensions | `[B, C]` |
| `max` / `fastmax` | Max over spatial dimensions | `[B, C]` |
| `avgmax` / `fastavgmax` | Average of avg and max pools | `[B, C]` |
| `catavgmax` / `fastcatavgmax` | Concatenate avg and max features | `[B, 2C]` |

Head choices:

| Head | Best fit | Notes |
| --- | --- | --- |
| `ClassifierHead` | Standard CNN-style NCHW map to logits | `pre_logits=True` returns pooled/dropped features before `fc`. |
| `NormMlpClassifierHead` | NCHW map with normalization and optional hidden layer | Uses 2D norm by default and switches linear/conv behavior when pooling is disabled. |
| `ClNormMlpClassifierHead` | Channel-last (`NHWC`) or token (`NLC`) features | Validates `input_fmt` as `NHWC` or `NLC`. |
| `create_classifier` | Low-level factory returning pooling and fc modules | Use when a model class wants to own the sequence itself. |

## Feature Extraction Components

Feature wrappers live under `timm.models` but are part of component-level custom model work.

| Component/API | Use | Requirements |
| --- | --- | --- |
| `FeatureInfo` | Describes feature channels, reductions, and source modules | Each dict needs positive `num_chs`, nondecreasing `reduction`, and `module`. |
| `FeatureListNet` | Rebuilds a model and returns selected features as a list | Source modules must be registered and executed in order; no repeated module reuse. |
| `FeatureDictNet` | Same as `FeatureListNet`, but returns an ordered dict | `out_map` can rename outputs. |
| `FeatureHookNet` / `FeatureHooks` | Captures features using hooks | Eager-mode friendly; hooks are not a TorchScript-first interface. |
| `create_feature_extractor`, `get_graph_node_names` | FX graph extraction by node name | Requires traceable operations and stable node names. |
| `features_only=True` in `timm.create_model` | High-level backbone wrapper for supported timm models | Inspect `model.feature_info.channels()` and `.reduction()` instead of assuming strides. |
| `forward_intermediates()` | Model-family-specific intermediate feature return | Not every model exposes it; indices are model-specific. |

## Layer Configuration Context

`timm.layers` exposes configuration helpers such as `set_layer_config`, `set_scriptable`, `set_exportable`, `set_no_jit`, `set_fused_attn`, and `set_reentrant_ckpt`. Use them when a layer factory must choose scriptable/exportable/no-JIT implementations or disable fused attention for reproducibility/export constraints.

```python
from timm.layers import create_act_layer, set_layer_config

with set_layer_config(scriptable=True):
    act = create_act_layer('swish')
```

Keep these settings scoped with context managers unless the task intentionally changes global layer behavior.
