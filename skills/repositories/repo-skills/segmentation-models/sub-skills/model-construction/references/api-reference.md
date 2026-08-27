# Segmentation Models constructor API reference

This reference captures the model-construction surface of Segmentation Models 1.0.1. The constructors return ordinary Keras `Model` instances using the active `keras` or `tf.keras` backend selected by Segmentation Models.

## Framework selection

Select the framework before importing and constructing objects:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"  # or "keras"
import segmentation_models as sm

assert sm.framework() in {"tf.keras", "keras"}
```

`sm.set_framework(name)` accepts `"tf.keras"` or `"keras"`, case-insensitively. Prefer setting `SM_FRAMEWORK` before import because Segmentation Models injects the selected Keras backend, layers, models, utils, and losses into its constructors and custom objects.

Generic installation pattern:

```bash
pip install segmentation-models
# Install a suitable TensorFlow/Keras backend separately for the target platform.
```

## Shared constructor concepts

- `backbone_name`: lowercase name of the classification encoder used as the feature extractor.
- `input_shape`: Keras image shape. With the default `channels_last` format it is `(height, width, channels)`.
- `classes`: output channels in the segmentation mask.
- `activation`: Keras activation used for the final mask layer (`"sigmoid"`, `"softmax"`, `"linear"`, etc.).
- `weights`: optional path to full segmentation-model weights to load after construction. This is not the same as `encoder_weights`.
- `encoder_weights`: `"imagenet"` or `None`. `"imagenet"` may download pretrained encoder weights and is RGB-oriented. Use `None` for offline smoke tests and non-RGB channel counts unless inputs are mapped to 3 channels externally.
- `encoder_freeze`: if `True`, backbone layers are marked non-trainable during construction.
- `encoder_features`: for `Unet`, `Linknet`, and `FPN`, either `"default"` or a list of encoder layer names/indices used as skip/pyramid features.
- `**kwargs`: forwarded through Keras-applications/classification-models construction and filtered for Segmentation Models' injected Keras submodules.

## Constructor signatures and defaults

### Unet

```python
sm.Unet(
    backbone_name="vgg16",
    input_shape=(None, None, 3),
    classes=1,
    activation="sigmoid",
    weights=None,
    encoder_weights="imagenet",
    encoder_freeze=False,
    encoder_features="default",
    decoder_block_type="upsampling",
    decoder_filters=(256, 128, 64, 32, 16),
    decoder_use_batchnorm=True,
    **kwargs,
)
```

Important validation/behavior:

- `decoder_block_type` must be `"upsampling"` or `"transpose"`.
- Dynamic spatial dimensions are allowed, but actual height and width should generally be divisible by 32.
- The final output shape preserves spatial resolution for valid encoder-decoder-aligned inputs and has `classes` channels.

Typical binary model:

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

### FPN

```python
sm.FPN(
    backbone_name="vgg16",
    input_shape=(None, None, 3),
    classes=21,
    activation="softmax",
    weights=None,
    encoder_weights="imagenet",
    encoder_freeze=False,
    encoder_features="default",
    pyramid_block_filters=256,
    pyramid_use_batchnorm=True,
    pyramid_aggregation="concat",
    pyramid_dropout=None,
    **kwargs,
)
```

Important validation/behavior:

- `pyramid_aggregation` must be `"sum"` or `"concat"`.
- `pyramid_block_filters` controls FPN block capacity; the segmentation-head filters are half this value.
- Dynamic spatial dimensions are allowed, but actual height and width should generally be divisible by 32.

Multiclass FPN example:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

model = sm.FPN(
    "efficientnetb0",
    input_shape=(256, 256, 3),
    classes=4,
    activation="softmax",
    encoder_weights="imagenet",
    pyramid_aggregation="concat",
)
```

### Linknet

```python
sm.Linknet(
    backbone_name="vgg16",
    input_shape=(None, None, 3),
    classes=1,
    activation="sigmoid",
    weights=None,
    encoder_weights="imagenet",
    encoder_freeze=False,
    encoder_features="default",
    decoder_block_type="upsampling",
    decoder_filters=(None, None, None, None, 16),
    decoder_use_batchnorm=True,
    **kwargs,
)
```

Important validation/behavior:

- `decoder_block_type` must be `"upsampling"` or `"transpose"`.
- `None` values in `decoder_filters` let Linknet infer filters from corresponding skip tensors.
- Dynamic spatial dimensions are allowed, but actual height and width should generally be divisible by 32.

Lightweight binary example:

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

### PSPNet

```python
sm.PSPNet(
    backbone_name="vgg16",
    input_shape=(384, 384, 3),
    classes=21,
    activation="softmax",
    weights=None,
    encoder_weights="imagenet",
    encoder_freeze=False,
    downsample_factor=8,
    psp_conv_filters=512,
    psp_pooling_type="avg",
    psp_use_batchnorm=True,
    psp_dropout=None,
    **kwargs,
)
```

Important validation/behavior:

- `input_shape` must not be `None`; height and width must be concrete integers.
- Height and width must each be divisible by `6 * downsample_factor` and at least that size.
- `downsample_factor` must be one of `4`, `8`, or `16`.
- `psp_pooling_type` must be `"avg"` or `"max"`.

Valid small PSPNet example:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

model = sm.PSPNet(
    "resnet18",
    input_shape=(96, 96, 3),  # 96 is divisible by 6 * 8 == 48
    classes=3,
    activation="softmax",
    encoder_weights=None,
    downsample_factor=8,
)
```

## Preprocessing API

Use the preprocessing function that corresponds to the selected backbone:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm

BACKBONE = "resnet34"
preprocess_input = sm.get_preprocessing(BACKBONE)
images = preprocess_input(images)
model = sm.Unet(BACKBONE, encoder_weights="imagenet")
```

Preprocessing is backbone-specific. Do not reuse a preprocessing function from one backbone with another backbone unless deliberately reproducing an old experiment.

## Non-RGB input patterns

Randomly initialized encoder for native non-RGB channels:

```python
model = sm.Unet(
    "resnet34",
    input_shape=(None, None, 1),
    classes=1,
    activation="sigmoid",
    encoder_weights=None,
)
```

Pretrained RGB encoder with an external learned channel mapper:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
from tensorflow import keras
import segmentation_models as sm

channels = 6
base = sm.Unet("resnet34", input_shape=(None, None, 3), encoder_weights="imagenet")
inp = keras.layers.Input(shape=(None, None, channels))
rgb_like = keras.layers.Conv2D(3, (1, 1), name="channel_mapper")(inp)
out = base(rgb_like)
model = keras.models.Model(inp, out, name=base.name)
```

## Output configuration guide

| Task type | `classes` | `activation` | Notes |
| --- | ---: | --- | --- |
| Binary foreground/background | `1` | `"sigmoid"` | Mask shape usually `(H, W, 1)`. |
| Mutually exclusive multiclass | number of mask channels, often foreground classes plus background | `"softmax"` | Use categorical targets aligned with channels. |
| Independent multilabel masks | number of independent labels | `"sigmoid"` | Classes are not mutually exclusive. |
| Logits/custom activation downstream | task-specific | `"linear"` | Pair with losses/metrics that expect logits or raw values. |
