# PyTorch API Reference

This reference focuses on the public PyTorch surface that future agents are most likely to call directly.

## Import surfaces

- `import resnest.torch as resnest_torch` exposes the ResNeSt factories and the fast ablation factories.
- `from resnest.torch.models.build import get_model` resolves registry-backed builders by name.
- `from resnest.torch.models.resnet import ResNet, Bottleneck` gives the ResNet backbone class and block class.
- `from resnest.torch.models.splat import SplAtConv2d, rSoftMax` gives the Split-Attention layer and its reducer.

## Factory signatures

All public factory functions in this package follow the same signature pattern:

```python
(pretrained=False, root='~/.encoding/models', **kwargs)
```

The `root` argument is retained for compatibility, but the current PyTorch factory implementations do not pass it into the pretrained-weight downloader. In practice, `pretrained=True` follows PyTorch Hub cache resolution.

### ResNeSt factories exported from `resnest.torch`

| Factory | Default block layout | Default attention | Default stem | Pretrained in this release | Notes |
|---|---:|---:|---:|---|---|
| `resnest50` | `[3, 4, 6, 3]` | `radix=2`, `groups=1` | deep stem, width 32 | yes | canonical small ResNeSt classification model |
| `resnest101` | `[3, 4, 23, 3]` | `radix=2`, `groups=1` | deep stem, width 64 | yes | larger depth, same attention recipe |
| `resnest200` | `[3, 24, 36, 3]` | `radix=2`, `groups=1` | deep stem, width 64 | yes | heavyweight classification model |
| `resnest269` | `[3, 30, 48, 8]` | `radix=2`, `groups=1` | deep stem, width 64 | yes | largest canonical ImageNet model |
| `resnest50_fast_1s1x64d` | `[3, 4, 6, 3]` | `radix=1`, `groups=1` | deep stem, width 32 | yes | fast ablation variant |
| `resnest50_fast_2s1x64d` | `[3, 4, 6, 3]` | `radix=2`, `groups=1` | deep stem, width 32 | yes | fast ablation variant |
| `resnest50_fast_4s1x64d` | `[3, 4, 6, 3]` | `radix=4`, `groups=1` | deep stem, width 32 | yes | fast ablation variant |
| `resnest50_fast_1s2x40d` | `[3, 4, 6, 3]` | `radix=1`, `groups=2` | deep stem, width 32 | yes | fast ablation variant |
| `resnest50_fast_2s2x40d` | `[3, 4, 6, 3]` | `radix=2`, `groups=2` | deep stem, width 32 | yes | fast ablation variant |
| `resnest50_fast_4s2x40d` | `[3, 4, 6, 3]` | `radix=4`, `groups=2` | deep stem, width 32 | yes | fast ablation variant |
| `resnest50_fast_1s4x24d` | `[3, 4, 6, 3]` | `radix=1`, `groups=4` | deep stem, width 32 | yes | fast ablation variant |

### Registry-backed baseline builders

`get_model(name)` resolves these registered names:

| Registry name | Builder module | Notes |
|---|---|---|
| `resnet50` | `resnest.torch.models.resnet` | plain ResNet baseline, not exposed by Torch Hub |
| `resnet101` | `resnest.torch.models.resnet` | plain ResNet baseline, not exposed by Torch Hub |
| `resnet152` | `resnest.torch.models.resnet` | plain ResNet baseline, not exposed by Torch Hub |
| `resnest50` | `resnest.torch.models.resnest` | also exposed directly from `resnest.torch` |
| `resnest101` | `resnest.torch.models.resnest` | also exposed directly from `resnest.torch` |
| `resnest200` | `resnest.torch.models.resnest` | also exposed directly from `resnest.torch` |
| `resnest269` | `resnest.torch.models.resnest` | also exposed directly from `resnest.torch` |

The fast ablation factories are not in the registry, so config-driven code should call them directly rather than looking them up by `get_model()`.

## Core classes and helpers

| Symbol | Purpose | Useful defaults / notes |
|---|---|---|
| `ResNet(block, layers, radix=1, groups=1, bottleneck_width=64, num_classes=1000, dilated=False, dilation=1, deep_stem=False, stem_width=64, avg_down=False, rectified_conv=False, rectify_avg=False, avd=False, avd_first=False, final_drop=0.0, dropblock_prob=0, last_gamma=False, norm_layer=nn.BatchNorm2d)` | Backbone and classifier head | Use `num_classes` to change the classifier output size; `dropblock_prob>0` is not usable in this build because the placeholder layer raises `NotImplementedError`. |
| `Bottleneck(...)` | Residual block used by the ResNeSt/ResNet builders | Includes Split-Attention when `radix>=1`. |
| `SplAtConv2d(in_channels, channels, kernel_size, stride=(1,1), padding=(0,0), dilation=(1,1), groups=1, bias=True, radix=2, reduction_factor=4, rectify=False, rectify_avg=False, norm_layer=None, dropblock_prob=0.0, **kwargs)` | Split-Attention convolution | For tiny smokes, use `norm_layer=None` to avoid batchnorm dependence. Output shape preserves spatial size when padding matches kernel size. |
| `rSoftMax(radix, cardinality)` | Attention reducer | Uses softmax across radix branches when `radix>1`, otherwise sigmoid. |
| `get_model(model_name)` | Registry lookup | Raises a registry error when the name is not registered. |

## Torch Hub entry points

`hubconf.py` exposes the same public classification factories for Torch Hub use and depends only on `torch`.

Hub-visible names:

- `resnest50`
- `resnest101`
- `resnest200`
- `resnest269`
- `resnest50_fast_1s1x64d`
- `resnest50_fast_2s1x64d`
- `resnest50_fast_4s1x64d`
- `resnest50_fast_1s2x40d`
- `resnest50_fast_2s2x40d`
- `resnest50_fast_4s2x40d`
- `resnest50_fast_1s4x24d`

Example pattern:

```python
import torch
model = torch.hub.load('zhanghang1989/ResNeSt', 'resnest50', pretrained=False)
```

## Package-support utilities

| Symbol | Purpose | Notes |
|---|---|---|
| `get_dataset('ImageNet')` | Returns the ImageNet folder dataset wrapper | Expects train/val subdirectories under the configured root. |
| `get_transform('ImageNet')` | Returns the train/val transform pair | Train uses random crop, flip, color jitter, lighting, and normalize; val uses center crop and normalize. |
| `get_criterion(cfg, train_loader, gpu)` | Chooses mixup, label smoothing, or cross-entropy | MixUp is CUDA-oriented and assumes 1000 classes. |
| `accuracy`, `AverageMeter`, `LR_Scheduler`, `save_checkpoint`, `mkdir`, `PathManager` | Training and evaluation helpers | `PathManager` comes from `iopath`; `accuracy` expects class logits. |

## Pretrained-weight behavior

- Core and fast factory functions load weights with `torch.hub.load_state_dict_from_url(..., check_hash=True)` when `pretrained=True`.
- Downloaded files follow the PyTorch Hub cache, not a custom `root` folder.
- `resnet50/101/152` are registry-backed baselines and do not have pretrained URLs in this release.
- `classes` must remain `1000` if you want pretrained ImageNet weights to load without a classifier mismatch.
