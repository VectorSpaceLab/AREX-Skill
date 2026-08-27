# Image Hypermodels API Reference

This reference records the KerasTuner 1.4.8 image hypermodel contract. The
supporting evidence was the four `keras_tuner/applications` implementation
modules and their matching tests, plus installed-package signature and
backend probes. Runtime instructions in this skill are self-contained and do
not require access to the source checkout.

## Public signatures

```text
HyperResNet(include_top=True, input_shape=None, input_tensor=None,
            classes=None, **kwargs)
HyperXception(include_top=True, input_shape=None, input_tensor=None,
              classes=None, **kwargs)
HyperEfficientNet(input_shape=None, input_tensor=None, classes=None,
                  augmentation_model=None, **kwargs)
HyperImageAugment(input_shape=None, input_tensor=None, rotate=0.5,
                  translate_x=0.4, translate_y=0.4, contrast=0.3,
                  augment_layers=3, **kwargs)
```

All four are `HyperModel` instances. Call `build(hp)` with a
`keras_tuner.engine.HyperParameters` object; construction registers or reads
named hyperparameters on that object.

## Shared input contract

- `input_shape` is an image shape without a batch dimension. Use
  `(height, width, channels)` for `channels_last` and `(channels, height,
  width)` for `channels_first`.
- `input_tensor` is an existing Keras input/output tensor. When it is present,
  each implementation uses it and calls `keras.utils.get_source_inputs()` for
  the model input list. This is the correct option for composing a preceding
  model or a graph with shared inputs.
- The constructor rejects the case where both are absent. It does not reject
  both being present; `input_tensor` takes precedence, so supplying both is
  usually confusing and should be avoided.
- Inspect `keras.backend.image_data_format()` at runtime. ResNet selects its
  batch-normalization axis as `3` for `channels_last` and `1` otherwise. The
  EfficientNet tests also switch their fixture shape when using a backend
  configured for channels-first.

## HyperResNet

### Validation and output

- `include_top=True` is the default and requires `classes` to be non-`None`.
  The classifier output has shape `(batch, classes)`, uses softmax, and the
  model is compiled with categorical cross-entropy and accuracy.
- `include_top=False` omits the classifier and returns the selected pooled
  feature tensor. The model is not compiled by this hypermodel; `classes` is
  accepted but not needed.
- The returned model is named `ResNet`.

### Search space

| Name | Domain | Effective default | Use |
|---|---|---:|---|
| `version` | `v1`, `v2`, `next` | `v2` | residual block family |
| `conv3_depth` | `4`, `8` | `4` | depth of the conv3 stack |
| `conv4_depth` | `6`, `23`, `36` | `6` | depth of the conv4 stack |
| `pooling` | `avg`, `max` | `avg` | global feature pooling |
| `optimizer` | `adam`, `rmsprop`, `sgd` | `adam` | classifier optimizer; top only |
| `learning_rate` | `0.1`, `0.01`, `0.001` | `0.01` | classifier optimizer rate; top only |

`version` also changes whether the initial convolution uses a bias and whether
pre-activation is used. The `next` branch uses grouped/depthwise residual
blocks, so do not assume all versions have identical layer counts.

## HyperXception

### Validation and output

- Its `include_top` and `classes` rules match `HyperResNet`.
- With `include_top=False`, `pooling` may produce a flattened or pooled
  feature output and no classifier compile step is performed.
- With the top, the hypermodel builds dense layers, a softmax classifier, and
  compiles with Adam, categorical cross-entropy, and accuracy. The returned
  model is named `Xception`.

### Search space

| Name | Domain | Effective default |
|---|---|---:|
| `activation` | `relu`, `selu` | `relu` |
| `conv2d_num_filters` | `32`, `64`, `128` | `64` |
| `kernel_size` | `3`, `5` | `3` |
| `initial_strides` | `2` | `2` |
| `sep_num_filters` | integer `128..768`, step `128` | `256` |
| `num_residual_blocks` | integer `2..8` | `4` |
| `pooling` | `flatten`, `avg`, `max` | `avg` |
| `num_dense_layers` | integer `1..3` | `1` |
| `dropout_rate` | `0.0..0.6`, step `0.1` | `0.5` |
| `dense_use_bn` | `True`, `False` | `True` |
| `learning_rate` | `1e-3`, `1e-4`, `1e-5` | `1e-3` |

The effective defaults above are the values observed from the installed
1.4.8 package. KerasTuner may represent a boolean choice as `1` in
`hp.values`; compare its logical value rather than depending on serialization.

## HyperEfficientNet

### Validation and fixed composition

- `classes` is mandatory and must be truthy in the current implementation;
  `None` and `0` are rejected. There is no `include_top` parameter.
