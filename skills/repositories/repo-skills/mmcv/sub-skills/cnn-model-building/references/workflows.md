# MMCV CNN Workflows

These recipes are self-contained examples for future agents using `mmcv.cnn` in MMCV 2.2.0. They assume `torch` and importable `mmcv` are installed. They do not require source checkout files.

## Build Layers From Configs

Use builder configs when model code should mirror OpenMMLab-style experiment configs.

```python
from mmcv.cnn import (
    build_activation_layer,
    build_conv_layer,
    build_norm_layer,
    build_padding_layer,
    build_upsample_layer,
)

conv = build_conv_layer(
    dict(type='Conv2d'), in_channels=3, out_channels=8,
    kernel_size=3, padding=1)
norm_name, norm = build_norm_layer(dict(type='BN'), num_features=8)
act = build_activation_layer(dict(type='ReLU', inplace=True))
pad = build_padding_layer(dict(type='reflect'), 1)
upsample = build_upsample_layer(dict(type='nearest', scale_factor=2))
```

Important conventions:

- `build_conv_layer(None, ...)` is a shortcut for `Conv2d`.
- `build_norm_layer` returns a `(name, layer)` pair; add the returned layer under the returned name when building custom modules.
- `GN` requires `dict(type='GN', num_groups=...)`; `num_features` becomes `num_channels`.
- `nearest` and `bilinear` upsample configs become `nn.Upsample` with the corresponding `mode`.

## Convert a Handwritten Block to `ConvModule`

For a handwritten PyTorch block such as `conv -> bn -> relu`, use `ConvModule` and preserve channel/shape semantics.

```python
from mmcv.cnn import ConvModule

block = ConvModule(
    in_channels=3,
    out_channels=16,
    kernel_size=3,
    padding=1,
    norm_cfg=dict(type='BN'),
    act_cfg=dict(type='ReLU'),
)
```

Migration checklist:

- Preserve `stride`, `padding`, `dilation`, and `groups` exactly.
- If the original conv had no bias because a batch/instance norm followed it, keep `bias='auto'` or set `bias=False`.
- If the original conv used bias before batch/instance norm, set `bias=True` only if matching checkpoints requires it; MMCV will warn that the bias is unnecessary.
- Use `act_cfg=None` for conv-only or conv+norm blocks.
- Use `order=('norm', 'conv', 'act')` only when the source block really normalizes input channels before convolution; this changes the `num_features` used for norm.
- Use `forward(x, activate=False)` or `forward(x, norm=False)` only for explicit ablation/inference behavior.

## Build Depthwise Separable Blocks

```python
from mmcv.cnn import DepthwiseSeparableConvModule

block = DepthwiseSeparableConvModule(
    16,
    32,
    kernel_size=3,
    padding=1,
    norm_cfg=dict(type='BN'),
    act_cfg=dict(type='ReLU'))
```

The depthwise part uses `groups=in_channels`; do not pass `groups` yourself. Use `dw_norm_cfg`, `dw_act_cfg`, `pw_norm_cfg`, and `pw_act_cfg` to override either half independently.

## Register a Custom Layer

MMCV CNN builders use the MMEngine `MODELS` registry. Register custom modules before they are built.

```python
import torch.nn as nn
from mmengine.registry import MODELS
from mmcv.cnn import build_conv_layer

@MODELS.register_module()
class TinyConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, **kwargs):
        super().__init__()
        self.proj = nn.Conv2d(in_channels, out_channels, kernel_size, **kwargs)

    def forward(self, x):
        return self.proj(x)

layer = build_conv_layer(
    dict(type='TinyConv'), 3, 8, kernel_size=1)
```

For plugin layers, define `_abbr_` if the generated child name matters:

```python
from mmengine.registry import MODELS
from mmcv.cnn import build_plugin_layer

@MODELS.register_module()
class TinyPlugin(nn.Module):
    _abbr_ = 'tiny'
    def __init__(self, channels):
        super().__init__()
        self.identity = nn.Identity()
    def forward(self, x):
        return self.identity(x)

name, layer = build_plugin_layer(dict(type='TinyPlugin'), postfix=1, channels=8)
assert name == 'tiny1'
```

If the registry error mentions an unresolved type, ensure the Python module containing the registration was imported before the builder call.

## Use Plugin Blocks

`build_plugin_layer` is useful for attention/context blocks that should be inserted into a backbone by config.

```python
from mmcv.cnn import build_plugin_layer

name, context = build_plugin_layer(
    dict(type='ContextBlock', ratio=0.25, pooling_type='avg'),
    postfix='_gc',
    in_channels=64)
```

Built-in plugin examples include `ContextBlock`, `NonLocal2d`, `GeneralizedAttention`, and `ConvModule`. Some plugin blocks are pure PyTorch, but `GeneralizedAttention` or downstream attention choices may overlap with optional ops; route compiled op failures to `ops-and-builds`.

## Fuse Conv and BatchNorm

Use `fuse_conv_bn` on inference copies of models that have `nn.Conv2d` followed by batch norm.

```python
import torch.nn as nn
from mmcv.cnn import ConvModule, fuse_conv_bn

model = nn.Sequential(
    ConvModule(3, 8, 3, padding=1, norm_cfg=dict(type='BN')),
    ConvModule(8, 8, 3, padding=1, norm_cfg=dict(type='BN')),
).eval()

fused = fuse_conv_bn(model)
```

The utility recursively replaces batch norm children following eligible convs with `nn.Identity` and updates conv weights/biases. Avoid using it mid-training unless you intentionally mutate the module.

## Check FLOPs and Parameters

```python
from io import StringIO
import torch.nn as nn
from mmcv.cnn import get_model_complexity_info

model = nn.Sequential(
    nn.Conv2d(3, 8, 3),
    nn.ReLU(),
    nn.Flatten(),
    nn.Linear(8 * 14 * 14, 2),
)
stream = StringIO()
flops, params = get_model_complexity_info(
    model,
    (3, 16, 16),
    print_per_layer_stat=False,
    as_strings=True,
    ost=stream,
)
```

`input_shape` is channel-first without batch dimension. If the model forward needs named inputs, pass `input_constructor` that maps `input_shape` to a kwargs dict.

## Use Wrappers and Small Helpers

- Use `Conv2d`, `Conv3d`, `Linear`, `MaxPool2d`, and `MaxPool3d` as drop-in PyTorch wrappers where older empty-tensor compatibility matters.
- Use `Scale(scale=1.0)` for a learnable scalar multiplier.
- Use `ContextBlock` for global context with `pooling_type='att'` or `'avg'` and fusion types `channel_add`/`channel_mul`.
- Use `NonLocal1d`, `NonLocal2d`, or `NonLocal3d` with `mode` in `gaussian`, `embedded_gaussian`, `dot_product`, or `concatenation`.
- Use `make_res_layer` and `make_vgg_layer` for lightweight stage construction at overview depth, not as complete model training recipes.

## CPU-Safe Validation

The bundled script builds representative layers and modules, runs tiny CPU forwards, checks expected failure messages, and optionally checks FLOPs:

```bash
python ../scripts/cnn_builder_smoke.py --check-errors --check-flops
```

If this script fails with missing `torch`, install or activate a PyTorch environment. If it fails with `mmcv._ext` while using only these CNN checks, inspect whether external code imported `mmcv.ops` or deformable attention paths unintentionally.
