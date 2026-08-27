# Keras backbones and preprocessing

The bundled `segmentation_models` package supports the following backbone names
in this snapshot:

- `vgg16`
- `vgg19`
- `resnet18`
- `resnet34`
- `resnet50`
- `resnet101`
- `resnet152`
- `resnext50`
- `resnext101`
- `densenet121`
- `densenet169`
- `densenet201`
- `inceptionv3`
- `inceptionresnetv2`

## Preprocessing mapping

| Backbone family | Preprocessing |
| --- | --- |
| VGG | Keras `preprocess_input` for the VGG application model |
| ResNet | BGR channel reversal helper (`[..., ::-1]`) |
| ResNeXt | Identity helper in this snapshot |
| DenseNet | Keras `preprocess_input` for DenseNet |
| Inception V3 | Keras `preprocess_input` for Inception V3 |
| Inception-ResNet V2 | Keras `preprocess_input` for Inception-ResNet V2 |

Use `get_preprocessing(backbone)` when you want the matching function.

## Weight catalog notes

- The classification-models bundle includes `imagenet` weights for the listed
  backbones and additional variants for some ResNet / ResNeXt models.
- Some weights require `include_top=True` versus `False` consistency.
- The weight downloader uses Keras' cache and will fetch archives from the
  network unless they are already present.

## Builder behavior that depends on backbones

- `Unet`, `Nestnet`, and `Xnet` all use `get_backbone(backbone_name, ...,
  include_top=False)`.
- `PSPNet` also chooses a backbone-specific feature layer based on the requested
  downsample factor.
- Input shape constraints come from the underlying backbone, not only from the
  segmentation head.

## Shape reminders

- VGG16 needs at least `48x48` inputs.
- PSPNet with `downsample_factor=8` requires H and W divisible by `48`.
- Some backbones accept larger or differently constrained inputs, but the shape
  guard still comes from the selected architecture.

## Reference-only test data

The classification-models test bundle includes a `seagull.jpg` example and a
network-dependent ImageNet test. Use those as evidence, not as the default
runtime path.
