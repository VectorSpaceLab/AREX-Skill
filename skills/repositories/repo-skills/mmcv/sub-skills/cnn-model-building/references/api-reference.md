# MMCV CNN API Reference

This reference covers MMCV 2.2.0 `mmcv.cnn` helpers that work with PyTorch. In an `mmcv-lite` install, pure PyTorch CNN helpers are available, while compiled `mmcv.ops` paths are conditional and should be routed to `ops-and-builds`.

## Builder Functions

| API | Signature pattern | Returns | Notes |
| --- | --- | --- | --- |
| `build_conv_layer` | `build_conv_layer(cfg, *args, **kwargs)` | `nn.Module` | `cfg=None` defaults to `Conv2d`; `cfg` must be a dict with `type` unless `None`. |
| `build_norm_layer` | `build_norm_layer(cfg, num_features, postfix='')` | `(name, nn.Module)` | Name is inferred abbreviation plus postfix, such as `bn1`, `gn`, or `ln_head`. |
| `build_activation_layer` | `build_activation_layer(cfg)` | `nn.Module` | Delegates to the MMEngine `MODELS` registry. |
| `build_padding_layer` | `build_padding_layer(cfg, *args, **kwargs)` | `nn.Module` | `cfg` must be a dict with `type`; positional args usually pass padding size. |
| `build_upsample_layer` | `build_upsample_layer(cfg, *args, **kwargs)` | `nn.Module` | Adds `mode` automatically for `nearest` and `bilinear` `nn.Upsample`. |
| `build_plugin_layer` | `build_plugin_layer(cfg, postfix='', **kwargs)` | `(name, nn.Module)` | Name is inferred from `_abbr_` or snake-cased class name plus postfix. |
| `is_norm` | `is_norm(layer, exclude=None)` | `bool` | Recognizes batch, instance, group, and layer norm bases; `exclude` must be a type or tuple of types. |

All config builders accept a class object as `type` as well as a registered string. Invalid config shape raises `TypeError`, missing `type` raises `KeyError`, unregistered `type` raises `KeyError`, and invalid postfix usually raises `AssertionError`.

## Supported Config Types

| Builder | Supported `type` values from docs/tests | Important arguments |
| --- | --- | --- |
| Convolution | `Conv1d`, `Conv2d`, `Conv3d`, `Conv`, `deconv`, `deconv3d`, wrapper classes such as `ConvTranspose2d` when registered | `in_channels`, `out_channels`, `kernel_size`, `stride`, `padding`, `dilation`, `groups`, `bias` |
| Normalization | `BN`, `BN1d`, `BN2d`, `BN3d`, `SyncBN`, `GN`, `LN`, `IN`, `IN1d`, `IN2d`, `IN3d` | `num_features` argument; `GN` config must include `num_groups`; `requires_grad` controls parameters |
| Activation | `ReLU`, `LeakyReLU`, `PReLU`, `RReLU`, `ReLU6`, `ELU`, `Sigmoid`, `Tanh`, `GELU`, `SiLU`, `Clamp`, `Clip`, `HSigmoid`, `HSwish`, `Swish` | Type-specific PyTorch kwargs; `ConvModule` injects `inplace` for most activations |
| Padding | `zero`, `reflect`, `replicate` | Padding size is usually passed as an argument to the builder. |
| Upsample | `nearest`, `bilinear`, `deconv`, `deconv3d`, `pixel_shuffle` | `scale_factor`, `size`, deconv channel/kernel args, or pixel shuffle args. |
| Plugin | `ContextBlock`, `GeneralizedAttention`, `NonLocal2d`, `ConvModule`, and custom `MODELS` registrations | `postfix` names layers; kwargs can be supplied outside `cfg`. |

`GeneralizedAttention` and some transformer/deformable attention use cases can touch optional compiled paths. If an import mentions `mmcv.ops`, `mmcv._ext`, or installing full `mmcv`, treat that as an ops/build issue rather than a pure CNN builder issue.

## Module Bundles

### `ConvModule`

Signature facts verified for MMCV 2.2.0:

```python
ConvModule(
    in_channels, out_channels, kernel_size, stride=1, padding=0,
    dilation=1, groups=1, bias='auto', conv_cfg=None, norm_cfg=None,
    act_cfg={'type': 'ReLU'}, inplace=True, with_spectral_norm=False,
    padding_mode='zeros', order=('conv', 'norm', 'act'),
    efficient_conv_bn_eval=False)
```

Key behavior:

