# MMCV CNN Troubleshooting

Use this guide for pure PyTorch `mmcv.cnn` failures in MMCV 2.2.0. If the traceback is about `mmcv._ext`, `mmcv.ops`, CUDA/C++ compilation, or installing full `mmcv`, route to `ops-and-builds`.

## Import and Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | `mmcv.cnn` helpers depend on PyTorch. | Install or activate an environment with `torch`; then run the smoke helper. |
| `ModuleNotFoundError: No module named 'mmcv'` | MMCV is not installed/importable. | Install the package distribution that imports as `mmcv`; MMCV Lite is sufficient for pure CNN builders. |
| `ModuleNotFoundError: No module named 'mmcv._ext'` | Code imported compiled ops, often through `mmcv.ops` or deformable attention. | Do not assume ops are available in `mmcv-lite`; route compiled op setup/runtime to `ops-and-builds`. |
| Warning that `MultiScaleDeformableAttention` failed to import | `mmcv.cnn.bricks.transformer` attempted an optional ops import. | Continue for pure transformer bricks; use full MMCV/ops guidance only if deformable attention is required. |

## Config Builder Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `TypeError: cfg must be a dict` | Builder received a string or other non-dict config. | Use `dict(type='Conv2d')`, `dict(type='BN')`, etc.; only `build_conv_layer` accepts `cfg=None`. |
| `KeyError: the cfg dict must contain the key "type"` | Config dict omitted `type`. | Add the registry type string or class object under `type`. |
| `KeyError: Cannot find ... in registry` | Type is misspelled, unsupported, or the custom module was not imported and registered. | Check supported types in `api-reference.md`; import the module containing `@MODELS.register_module()` before building. |
| `AssertionError` for postfix | `build_norm_layer` or `build_plugin_layer` got a postfix that is not `str` or `int`. | Use `postfix=''`, `postfix=1`, or a string such as `'_head'`. |

## Normalization and Shape Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError` from `build_norm_layer(dict(type='GN'), ...)` | GroupNorm config lacks `num_groups`. | Use `dict(type='GN', num_groups=<groups>)`. |
| GroupNorm runtime error about channels not divisible by groups | `num_features`/channels is incompatible with `num_groups`. | Choose a divisor of the channel count, e.g. `num_groups=4` for 16 channels. |
| BatchNorm shape mismatch | Wrong `num_features` or wrong `ConvModule.order`. | For `order=('conv','norm','act')`, norm channels are `out_channels`; for norm before conv, norm channels are `in_channels`. |
| LayerNorm shape mismatch | `LN` expects the normalized shape supplied by `num_features` or downstream shape. | Use `LN` mainly where feature vectors match, such as transformer embeddings, or pass the correct normalized shape if using raw PyTorch. |
| `is_norm(..., exclude='BN')` raises `TypeError` | `exclude` must be a type or tuple of types. | Pass a norm class such as `torch.nn.BatchNorm2d` or a tuple of classes. |

## `ConvModule` Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError` for `conv_cfg`, `norm_cfg`, or `act_cfg` | Non-`None` config is not a dict. | Use dict configs or `None`. |
| `KeyError` for activation such as `softmax` | Activation is not registered under that name. | Use supported activation types or register a custom activation with `MODELS`. |
| Warning `Unnecessary conv bias before batch/instance norm` | `bias=True` with BN/IN. | Prefer `bias='auto'` or `bias=False` unless preserving checkpoint compatibility. |
| Unexpected missing conv bias | `bias='auto'` disables conv bias whenever `norm_cfg` is present. | Set `bias=True` explicitly if you really need it. |
| No activation layer created | `act_cfg=None`. | This is intentional for conv-only or conv+norm blocks; set `act_cfg=dict(type='ReLU')` to enable activation. |
| `AssertionError` for `order` | Order is not a tuple of exactly `conv`, `norm`, and `act`. | Use tuples such as `('conv', 'norm', 'act')` or `('norm', 'conv', 'act')`. |
| Shape mismatch after order change | Norm channel count changed with layer order. | Recompute whether norm should use input or output channels before changing order. |
| `KeyError` for `padding_mode` | Mode is not in PyTorch official modes or MMCV padding registry. | Use `zeros`, `circular`, `reflect`, or a registered padding layer. |

## Depthwise Separable Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: groups should not be specified` | `DepthwiseSeparableConvModule` controls depthwise `groups` internally. | Remove `groups`; the depthwise conv uses `groups=in_channels`. |
| Only one half has norm/activation | `dw_*` or `pw_*` override differs from shared config. | Use shared `norm_cfg`/`act_cfg` for both halves, or set both depthwise and pointwise overrides explicitly. |

## Plugin and Attention Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Plugin name is not what code expects | Class lacks `_abbr_`, so name is snake-cased class name plus postfix. | Add `_abbr_` to custom plugin or use the returned name instead of guessing. |
| `ContextBlock` assertion on pooling type | `pooling_type` is not `att` or `avg`. | Use one of the supported values. |
| `ContextBlock` assertion on fusion types | Fusion types are not a list/tuple of `channel_add` and/or `channel_mul`. | Pass `('channel_add',)`, `('channel_mul',)`, or both. |
| `NonLocal*` raises unsupported mode | Mode is not one of `gaussian`, `embedded_gaussian`, `dot_product`, `concatenation`. | Use a supported mode and ensure input dimensionality matches the chosen `NonLocal1d/2d/3d`. |
| Transformer layer assertion on operation order | `operation_order` contains invalid operation names or inconsistent attention/FFN config counts. | Use names from `self_attn`, `cross_attn`, `norm`, and `ffn`; match list lengths to counts. |

## Complexity and Fusion Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError` from `get_model_complexity_info` | `input_shape` is not a tuple or is empty; model is not `nn.Module`. | Pass channel-first shape without batch dimension, e.g. `(3, 224, 224)`. |
| FLOPs are missing for custom layers | Complexity counter only handles supported exact module types. | Wrap custom behavior in supported modules or treat results as partial. |
| Fused model behavior changes | Fusing mutated a training model or non-conv/BN pattern. | Call `.eval()`, fuse an inference copy, and compare outputs on representative inputs. |
| BatchNorm remains after fusion | Only BN immediately after a stored `nn.Conv2d` child is fused. | Inspect module child order; nested or nonstandard patterns may need manual handling. |

## Quick Diagnostic Command

Run this CPU-only helper when debugging builder failures:

```bash
python ../scripts/cnn_builder_smoke.py --check-errors --check-flops
```

It reports missing imports, builds representative conv/norm/activation/padding/upsample/plugin/module utilities, runs tiny forwards, checks intentional invalid configs, and verifies a small FLOPs query.
