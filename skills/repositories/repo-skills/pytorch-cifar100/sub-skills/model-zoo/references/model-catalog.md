# Model catalog

`utils.get_network(args)` matches exact lowercase tokens. When the README and source disagree, the routed factory in `utils.py` wins.

## Routed through `utils.get_network`

| Family | Routed `-net` tokens | Source module | Factory function(s) | Notes |
| --- | --- | --- | --- | --- |
| VGG | `vgg11`, `vgg13`, `vgg16`, `vgg19` | `models/vgg.py` | `vgg11_bn`, `vgg13_bn`, `vgg16_bn`, `vgg19_bn` | The routed factories are batch-norm VGGs with a 100-class head. |
| DenseNet | `densenet121`, `densenet161`, `densenet169`, `densenet201` | `models/densenet.py` | `densenet121`, `densenet161`, `densenet169`, `densenet201` | README omits `densenet169`; `utils.get_network` still supports it. |
| GoogleNet | `googlenet` | `models/googlenet.py` | `googlenet` | Single routed factory. |
| Inception v3 | `inceptionv3` | `models/inceptionv3.py` | `inceptionv3` | CIFAR-100 adaptation with a 100-class head. |
| Inception v4 / ResNet-v2 | `inceptionv4`, `inceptionresnetv2` | `models/inceptionv4.py` | `inceptionv4`, `inception_resnet_v2` | Both routed factories live in the same module. |
| Xception | `xception` | `models/xception.py` | `xception` | CIFAR-100 classifier head. |
| ResNet | `resnet18`, `resnet34`, `resnet50`, `resnet101`, `resnet152` | `models/resnet.py` | `resnet18`, `resnet34`, `resnet50`, `resnet101`, `resnet152` | CIFAR stem uses `3×3` conv and adaptive pooling. |
| PreActResNet | `preactresnet18`, `preactresnet34`, `preactresnet50`, `preactresnet101`, `preactresnet152` | `models/preactresnet.py` | same token names | Pre-activation residual family. |
| ResNeXt | `resnext50`, `resnext101`, `resnext152` | `models/resnext.py` | `resnext50`, `resnext101`, `resnext152` | Source comments describe `c32x4d`-style variants. |
| ShuffleNet | `shufflenet` | `models/shufflenet.py` | `shufflenet` | Single v1-style token. |
| ShuffleNetV2 | `shufflenetv2` | `models/shufflenetv2.py` | `shufflenetv2` | Single routed factory. |
| SqueezeNet | `squeezenet` | `models/squeezenet.py` | `squeezenet` | Defaults to `class_num=100`. |
| MobileNet | `mobilenet` | `models/mobilenet.py` | `mobilenet(alpha=1, class_num=100)` | Token uses repo defaults. |
| MobileNetV2 | `mobilenetv2` | `models/mobilenetv2.py` | `mobilenetv2` | 100-class head. |
| NASNet | `nasnet` | `models/nasnet.py` | `nasnet` | Source default is `NasNetA(4, 2, 44, 44)`. |
| Attention | `attention56`, `attention92` | `models/attention.py` | `attention56`, `attention92` | README results table says `attention59`; treat that as a typo. |
| SE-ResNet | `seresnet18`, `seresnet34`, `seresnet50`, `seresnet101`, `seresnet152` | `models/senet.py` | same token names | Squeeze-and-excitation residual family. |
| WideResNet | `wideresnet` | `models/wideresidual.py` | `wideresnet(depth=40, widen_factor=10)` | README reports it as `wideresnet-40-10`; the token omits the hyperparameters. |
| StochasticDepth | `stochasticdepth18`, `stochasticdepth34`, `stochasticdepth50`, `stochasticdepth101` | `models/stochasticdepth.py` | `stochastic_depth_resnet18`, `stochastic_depth_resnet34`, `stochastic_depth_resnet50`, `stochastic_depth_resnet101` | `stochastic_depth_resnet152` exists in source but is not mapped by `utils.get_network`. |

## Present in source but not routed by `utils.get_network`

| Source-only entry | Source module | Factory function | Why it matters |
| --- | --- | --- | --- |
| ResNet-in-ResNet | `models/rir.py` | `resnet_in_resnet` | Mentioned in README prose as "resnet in resnet", but there is no `-net` token for it. |
| StochasticDepth-152 | `models/stochasticdepth.py` | `stochastic_depth_resnet152` | Useful if a future source update adds the token, but currently unreachable through the CLI factory. |

## Token selection reminders

- Use the exact lowercase token, not a family name or a hyphenated alias.
- Prefer the routed token list above over README prose when they disagree.
- `train.py`, `test.py`, and `lr_finder.py` all consume the same token space through `utils.get_network`.
