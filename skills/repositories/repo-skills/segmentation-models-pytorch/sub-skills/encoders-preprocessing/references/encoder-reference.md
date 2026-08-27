# Encoder Reference

SMP exposes encoder/backbone selection through both direct encoder helpers and model constructors. Direct helpers live under `segmentation_models_pytorch.encoders`; model constructors pass the same values as `encoder_name`, `encoder_weights`, `encoder_depth`, and sometimes `encoder_output_stride`.

## Core APIs

```python
import segmentation_models_pytorch as smp
from segmentation_models_pytorch.encoders import get_encoder, get_encoder_names

names = get_encoder_names()
encoder = get_encoder(
    "resnet34",
    in_channels=3,
    depth=5,
    weights=None,
    output_stride=32,
)
```

- `get_encoder_names()` returns the native SMP encoder registry. Installed inspection found 76 native/ported registry names.
- `get_encoder(name, in_channels=3, depth=5, weights=None, output_stride=32, **kwargs)` instantiates an encoder and returns a PyTorch module.
- `depth` controls how many encoder stages are returned. Native encoder tests expect `depth + 1` feature maps because the input tensor is included as the first feature.
- `output_stride=32` is the default. Dilated modes usually use `8` or `16`; unsupported values or unsupported families raise errors.
- `in_channels` can be changed from RGB. When pretrained weights are used, SMP adapts the first convolution; for `None` weights it initializes randomly.

## Native Families

The native registry covers common segmentation backbones and their SMP-maintained weight metadata:

- ResNet and ResNeXt: `resnet18`, `resnet34`, `resnet50`, `resnext50_32x4d`, and related variants.
- DPN, VGG, SENet, DenseNet, Xception, InceptionResNetV2, and InceptionV4.
- EfficientNet and selected ported timm EfficientNet / SKNet names.
- MobileNet, MobileOne, and Mix Vision Transformer (`mit_b0` through `mit_b5`).

Use a native name when you want stable SMP registry behavior, string pretrained weights such as `"imagenet"`, and preprocessing metadata from SMP's own settings.

## Timm Universal Encoders

SMP also supports many timm models through the `tu-` prefix:

```python
model = smp.Unet(
    encoder_name="tu-resnet18",
    encoder_weights=True,
    classes=1,
)
```

Rules for `tu-` encoders:

- Use `tu-<timm-model-name>` or `tu-<timm-model-name>.<pretrained-tag>` as the encoder name.
- Set `encoder_weights=True` / `weights=True` to ask timm for pretrained weights.
- Set `encoder_weights=None` / `weights=None` for random initialization and offline-safe instantiation.
- Avoid string weights such as `"imagenet"`; SMP warns that `tu-` weights should be `True` or `None` because the pretrained tag belongs in the model name.
- `output_stride` is passed to timm only when it is not the default `32`. Some timm models, especially transformer-like families, do not support dilated output stride.
- `depth` must be from 1 to 5 for `TimmUniversalEncoder`.

Timm universal encoders normalize feature hierarchies across model styles:

- Traditional-style models often return feature scales like 1/2, 1/4, 1/8, 1/16, 1/32.
- Transformer-style timm models often start at 1/4, so SMP inserts an empty 1/2-scale feature for segmentation compatibility.
- VGG-style timm models can include scale-1 features.

## Deprecated `timm-` Prefix

SMP still contains older `timm-` ported names and conversion logic, but the current guidance is to prefer `tu-` names.

- Any encoder name starting with `timm-` emits a deprecation warning.
- Some old names are automatically converted to equivalent `tu-` names: `timm-regnet*`, `timm-res2*`, `timm-resnest*`, `timm-mobilenetv3*`, and `timm-gernet*`.
- `timm-mobilenetv3*` conversion adds timm's `tf_` prefix after `tu-`.
- Other old ported `timm-` names may still be registry names, but new guidance should use `tu-` when a timm universal equivalent exists.

Migration examples:

| Deprecated request | Preferred request | Notes |
| --- | --- | --- |
| `timm-resnest50d` | `tu-resnest50d` | Auto-converted by `get_encoder`, but still warns. |
| `timm-res2net50_26w_4s` | `tu-res2net50_26w_4s` | Use `True` or `None` weights with `tu-`. |
| `timm-mobilenetv3_large_100` | `tu-tf_mobilenetv3_large_100` | SMP conversion maps `mobilenetv3` to timm's `tf_` name. |
| `timm-efficientnet-b0` | Prefer native `efficientnet-b0` or a timm `tu-...` equivalent | This is a ported registry family; do not assume all `timm-` names auto-convert. |

## DPT-Compatible Encoders

DPT is different from ordinary encoder-backed architectures. It uses `TimmViTEncoder` internally and accepts only `tu-` encoder names:

```python
model = smp.DPT(
    encoder_name="tu-vit_base_patch16_224.augreg_in21k",
    encoder_weights="imagenet",
    encoder_depth=4,
    classes=1,
)
```

DPT caveats:

- The `smp.DPT` constructor strips `tu-` and passes the timm model name into `TimmViTEncoder`.
- `encoder_weights` is treated as a boolean request: any non-`None` value enables pretrained timm loading for the selected name.
- `encoder_depth` must not exceed the number of blocks exposed by timm feature metadata; DPT defaults to 4.
- `encoder_output_indices` can override uniformly sampled block indices, but its length must equal `encoder_depth` and each index must be in range.
- DPT does not use dilated `output_stride`; `TimmViTEncoder` rejects `output_stride`.
- Many ViT backbones have fixed trained image sizes. If a non-trained resolution is required, pass `dynamic_img_size=True` only when the timm model supports it, and still check `model.encoder.is_fixed_input_size` plus `model.encoder.input_size`.
- The DPT docs list tested compatible `tu-` ViT-style names; do not assume every timm transformer works.

## Choosing Safely

- For ordinary Unet/FPN/Linknet-style models, start with native `resnet34`, `resnet50`, `mobilenet_v2`, `efficientnet-b0`, `mit_b0`, or `mobileone_s0` depending on speed/accuracy needs.
- For broad timm coverage, use `tu-...` and validate with the script in `scripts/check_encoder.py` before committing to an architecture.
- For DeepLabV3, DeepLabV3+, and PAN, check whether the encoder supports the requested output stride/dilation.
- For fully offline runs, instantiate with `encoder_weights=None` and avoid APIs that fetch missing pretrained configs unless the metadata is already cached or locally encoded.
