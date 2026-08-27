# Model Reference

Read this for source-derived model facts before editing commands, debugging
TensorFlow graph construction, or interpreting checkpoint compatibility.

## ResNet wrapper

The repository defines a `ResNet` class with this operating contract:

```text
ResNet(images, is_training).build_model() -> logits tensor
```

Source-derived facts:

- `images` is expected as a 4-D tensor shaped `[batch, image_size, image_size, 3]`.
- If `FLAGS.data_format == "NCHW"`, the constructor transposes images to
  `[batch, channels, height, width]` before convolution.
- Supported `FLAGS.resnet_size` values are `50`, `101`, and `152`.
- Filter widths by stage are `[256, 512, 1024, 2048]`.
- Stage block counts are:
  - ResNet-50: `[3, 4, 6, 3]`
  - ResNet-101: `[3, 4, 23, 3]`
  - ResNet-152: `[3, 8, 36, 3]`
- `build_model()` stores `net.feat` after global average pooling and `net.logit`
  after the dense logits layer.
- CPU graph smokes with TensorFlow 1.6 and `class_num=1000` produced logits
  shape `[1, 1000]`. Feature layout follows `data_format`: with explicit
  `NCHW`, `net.feat` is `[1, 2048, 1, 1]`; with the channels-last path it is
  `[1, 1, 1, 2048]`.

## Preprocessing and input records

Training parses TFRecords with features `width`, `height`, `image`, `label`, and
`name`. Multi-label pretraining decodes `label` from raw `float32` bytes and
reshapes it to `[class_num]`. Finetuning reads `label` as a scalar integer and
one-hot encodes it.

The preprocessing path uses:

- random distorted bounding boxes for training;
- central crop and bilinear resize for evaluation;
- horizontal flips, random rotation via `tf.contrib.image.rotate`, and color
  distortion in training;
- final rescale from `[0, 1]` to `[-1, 1]`.

Because `tf.contrib` is required, a TensorFlow 2-only runtime is not faithful to
the original model code.

## Multi-label pretraining loss

The pretraining script builds an Estimator `model_fn` with:

- sigmoid-style `tf.nn.weighted_cross_entropy_with_logits`;
- non-negative mask that ignores labels equal to `-1`;
- dynamic positive and selected-negative loss coefficients controlled by
  `mask_thres`, `neg_select`, and per-class counters;
- L2 weight decay excluding batch-normalization variables;
- Momentum optimizer and piecewise learning-rate decay with warmup support.

Use this only as source-derived operating guidance. Do not claim loss behavior
was numerically reproduced unless a separate test runs the training graph.

## Finetuning graph

The finetuning script builds a manual multi-GPU tower graph over ImageNet-style
scalar labels. It averages gradients across towers and can optionally restrict
trainable variables when `FixBlock2=True`.

Checkpoint restoration skips variables containing `global_step`, `Momentum`, or
`logits`, then assigns matching variables by name. This means a checkpoint can
partially restore the backbone while leaving a new classification head.

## Data format warning

The flag defaults use `data_format='channels_first'`, while the ResNet code
specifically checks for `"NCHW"`. The public shell examples pass `NCHW`. When
constructing commands, prefer explicit `--data_format NCHW` for GPU workflows or
validate that the runtime handles the intended format before running.
