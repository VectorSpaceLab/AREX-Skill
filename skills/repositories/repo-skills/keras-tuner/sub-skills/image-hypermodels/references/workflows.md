# Image Hypermodels Workflows

Use these procedures after reading the applicable sections of
`api-reference.md`. Keep all expensive work explicit and bounded.

## 1. Select the input and model contract

1. Inspect the installed version and backend image layout:

   ```python
   import keras_tuner
   from keras_tuner.backend import keras

   print(keras_tuner.__version__)
   print(keras.backend.image_data_format())
   ```

2. Define an image shape without a batch axis. Use channels-last or
   channels-first according to the printed layout. If the model is being
   inserted into an existing graph, create one `keras.Input` and pass it as
   `input_tensor`; otherwise pass `input_shape`.
3. Decide whether the model is a classifier or feature extractor before
   constructing it. ResNet/Xception classifiers need `classes`; feature
   extractors should use `include_top=False`. EfficientNet is always a
   classifier and needs `classes`.
4. Create a fresh `HyperParameters` object for a first smoke build. Reuse the
   same object only when intentionally composing hypermodels or testing
   deterministic overrides.

## 2. Deterministic ResNet/Xception smoke build

Build a feature extractor first to avoid training and compiler work:

```python
from keras_tuner import HyperParameters
from keras_tuner.applications import HyperResNet, HyperXception

hp = HyperParameters()
resnet = HyperResNet(input_shape=(64, 64, 3), include_top=False)
features = resnet.build(hp)
assert features.name == "ResNet"
assert hp.get("version") == "v2"

hp = HyperParameters()
hp.Fixed("pooling", "avg")
xception = HyperXception(
    input_shape=(64, 64, 3), classes=4, include_top=False
)
features = xception.build(hp)
assert features.name == "Xception"
assert hp.get("pooling") == "avg"
```

Use a larger shape such as `(128, 128, 3)` when a native backend complains
about spatial dimensions after repeated striding. For a classifier build,
pre-register compatible values and assert `model.output_shape == (None,
classes)`, then verify that the model is compiled before calling `fit` or
`train_on_batch`.

Useful deterministic overrides include:

```python
hp.Choice("version", ["v1"])
hp.Fixed("conv3_depth", 8)
hp.Fixed("pooling", "max")
```

for ResNet, and:

```python
hp.Fixed("activation", "selu")
hp.Fixed("num_residual_blocks", 2)
hp.Fixed("pooling", "flatten")
```

for Xception. Do not register a value outside the hypermodel's domain unless
the goal is specifically to test the resulting conflict.

## 3. Build a transform-only augmentation model

Use fixed mode when the goal is to apply every enabled transform in a known
order:

```python
from keras_tuner import HyperParameters
from keras_tuner.applications import HyperImageAugment

hp = HyperParameters()
augment = HyperImageAugment(
    input_shape=(64, 64, 3),
    rotate=[0.1, 0.2],
    translate_x=0.15,
    translate_y=None,
    contrast=None,
    augment_layers=0,
)
model = augment.build(hp)
assert model.name == "image_augment"
assert model.output_shape == (None, None, None, 3)
assert hp.get("factor_rotate") == 0.1
assert "factor_translate_y" not in hp.values
```

Use positive `augment_layers` when each sample should receive a randomly
selected transform per layer:

```python
hp = HyperParameters()
hp.Fixed("augment_layers", 2)
hp.Fixed("factor_rotate", 0.1)
hp.Fixed("factor_translate_x", 0.0)
hp.Fixed("factor_translate_y", 0.0)
hp.Fixed("factor_contrast", 0.0)
augment = HyperImageAugment(input_shape=(64, 64, 3), augment_layers=[1, 3])
model = augment.build(hp)
assert model.name == "image_rand_augment"
```

Validate scalar and two-value factors in caller code: use values in `[0, 1]`,
use exactly two elements for a range, and keep the lower endpoint no larger
than the upper endpoint. Setting a transform to `None` excludes its
`factor_<name>` hyperparameter entirely.

## 4. Compose augmentation with EfficientNet

`HyperEfficientNet` accepts a fixed Keras model or a `HyperModel`. A
`HyperModel` is built with the same `hp`, which makes its factor choices part of
the EfficientNet trial:

```python
from keras_tuner import HyperParameters
from keras_tuner.applications import HyperEfficientNet, HyperImageAugment

hp = HyperParameters()
augment = HyperImageAugment(
    input_shape=(64, 64, 3), augment_layers=0, contrast=None
)
hypermodel = HyperEfficientNet(
    input_shape=(64, 64, 3), classes=4, augmentation_model=augment
)
```

The augmentation is applied before the variant-specific resize and backbone.
Do not use an arbitrary callable or a bare layer as `augmentation_model`; wrap
it in a Keras `Model` or `HyperModel`.

This workflow is intentionally incomplete until the weight policy is decided.
The implementation invokes Keras Applications EfficientNet without a
`weights` override, so the installed API default (`weights="imagenet"`) may
fetch weights. Before `hypermodel.build(hp)`:

1. Decide whether network access is permitted and whether the expected weight
   cache is present.
2. Start with version `B0`, a small synthetic input, and a single bounded
   trial/build.
3. Run under an external timeout and capture the cache/download log.
4. If offline or cache-missing, stop before build; use ResNet/Xception or the
   augmentation-only workflow for a no-network smoke check. There is no
   `weights=None` parameter on this hypermodel.

## 5. Input-tensor graph composition

Use one source tensor when a preprocessing graph must feed the image model:

```python
inputs = keras.Input(shape=(64, 64, 3), name="image")
aug_model = keras.Sequential(
    [keras.layers.RandomRotation(0.1)], name="fixed_aug"
)
# Pass a Keras Model, not the layer itself, as augmentation_model.
model = HyperEfficientNet(
    input_tensor=inputs, classes=4, augmentation_model=aug_model
)
```

After building, check the source input identity and the presence/order of the
augmentation layer before the backbone. If both `input_shape` and
`input_tensor` are supplied, the tensor path wins; remove the redundant shape
to make graph intent clear.

## 6. Safe staged execution

A safe order for automation is:

1. From the skill root, run `sub-skills/image-hypermodels/scripts/smoke_build.py`
   with its default augmentation-only mode.
2. If needed, opt into ResNet/Xception feature-extractor builds with the
   script's explicit heavy-build flag and an external timeout.
3. Only after a user-approved cache/network decision, opt into EfficientNet
   with both heavy-build and network permission flags plus an external timeout.
4. Run the actual tuner with a small `max_trials`, then expand architecture
   variants and input sizes after observing memory, compile, and training time.

The flags are opt-in gates, not a security sandbox or process timeout. A
successful flag check does not prove that the build is bounded, offline, or
safe for the available memory; enforce the timeout and network policy outside
this helper.

Keep build and train phases separate. A successful graph build does not prove
that the chosen input resolution, labels, loss, memory budget, and backend can
complete training.
