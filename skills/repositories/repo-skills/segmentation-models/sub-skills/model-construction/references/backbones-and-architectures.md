# Backbones and architecture selection

Segmentation Models combines one of four segmentation decoders with a classification backbone encoder. The model constructor creates a Keras `Model`; choose the decoder for the task shape and choose the backbone for the speed/accuracy/memory trade-off.

## Supported architectures

| Architecture | Best fit | Constructor notes |
| --- | --- | --- |
| `Unet` | Strong default for binary or multiclass segmentation, especially when preserving fine spatial detail matters. | Encoder-decoder with skip concatenations. Defaults to `classes=1`, `activation="sigmoid"`, `decoder_block_type="upsampling"`, and five decoder filter stages `(256, 128, 64, 32, 16)`. |
| `Linknet` | Faster/lighter encoder-decoder tasks where speed is important and the output still needs input-resolution masks. | Uses additive skip-style decoder blocks. Defaults to `classes=1`, `activation="sigmoid"`, `decoder_filters=(None, None, None, None, 16)` so most decoder channels are inferred from encoder skips. |
| `FPN` | Objects or classes appearing at multiple scales; multiclass semantic segmentation with strong feature pyramid aggregation. | Defaults to `classes=21`, `activation="softmax"`, `pyramid_block_filters=256`, and `pyramid_aggregation="concat"`. Use `"sum"` for lower-channel aggregation. |
| `PSPNet` | Scene parsing/global context where fixed image size is acceptable. | Requires concrete `input_shape`; height and width must be divisible by `6 * downsample_factor`. Defaults to `input_shape=(384, 384, 3)`, `classes=21`, `activation="softmax"`, `downsample_factor=8`. |

## Supported backbone names

Use exact lowercase names:

- ResNet: `resnet18`, `resnet34`, `resnet50`, `resnet101`, `resnet152`
- SE-ResNet: `seresnet18`, `seresnet34`, `seresnet50`, `seresnet101`, `seresnet152`
- SE-ResNeXt: `seresnext50`, `seresnext101`
- SENet: `senet154`
- ResNeXt: `resnext50`, `resnext101`
- VGG: `vgg16`, `vgg19`
- DenseNet: `densenet121`, `densenet169`, `densenet201`
- Inception: `inceptionresnetv2`, `inceptionv3`
- MobileNet: `mobilenet`, `mobilenetv2`
- EfficientNet: `efficientnetb0`, `efficientnetb1`, `efficientnetb2`, `efficientnetb3`, `efficientnetb4`, `efficientnetb5`, `efficientnetb6`, `efficientnetb7`

Programmatic listing:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

names = sm.get_available_backbone_names()
```

Avoid unsupported Keras-Applications names such as `xception`, `nasnetlarge`, `nasnetmobile`, `resnet50v2`, `resnet101v2`, and `resnet152v2`; they are not exposed by this package version.

## Backbone selection heuristics

- **Start simple:** `resnet34`, `resnet50`, `efficientnetb0`, `mobilenetv2`, and `vgg16` are practical first choices depending on accuracy/memory needs.
- **Small/fast deployments:** `mobilenet`, `mobilenetv2`, `resnet18`, `seresnet18`, and `efficientnetb0` reduce parameters and memory.
- **Balanced accuracy:** `resnet34`, `resnet50`, `densenet121`, and `efficientnetb1`-`efficientnetb3` are common middle-ground backbones.
- **Heavy/high-capacity experiments:** `resnet101/152`, `seresnet101/152`, `seresnext101`, `senet154`, `densenet169/201`, and `efficientnetb4`-`efficientnetb7` can be memory-intensive. Use smaller image sizes or no prediction smoke run when only validating construction.
- **Legacy/default compatibility:** the constructors default to `vgg16`; it is easy to reason about but not always the best speed/accuracy trade-off.
- **Non-RGB inputs:** do not combine `encoder_weights="imagenet"` directly with a non-3-channel `input_shape`. Either set `encoder_weights=None` or put a learned/adapted channel-mapping layer before a 3-channel pretrained model.

## Architecture recipes

### Binary foreground/background Unet

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

BACKBONE = "resnet34"
preprocess_input = sm.get_preprocessing(BACKBONE)
model = sm.Unet(
    BACKBONE,
    input_shape=(None, None, 3),
    classes=1,
    activation="sigmoid",
    encoder_weights="imagenet",
)
```

### Mutually exclusive multiclass FPN

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

model = sm.FPN(
    "efficientnetb0",
    input_shape=(256, 256, 3),
    classes=5,          # include background if your mask encoding needs it
    activation="softmax",
    encoder_weights="imagenet",
    pyramid_aggregation="concat",
)
```

### Lightweight Linknet for speed

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

model = sm.Linknet(
    "mobilenetv2",
    input_shape=(None, None, 3),
    classes=1,
    activation="sigmoid",
    encoder_weights="imagenet",
)
```

### Fixed-size PSPNet with offline encoder

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

model = sm.PSPNet(
    "resnet18",
    input_shape=(96, 96, 3),
    classes=3,
    activation="softmax",
    encoder_weights=None,
    downsample_factor=8,
)
```

### Non-RGB model trained from scratch

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

model = sm.Unet(
    "resnet34",
    input_shape=(None, None, 4),
    classes=2,
    activation="sigmoid",
    encoder_weights=None,
)
```

## Shape rules by architecture

- `Unet`, `Linknet`, `FPN`: constructor defaults allow `(None, None, 3)`, but real input height/width should generally be multiples of 32 so encoder and decoder feature maps align through downsampling and upsampling. Native construction tests used shapes such as `32x32` and `256x256`.
- `PSPNet`: no dynamic height/width. For `downsample_factor=4`, use height/width divisible by `24`; for `8`, divisible by `48`; for `16`, divisible by `96`. The default `384x384` is valid for all three factors.

## Preprocessing and image format

- Use `sm.get_preprocessing(backbone_name)` for the exact backbone used in the model.
- Keep image channel order and Keras image data format consistent across preprocessing, model construction, and data batches.
- The common path is `channels_last` with batch shape `(batch, height, width, channels)`.
- If using `channels_first`, set the Keras backend image data format before model construction and use matching input and batch shapes.
