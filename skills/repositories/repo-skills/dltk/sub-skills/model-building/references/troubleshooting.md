# Model-building troubleshooting

## `inputs are required to have a rank of 5`

DLTK's 3D residual unit and network builders assert a static rank of five. Supply channel-last input shaped `[batch, x, y, z, channels]`, for example `[1, 16, 32, 32, 1]`. A 2D `[batch, x, y, channels]` tensor, a flattened vector, or a label tensor with an accidental channel axis is not interchangeable. Fix the Reader's `example_shapes` and feature construction in [data-pipelines](../../data-pipelines/SKILL.md); do not add arbitrary singleton axes to hide a data contract error.

## `len(strides) == len(filters)` assertion

The encoder schedules are parallel sequences. For each entry in `filters`, provide one three-element spatial stride in `strides`. Start with, for example:

```python
filters = (2, 4)
strides = ((1, 1, 1), (1, 1, 1))
```

Then add downsampling only after the all-one graph executes. This applies to `resnet_3d`, both residual UNets, `residual_fcn_3d`, `convolutional_autoencoder_3d`, and the DCGAN generator/discriminator. For a super-resolution network, validate that `upsampling_factor` itself has exactly three entries.

## Skip concat/add shape mismatch

A UNet skip uses `tf.concat` and an FCN upscore uses `tf.add`; spatial dimensions must match exactly. The most common causes are:

- the input extent is not compatible with cumulative encoder strides;
- an odd spatial extent rounded differently under strided `same` convolution and transpose convolution;
- a skip stride was copied in the wrong order; or
- `filters` and `strides` were changed independently.

Build a tiny all-one schedule first, print each static tensor shape from graph construction, and introduce one factor of two at a time. Use an input whose `x`, `y`, and `z` dimensions are divisible by the product of the relevant downsampling factors. DLTK does not crop or pad these UNet/FCN skip branches automatically.

## Static channel/spatial shape is `None`

`linear_upsample_3d` reads the static rank and channel count from `inputs.get_shape()`. The autoencoder also computes a static product of encoded dimensions before its dense bottleneck, and GAN discriminator flattening uses a static product. Make `channels` and the encoded spatial extents known at graph construction. If a Reader produces unknown dimensions, set `example_shapes` or an explicit `Tensor.set_shape` from the real contract before calling the builder; do not guess dimensions.

## Batch normalization behaves incorrectly

Every major network passes `training=(mode == tf.estimator.ModeKeys.TRAIN)` to `tf.layers.batch_normalization`. Ensure the enclosing `model_fn` passes its `mode` through unchanged. In TRAIN, collect update ops and place the optimizer minimize call under their control dependencies:

```python
update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
with tf.control_dependencies(update_ops):
    train_op = optimizer.minimize(loss, global_step=tf.train.get_global_step())
```

In EVAL/PREDICT, initialize moving-statistic variables and do not substitute a Python boolean that is always true. The builders do not create this training operation for you. See [training-and-estimators](../../training-and-estimators/SKILL.md).

## Unexpected output key or rank

Use the exact dictionary keys:

- ResNet and segmentation: `logits`, `y_prob`, `y_`.
- Autoencoder: `hidden_units`, `x_`.
- DCGAN generator: `gen`.
- DCGAN discriminator: `logits`, `probs`, `pred`.
- Super-resolution: `x_`.

Segmentation logits are `[B, X, Y, Z, K]`, probabilities have the same rank, and `y_` is `[B, X, Y, Z]` for multiclass output. ResNet logits/probabilities are `[B, K]` and `y_` is `[B]`. If a downstream Estimator or exporter expects a different key, adapt that boundary rather than renaming internal outputs in a way that breaks the public contract. Route export and predictor concerns to [inference-and-deployment](../../inference-and-deployment/SKILL.md).

## One-class output is surprising

The package applies softmax to `logits` for `y_prob`. With one output class, that probability is one. The one-class `y_` branch thresholds the raw output at `0.5`; it is not a sigmoid probability branch. For scalar regression, use `logits` directly and choose a regression loss in the training layer.

## Loss or metric is `NaN`

`dice_loss` can produce an empty reduction if all selected sample/class entries are absent after `only_present` or background filtering. Check label presence and class count. The NumPy `dice` metric returns `NaN` when both predictions and labels lack a class because its denominator is zero. Mask absent classes before aggregating a report. `abs_vol_difference` adds `1e-6` to the true count, while `crossentropy` expects one-hot labels and uses logits by default.

## Residual filters/strides do not align

`vanilla_residual_unit_3d` supports non-unit strides and differing input/output filters. It pools the residual path for a non-unit stride, pads when `in_filters < out_filters`, and uses a 3D convolution when `in_filters > out_filters`. A mismatch that remains after this conversion usually indicates a spatial-size problem or an unknown static channel count. Check `inputs.get_shape().as_list()[-1]`, use three-element positive strides, and test on an even, small spatial extent.

## DeepMedic does not build

This implementation has tightly coupled normal/subsampled pathway crop shapes, `VALID` convolutions by default, and residual locations. Its source explicitly labels it work in progress and warns it will not yield the original DeepMedic accuracy. It also uses linear/bilinear-style upsampling where the original uses repeat upsampling. Start with a task-specific, internally consistent configuration and static input large enough for every crop; do not treat a default-configuration failure as evidence that the other segmentation builders are invalid.

## GAN outputs or discriminator predictions look wrong

The generator expects a rank-5 noise tensor and returns `gen`; it does not add a final sigmoid/tanh in the package implementation. The discriminator returns `probs=tf.nn.sigmoid(logits)` but defines `pred` by comparing the raw `logits` to `0.5`. Preserve that behavior when compatibility matters. The repository's DCGAN application uses a custom monitored-session loop; network construction alone is not GAN training. Route optimizer/session orchestration to [training-and-estimators](../../training-and-estimators/SKILL.md).

## Super-resolution appears to invent detail

`simple_super_resolution_3d` only upsamples through learned transpose convolution. The repository application constructs its low-resolution input by artificial downsampling and trains against the original high-resolution target. Verify that degradation provenance before interpreting a result; this example does not prove recovery of unknown high-resolution information.

## TensorFlow import or missing legacy symbols

This route is verified for Python 3.7 and TensorFlow 1.15.0. It intentionally uses `tf.Session`, `tf.layers`, `tf.contrib` regularizers in application code, and `tf.estimator`. If those legacy symbols are absent or altered, use the prepared legacy environment or stop at the compatibility diagnosis; do not rewrite the skill's API claims.
