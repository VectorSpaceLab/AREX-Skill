# Model-construction troubleshooting

Use this guide when a Segmentation Models constructor, import, preprocessing call, or shape check fails.

## Framework/import problems

### Symptom: import prints or uses the wrong framework

Example: the runtime announces `Segmentation Models: using 'keras' framework` when the task expected TensorFlow Keras.

Recovery:

1. Restart the Python process or kernel if `segmentation_models` was already imported.
2. Set the framework before import:

   ```python
   import os
   os.environ["SM_FRAMEWORK"] = "tf.keras"  # or "keras"
   import segmentation_models as sm
   print(sm.framework())
   ```

3. Prefer this early environment selection over calling `sm.set_framework(...)` after model objects have already been created.

### Symptom: `ImportError` or `ModuleNotFoundError` for `keras`, `tensorflow`, `efficientnet`, `classification_models`, or `keras_applications`

Recovery:

- Install Segmentation Models and a compatible TensorFlow/Keras backend for the target platform.
- In modern environments prefer `SM_FRAMEWORK=tf.keras` and an installed TensorFlow package.
- If a standalone Keras stack is required, set `SM_FRAMEWORK=keras` before import and ensure standalone Keras is installed.
- If dependency versions are mixed, reinstall Segmentation Models and its companion packages in a clean environment.

## Encoder weight and network problems

### Symptom: constructor hangs/fails while resolving ImageNet weights

Cause: `encoder_weights="imagenet"` can download pretrained encoder weights.

Recovery:

- Use `encoder_weights=None` for offline smoke tests, fast constructor validation, non-RGB input shapes, and CI-style checks.
- If ImageNet initialization is required, run in an environment with network/cache access or pre-populate the Keras weight cache.
- Keep `weights=None` unless loading a full segmentation-model weights file from a known matching architecture.

### Symptom: non-RGB model fails with pretrained encoder weights

Cause: ImageNet encoder weights are defined for RGB-like 3-channel inputs.

Recovery:

- Train from scratch with `encoder_weights=None` and `input_shape=(H, W, channels)`.
- Or build a separate Keras input plus a `Conv2D(3, (1, 1))` channel mapper before a pretrained 3-channel Segmentation Models base model.

## Constructor validation errors

### Symptom: invalid backbone name

Recovery:

- Use exact lowercase names from the supported list, such as `resnet34`, `vgg16`, `mobilenetv2`, or `efficientnetb0`.
- `resnet50v2`, `resnet101v2`, `resnet152v2`, `xception`, `nasnetlarge`, and `nasnetmobile` are not exposed in this package version.
- Check names with:

  ```python
  import os
  os.environ["SM_FRAMEWORK"] = "tf.keras"
  import segmentation_models as sm
  print(sm.get_available_backbone_names())
  ```

### Symptom: `Decoder block type should be in ("upsampling", "transpose")`

Applies to `Unet` and `Linknet`.

Recovery:

```python
model = sm.Unet("resnet34", decoder_block_type="upsampling")
# or
model = sm.Linknet("resnet34", decoder_block_type="transpose")
```

### Symptom: `Aggregation parameter should be in ("sum", "concat")`

Applies to `FPN`.

Recovery:

```python
model = sm.FPN("resnet34", pyramid_aggregation="concat")
# or
model = sm.FPN("resnet34", pyramid_aggregation="sum")
```

### Symptom: `Unsupported pooling type`

Applies to `PSPNet`.

Recovery: set `psp_pooling_type="avg"` or `psp_pooling_type="max"`.

### Symptom: `Unsupported factor` for PSPNet

Recovery: set `downsample_factor` to exactly `4`, `8`, or `16`.

## Input-shape and output-shape problems

### Symptom: PSPNet reports `Input shape should be a tuple of 3 integers` or `Wrong shape ... H and W should be divisible by ...`

Cause: PSPNet validates height/width before backbone construction.

Recovery:

- Use a concrete shape: no `None` height/width for PSPNet.
- Ensure height and width are divisible by `6 * downsample_factor` and at least that size.
- Examples:
  - `downsample_factor=4`: `input_shape=(72, 72, 3)` or larger multiples of `24`.
  - `downsample_factor=8`: `input_shape=(96, 96, 3)`, `(384, 384, 3)`, or other multiples of `48`.
  - `downsample_factor=16`: `input_shape=(192, 192, 3)`, `(384, 384, 3)`, or other multiples of `96`.

### Symptom: Unet/Linknet/FPN build but prediction fails with tensor-size mismatch

Cause: although dynamic shapes can be constructed, the actual image height/width still needs to align through the encoder/decoder downsampling path.

Recovery:

- Use image height and width divisible by 32 for typical full encoder-decoder alignment.
- Try a known-safe constructor/predict smoke size such as `64x64`, `96x96`, `128x128`, or `256x256` depending on architecture.
- If using crops/padding, make preprocessing and data-loader output shapes match model input shape.

### Symptom: output channel count or activation is not what the task expects

Recovery:

- Binary foreground/background: `classes=1, activation="sigmoid"`.
- Mutually exclusive multiclass: `classes=<mask channels>`, usually with `activation="softmax"`.
- Independent multilabel masks: `classes=<labels>`, usually with `activation="sigmoid"`.
- If a loss expects logits, set `activation="linear"` and route loss/metric details to the losses/metrics skill.

## Data format and channels problems

### Symptom: model expects `channels_last` but data is `channels_first`, or vice versa

Recovery:

- The common path is `channels_last`: input shape `(H, W, C)` and batch shape `(N, H, W, C)`.
- If using `channels_first`, set the active Keras backend image data format before construction and ensure preprocessing, input shape, and batches all use that same convention.
- Avoid switching image data format after model objects are created.

### Symptom: preprocessing produces unexpected scales or colors

Recovery:

- Obtain preprocessing from the same backbone used by the model:

  ```python
  preprocess_input = sm.get_preprocessing("resnet34")
  x = preprocess_input(x)
  model = sm.Unet("resnet34", encoder_weights="imagenet")
  ```

- Do not reuse a preprocessing function from a different backbone unless reproducing a legacy run.
- For non-RGB models trained from scratch with `encoder_weights=None`, decide whether backbone-specific ImageNet preprocessing still makes sense for the data; often the data pipeline uses its own normalization.

## Weight-file problems

### Symptom: `model.load_weights(...)` fails during constructor call

Cause: the `weights` argument loads a full segmentation-model weight file after constructing the requested architecture. The file must match architecture, backbone, classes, activation/head shape, and often framework conventions.

Recovery:

- First construct with `weights=None` to prove the architecture is valid.
- Recreate the exact original architecture/backbone/classes before loading weights.
- Do not pass encoder ImageNet weights through `weights`; use `encoder_weights="imagenet"` for encoder initialization.

## Safe diagnostic command

The bundled smoke script builds without network downloads by default:

```bash
python scripts/model_constructor_smoke.py --architecture Unet --backbone resnet18 --height 64 --width 64 --classes 1 --activation sigmoid --framework tf.keras
```

Add `--predict` only when a one-batch forward pass is acceptable in the runtime environment.