- `augmentation_model` must be `None`, a Keras `Model`, or a `HyperModel`.
  A plain integer, callable, or arbitrary layer is rejected. A fixed Keras
  model is applied directly. A `HyperModel` is first built with the same `hp`
  object, so its hyperparameters participate in the same trial.
- The augmentation output is fed into a resize layer and then into the selected
  Keras Applications EfficientNet backbone. The model always adds global
  average/max pooling, dropout, a `classes`-wide softmax head, and compiles
  with SGD (momentum `0.1`), categorical cross-entropy, and accuracy.
- The returned model is named `EfficientNet`.

### Search space

| Name | Domain | Effective default |
|---|---|---:|
| `version` | `B0` through `B7` | `B0` |
| `pooling` | `avg`, `max` | `avg` |
| `top_dropout_rate` | `0.2..0.8`, step `0.2` | `0.2` |
| `learning_rate` | `0.1`, `0.01`, `0.001` | `0.01` |

The selected variant is resized to the following square before the backbone:

| Variant | Resize |
|---|---:|
| `B0` | 224 |
| `B1` | 240 |
| `B2` | 260 |
| `B3` | 300 |
| `B4` | 380 |
| `B5` | 456 |
| `B6` | 528 |
| `B7` | 600 |

### Weight and cost caveat

The implementation calls the Keras Applications constructor with
`include_top=False` and `input_tensor=x` but omits `weights`. In the installed
Keras API, the default is `weights="imagenet"`; therefore a first build can
fetch ImageNet weights, and an offline build can fail when the files are not
cached. `HyperEfficientNet` does not expose a `weights=None` switch. Treat
variant selection and the first build as an explicit, potentially networked
operation. Start with B0 and a small trial budget.

## HyperImageAugment

`HyperImageAugment` returns a transform-only Keras model whose output preserves
the input image shape. It does not add a classifier or compile an optimizer.
Its returned name is `image_augment` in fixed mode and
`image_rand_augment` in positive `augment_layers` mode.

### Transform registration

Each transform argument is interpreted as follows:

- `None` or another false value excludes the transform from the search space.
- A scalar `x` registers a factor range `[0, x]`.
- A two-element sequence `[lo, hi]` registers `[lo, hi]`.
- More than two elements raise `ValueError`; nonnumeric endpoints raise
  `ValueError`.
- The intended factor domain is `[0, 1]`, but the constructor does not fully
  enforce those bounds or ordering. Validate them in caller code before
  starting a search.

The current transform-to-layer mapping is:

| Transform | Keras layer | Factor meaning |
|---|---|---|
| `rotate` | `RandomRotation` | maximum clockwise/counterclockwise rotation as a fraction of pi |
| `translate_x` | `RandomTranslation(x, 0)` | maximum horizontal translation as a ratio of width |
| `translate_y` | `RandomTranslation(0, y)` | maximum vertical translation as a ratio of height |
| `contrast` | `RandomContrast` | maximum contrast-change ratio |

Registered transforms appear in this order: `rotate`, `translate_x`,
`translate_y`, `contrast`.

### Defaults and modes

The constructor defaults are `rotate=0.5`, `translate_x=0.4`,
`translate_y=0.4`, `contrast=0.3`, and `augment_layers=3`.

- **Fixed sequential mode:** falsy `augment_layers` (normally `0` or `None`).
  Each registered transform gets `factor_<name>` as a `Float` with a `0.05`
  step and the registered bounds. A zero factor skips that layer; nonzero
  transforms run in registration order. Scalar defaults therefore create
  `factor_rotate` `[0, 0.5]`, `factor_translate_x` `[0, 0.4]`,
  `factor_translate_y` `[0, 0.4]`, and `factor_contrast` `[0, 0.3]`.
- **RandAugment-like mode:** a positive integer `n` creates
  `augment_layers` in `[1, n]`; a two-integer sequence `[lo, hi]` creates
  `[lo, hi]`. The effective default for an unconstrained integer is the lower
  bound. Each selected layer chooses one registered transform per sample.
  The same named `factor_<name>` values are reused across repeated layer
  constructions in a trial.

`augment_layers` must be an integer or a two-integer sequence when truthy.
The implementation does not provide a separate `randaug_count` or
`randaug_mag` parameter.

## Input tensors and composition checks

For an input tensor workflow, assert `model.inputs == [inputs]` (or the
backend-equivalent tensor identity), then assert the expected spatial/channel
shape. For classifier builds, assert `(None, classes)` output and a compiled
model when `include_top=True` or when using EfficientNet. For feature extractors
and augmentation-only models, assert the expected output feature/image shape
and do not assume an optimizer exists.
