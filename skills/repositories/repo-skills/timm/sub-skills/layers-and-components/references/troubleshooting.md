# Layers and Components Troubleshooting

## Quick Diagnosis Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Input height ... doesn't match model` from `PatchEmbed` | Input size differs from `img_size` while `strict_img_size=True` | Match the configured image size, set `strict_img_size=False`, or enable `dynamic_img_pad=True` when padding is acceptable. |
| Patch tokens cannot feed a conv/pool layer | `PatchEmbed(flatten=True)` returned `NLC` tokens | Reshape back to `[B, C, H, W]` using the known patch grid, or instantiate with `flatten=False`. |
| Classifier head channel mismatch | `catavgmax` doubled pooled features or `in_features` is wrong | Use `SelectAdaptivePool2d(...).feat_mult()` or `model.feature_info.channels()` to compute the final input size. |
| NHWC input gives wrong pooling dimensions | Pool/head created with default `input_fmt='NCHW'` | Pass `input_fmt='NHWC'` to pooling/head components that support it. |
| Norm output looks unstable in mixed precision | Norm computed in low precision | Try `LayerNormFp32`, `LayerNorm2dFp32`, `RmsNormFp32`, or `RmsNorm2dFp32` for numerically sensitive paths. |
| `DropPath` appears to do nothing | Module is in eval mode or `drop_prob=0` | Call `.train()` for stochastic-depth validation; use `.eval()` for deterministic inference checks. |
| `DropBlock2d` masks are unexpected | `couple_channels`, `scale_by_keep`, or block-size behavior differs from expectations | Set `couple_channels=False` for per-channel masks; set `scale_by_keep=False` to inspect unscaled zeros; validate asymmetric/even block sizes. |
| `FeatureInfo` assertion fails | Missing/invalid `num_chs`, `reduction`, or `module` fields | Provide positive channels, nondecreasing reductions, and real registered module names. |
| Feature wrapper says return layers are missing | `module` names do not match direct children or one-level flattened children | Align names with `named_children()`, use `flatten_sequential=True` where suitable, or switch to hook/FX extraction. |
| `output_stride` ignored or errors | Model family does not support requested dilation/stride conversion | Inspect `model.feature_info.reduction()` after construction; fall back to a supported stride. |
| FX extraction fails during tracing | Unsupported Python control flow, dynamic ops, or nontraceable modules | Use `features_only`, `forward_intermediates`, or hook-based extraction; register notrace functions/modules only when you understand the graph. |
| Import warning for `timm.models.layers` | Deprecated compatibility import path | Change imports to `timm.layers`. |

## Shape and Layout Mismatches

Most timm layers are explicit about tensor layout, but custom models often cross layout boundaries:

- CNN blocks, 2D attention, `SelectAdaptivePool2d` default mode, and `ClassifierHead` default mode expect `NCHW`.
- Transformer/token blocks and regular `LayerNorm`/`RmsNorm` usually work on `NLC` or final-channel tensors.
- `PatchEmbed` input is always `NCHW`, while its default output is `NLC` because `flatten=True`.
- `ClNormMlpClassifierHead` is for `NHWC` or `NLC`, not NCHW.
- Use `Format`, `nchw_to`, `nhwc_to`, `get_channel_dim`, and `get_spatial_dim` when writing layout-flexible helpers.

When debugging a mismatch, print or assert both the semantic layout and tensor shape at each boundary, not just the shape tuple.

## PatchEmbed Input Errors

`PatchEmbed` validates image size before projection when `img_size` is known:

- With `strict_img_size=True`, height and width must match `img_size` exactly.
- With `strict_img_size=False` and `dynamic_img_pad=False`, height and width must be divisible by `patch_size`.
- With `dynamic_img_pad=True`, inputs are padded to a divisible size and the dynamic feature size uses ceiling division.

If a downstream module uses absolute position embeddings, changing the patch grid may require position-embedding resampling through the appropriate model or position-embedding helper.

## Classifier and Pooling Errors

Common head mistakes:

- `pool_type='catavgmax'` doubles the pooled channel count, so a manual `nn.Linear` must use `2 * in_features`.
- `pool_type=''` is identity, so the head may preserve spatial dimensions until the classifier path flattens or applies a conv.
- `num_classes=0` intentionally returns features instead of logits; this is not a broken classifier.
- `use_conv=True` creates a convolutional classifier and changes how flattening happens after pooling.
- Non-NCHW pooling should use supported fast pooling and `output_size=1`.

## Normalization and Dtype Issues

Choose the norm for the tensor layout:

- Use `LayerNorm2d`/`RmsNorm2d` for channel-first image maps.
- Use `LayerNorm`/`RmsNorm` for token or channel-last final-dimension normalization.
- Use fp32 variants when autocast or low precision causes numerical drift.
- If freezing or converting batch norm in a model, route broader model surgery to the model-library or training workflow guidance.

## DropPath and DropBlock Behavior

`DropPath` and `DropBlock2d` are intentionally stochastic only in training mode:

```python
module = DropPath(0.5)
module.eval()
assert torch.equal(module(x), x)
module.train()
y = module(x)
```

Testing tips:

- Use a fixed random seed for deterministic assertions.
- For `DropPath`, masking is per sample and broadcasts over all non-batch dimensions.
- For `DropBlock2d`, small tensors and large blocks change the effective dropped area; validate shape preservation separately from drop ratio.
- `scale_by_keep=True` scales kept activations, so surviving values may be larger than the original tensor.

## Feature Wrapper and FX Failures

Feature extraction failures usually come from one of three sources:

1. `feature_info` does not describe the model accurately.
2. The wrapper cannot reconstruct the model execution order from registered modules.
3. FX tracing cannot represent the model's Python or operator behavior.

Mitigations:

- For timm registry models, prefer `create_model(..., features_only=True)` first.
- For custom models, create a small input and compare actual output shapes with `feature_info.channels()` and `feature_info.reduction()`.
- Use `FeatureHookNet` or direct forward hooks when rebuild-based wrappers cannot follow the graph.
- Use `get_graph_node_names` to inspect FX node names before selecting return nodes.
- Keep unsupported FX tracing out of export-critical paths unless separately validated.

## Moved Imports

The old compatibility path `timm.models.layers` may still resolve with a deprecation warning. New code should import from `timm.layers`:

```python
from timm.layers import PatchEmbed, ClassifierHead, SelectAdaptivePool2d, DropPath
```

If a project has many old imports, update them mechanically and run a component smoke check before changing behavior.
