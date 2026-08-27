# Custom Model Components

Use these recipes to wire timm reusable layers into custom PyTorch modules and to validate the result without downloads.

## Build a Patch-Embed + Head Smoke Path

A minimal ViT-like component path is:

```python
import torch
from timm.layers import PatchEmbed, ClassifierHead

patch = PatchEmbed(img_size=32, patch_size=4, in_chans=3, embed_dim=64)
tokens = patch(torch.randn(2, 3, 32, 32))
assert tokens.shape == (2, 64, 64)

# Convert NLC tokens back to a square NCHW map before using a CNN-style head.
feature_map = tokens.transpose(1, 2).reshape(2, 64, 8, 8)
head = ClassifierHead(in_features=64, num_classes=5, pool_type='avg')
assert head(feature_map).shape == (2, 5)
```

Validation checklist:

- Confirm `PatchEmbed.num_patches`, `grid_size`, and output shape after every image-size or patch-size change.
- Convert flattened patch output (`NLC`) before feeding NCHW layers.
- Set `strict_img_size=False` only when the downstream model can handle variable token counts.
- Set `dynamic_img_pad=True` when non-divisible image sizes should be padded instead of rejected.
- If changing patch size in an existing model, call `set_input_size()` and then validate positional embeddings separately.

## Compose Conv-Norm-Act Blocks

```python
from timm.layers import ConvNormAct, DropPath, LayerScale2d

block = ConvNormAct(3, 32, kernel_size=3, stride=2, norm_layer='batchnorm2d', act_layer='silu')
regularizer = DropPath(0.1)
scale = LayerScale2d(32)
```

Practical rules:

- Keep NCHW tensors for conv blocks, 2D attention, batch norm, and `LayerNorm2d`/`RmsNorm2d`.
- Use factory names (`norm_layer='batchnorm2d'`, `act_layer='gelu'`) when you want config-driven construction.
- Use class/callable arguments when a custom module needs constructor parameters not covered by string aliases.
- In residual blocks, put `DropPath` on the residual branch and remember it is inactive in eval mode.

## Choose the Right Norm Variant

| Input layout | Common norm | Notes |
| --- | --- | --- |
| NCHW image map | `BatchNormAct2d`, `LayerNorm2d`, `RmsNorm2d`, `GroupNorm` | Use `*2d` variants for channel-first tensors. |
| NLC tokens | `LayerNorm`, `RmsNorm`, `SimpleNorm` | Final channel dimension is normalized. |
| NHWC map | `LayerNorm`, `RmsNorm`, or channel-last classifier head | Avoid channel-first-only norms unless you convert layout. |
| Mixed precision-sensitive path | `LayerNormFp32`, `RmsNormFp32`, `LayerNorm2dFp32`, `RmsNorm2dFp32` | These compute normalization in fp32 to reduce numerical issues. |

## Configure Pooling and Heads

Use `ClassifierHead` for common CNN-style heads:

```python
from timm.layers import ClassifierHead

head = ClassifierHead(in_features=192, num_classes=0, pool_type='avg')
features = head(torch.randn(2, 192, 7, 7))
assert features.shape == (2, 192)
```

Head and pooling choices:

- `num_classes=0` or a negative class count makes the final classifier identity.
- `pool_type=''` keeps spatial structure; useful for dense prediction, but downstream heads must accept `[B, C, H, W]`.
- `pool_type='catavgmax'` doubles the input feature count for the classifier.
- `use_conv=True` makes the classifier a `1x1` conv and flattens after pooling when appropriate.
- For channel-last or token outputs, prefer `ClNormMlpClassifierHead(input_fmt='NHWC'|'NLC')`.

## Wrap a Custom Model for Features

When using timm feature wrappers with a custom model, provide accurate `feature_info` on the model and keep module names aligned with registered submodules.

```python
import torch.nn as nn
from timm.models._features import FeatureListNet

class TinyBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = nn.Conv2d(3, 8, 3, stride=2, padding=1)
        self.stage1 = nn.Conv2d(8, 16, 3, stride=2, padding=1)
        self.stage2 = nn.Conv2d(16, 32, 3, stride=2, padding=1)
        self.feature_info = [
            {'num_chs': 8, 'reduction': 2, 'module': 'stem'},
            {'num_chs': 16, 'reduction': 4, 'module': 'stage1'},
            {'num_chs': 32, 'reduction': 8, 'module': 'stage2'},
        ]

    def forward(self, x):
        x = self.stem(x)
        x = self.stage1(x)
        return self.stage2(x)

features = FeatureListNet(TinyBackbone(), out_indices=(0, 2))
```

Wrapper constraints:

- `feature_info` reductions must be positive and nondecreasing.
- `module` values must name registered child modules the wrapper can find.
- `FeatureListNet` and `FeatureDictNet` rebuild the model from ordered child modules, so unusual dynamic forward graphs, reused modules, and deeply nested modules may not work.
- Hook-based extraction is more flexible for eager execution but is less suitable for TorchScript/export workflows.
- FX extraction can target graph node names, but custom Python control flow or unsupported ops can break tracing.

## Use `features_only` and `forward_intermediates`

For timm registry models, prefer high-level feature APIs before manual wrappers:

```python
import timm

model = timm.create_model('resnet18', pretrained=False, features_only=True, out_indices=(1, 3))
channels = model.feature_info.channels()
reductions = model.feature_info.reduction()
```

Rules of thumb:

- Use `model.feature_info.channels()` to size downstream heads.
- Use `model.feature_info.reduction()` to compute feature strides instead of assuming index-to-stride mapping.
- Use negative `out_indices` for relative selection, such as `(-1,)` for the last feature.
- Set `output_stride` only on model families that support dilation changes; some support only stride 32.
- Use `forward_intermediates()` for ViT/block-level or model-specific intermediate extraction and verify that the chosen model implements it.

## Local Validation Checklist

1. Run a random forward pass with batch size 2 and small input dimensions.
2. Assert every intermediate shape at layout boundaries (`NCHW` ↔ `NLC`/`NHWC`).
3. Toggle `.train()` and `.eval()` for stochastic components such as `DropPath` and `DropBlock2d`.
4. Check classifier outputs for both `num_classes > 0` and `num_classes=0` if a feature mode is supported.
5. If feature wrappers are used, compare actual output channels and reductions to `feature_info`.
6. Keep validation no-download: use `pretrained=False` and random tensors.