- `conv_cfg=None` builds `Conv2d`; non-`None` must be a dict.
- `norm_cfg=None` disables normalization; otherwise `build_norm_layer` creates a named child such as `bn` or `gn`.
- `act_cfg=None` disables activation; otherwise `build_activation_layer` creates `activate`.
- `bias='auto'` sets convolution bias to `False` when `norm_cfg` is present and `True` otherwise.
- `order` must be a tuple of exactly `('conv', 'norm', 'act')` in any order; wrong length or duplicate/missing entries raises `AssertionError`.
- `padding_mode='reflect'` uses an explicit `ReflectionPad2d` before convolution; unsupported modes fail through `build_padding_layer`.
- `forward(x, activate=True, norm=True)` can skip activation or norm at call time.

### `DepthwiseSeparableConvModule`

Signature pattern:

```python
DepthwiseSeparableConvModule(
    in_channels, out_channels, kernel_size, stride=1, padding=0,
    dilation=1, norm_cfg=None, act_cfg={'type': 'ReLU'},
    dw_norm_cfg='default', dw_act_cfg='default',
    pw_norm_cfg='default', pw_act_cfg='default', **kwargs)
```

It creates a depthwise `ConvModule` with `groups=in_channels` followed by a pointwise `ConvModule` with kernel size `1`. Do not pass `groups` in `kwargs`; tests assert this is invalid. `dw_*='default'` and `pw_*='default'` inherit the shared `norm_cfg` or `act_cfg`.

## Wrapper and Utility Modules

| API | Purpose | CPU-safe notes |
| --- | --- | --- |
| `Conv2d`, `Conv3d` | Thin wrappers around PyTorch convs with older empty-tensor handling. | Use like `torch.nn` convs; registered as `Conv`/`Conv3d` with force overrides. |
| `Linear` | Wrapper around `torch.nn.Linear` with older empty-tensor handling. | Same constructor as `nn.Linear`. |
| `MaxPool2d`, `MaxPool3d` | Wrappers around PyTorch max pooling with older empty-tensor handling. | Same constructor as `nn.MaxPool*`. |
| `Scale(scale=1.0)` | Learnable scalar multiplier. | Stores a float `nn.Parameter` named `scale`. |
| `ContextBlock(in_channels, ratio, pooling_type='att', fusion_types=('channel_add',))` | GCNet context block. | `pooling_type` must be `att` or `avg`; fusion types must be `channel_add`/`channel_mul`. |
| `NonLocal1d/2d/3d` | Non-local blocks with modes `gaussian`, `embedded_gaussian`, `dot_product`, `concatenation`. | Mode validation is strict; `sub_sample` adds max pooling. |
| `HSigmoid`, `HSwish`, `Swish` | Activation modules. | `HSwish` may map to native `nn.Hardswish` on newer torch. |
| `fuse_conv_bn(module)` | Recursively fuses `nn.Conv2d` followed by batch norm for inference. | Replaces fused BN children with `nn.Identity`. Run on an eval/inference copy. |
| `get_model_complexity_info(model, input_shape, ...)` | Calculates FLOPs and parameter count. | `input_shape` must be a tuple with at least one dimension; supports common PyTorch conv/norm/pool/linear/upsample layers. |
| `make_res_layer(block, inplanes, planes, blocks, stride=1, dilation=1, style='pytorch', with_cp=False)` | Builds a small ResNet stage as `nn.Sequential`. | `block` usually `BasicBlock` or `Bottleneck` from `mmcv.cnn.resnet`. |
| `make_vgg_layer(inplanes, planes, num_blocks, dilation=1, with_bn=False, ceil_mode=False)` | Returns a list of VGG conv/norm/ReLU/maxpool modules. | Wrap in `nn.Sequential(*layers)` if a module is needed. |

## Transformer Bricks Overview

`mmcv.cnn.bricks.transformer` contains PyTorch-based helpers such as `AdaptivePadding`, `PatchEmbed`, `PatchMerging`, `MultiheadAttention`, `FFN`, `BaseTransformerLayer`, and `TransformerLayerSequence`. These use `build_conv_layer`, `build_norm_layer`, `build_activation_layer`, and MMEngine registries.

The same module attempts a compatibility import of `mmcv.ops.multi_scale_deform_attn.MultiScaleDeformableAttention`. In `mmcv-lite`, that optional import can warn or fail because compiled `mmcv._ext` ops are absent. Keep pure transformer bricks here, but route deformable attention or `mmcv.ops` installation/runtime issues to `ops-and-builds`.
