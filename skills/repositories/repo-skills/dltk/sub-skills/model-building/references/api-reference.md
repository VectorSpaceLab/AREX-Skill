# DLTK model-building API reference

Verified against the installed DLTK package version 0.2.1 from the task's public commit and the prepared Python 3.7/TensorFlow 1.15.0 environment. The signatures below preserve the package defaults; `mode` defaults are the actual `tf.estimator.ModeKeys` string values shown by inspection (`'eval'` or `'train'`).

## Core blocks

```text
prelu(inputs, alpha_initializer=tf.constant_initializer())
leaky_relu(inputs, alpha=0.1)
vanilla_residual_unit_3d(
    inputs, out_filters, kernel_size=(3, 3, 3), strides=(1, 1, 1),
    mode=tf.estimator.ModeKeys.EVAL, use_bias=False,
    activation=tf.nn.relu6,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
get_linear_upsampling_kernel(kernel_spatial_shape, out_filters, in_filters,
                             trainable=False)
linear_upsample_3d(inputs, strides=(2, 2, 2), use_bias=False,
                   trainable=False, name='linear_upsample_3d')
```

`prelu` creates a scalar trainable `alpha` variable named `alpha` in the current variable scope and calls `leaky_relu`. Use a scope that prevents duplicate variable names. `vanilla_residual_unit_3d` expects rank 5, batch-normalizes before activation, applies two `tf.layers.conv3d` operations, and uses pooling on the residual path for non-unit strides. It pads or convolves the residual path when input and output channel counts differ. `linear_upsample_3d` builds a fixed linear kernel by default, applies `tf.nn.conv3d_transpose`, and needs statically known input rank and channel count. The `use_bias` argument is present in its signature but the implementation's transpose-convolution call does not add a bias.

## Activations, losses, and NumPy metrics

```text
sparse_balanced_crossentropy(logits, labels)
dice_loss(logits, labels, num_classes, smooth=1e-5,
           include_background=True, only_present=False)
dice(predictions, labels, num_classes)
abs_vol_difference(predictions, labels, num_classes)
crossentropy(predictions, labels, logits=True)
```

`prelu`/`leaky_relu` operate on tensors. `sparse_balanced_crossentropy` uses sparse integer labels, computes softmax probabilities, and derives inverse class-frequency weights from the labels tensor. `dice_loss` uses sparse labels, one-hot encodes them, computes per-sample/per-class soft Dice over spatial axes 1–3, filters absent or background classes according to its flags, and returns a scalar `1 - Dice`. The NumPy `dice` and `abs_vol_difference` functions return `float32` arrays of length `num_classes`; `crossentropy` returns a scalar `float32`, expects one-hot labels, and treats its first argument as logits by default.

## Classification/regression

```text
resnet_3d(
    inputs, num_classes, num_res_units=1,
    filters=(16, 32, 64, 128),
    strides=((1, 1, 1), (2, 2, 2), (2, 2, 2), (2, 2, 2)),
    mode=tf.estimator.ModeKeys.EVAL, use_bias=False,
    activation=tf.nn.relu6,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
```

The initial 3D convolution and residual scales end in batch normalization, activation, global average pooling, and a dense layer named `hidden_units`. The output dictionary is:

- `logits`: `[B, num_classes]`.
- `y_prob`: softmax probabilities with the same shape.
- `y_`: `argmax(logits, axis=-1)` for `num_classes > 1`; for one class, a thresholded int32 tensor based on `logits[..., 0] >= 0.5`.

`len(filters)` must equal `len(strides)`. `num_res_units` is the number of residual units on each non-initial resolution scale.

## Segmentation

```text
upsample_and_concat(inputs, inputs2, strides=(2, 2, 2))
residual_unet_3d(
    inputs, num_classes, num_res_units=1,
    filters=(16, 32, 64, 128),
    strides=((1, 1, 1), (2, 2, 2), (2, 2, 2), (2, 2, 2)),
    mode=tf.estimator.ModeKeys.EVAL, use_bias=False,
    activation=leaky_relu,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
asymmetric_residual_unet_3d(
    inputs, num_classes, num_res_units=1,
    filters=(16, 32, 64, 128),
    strides=((1, 1, 1), (2, 2, 2), (2, 2, 2), (2, 2, 2)),
    mode=tf.estimator.ModeKeys.EVAL, use_bias=False,
    activation=leaky_relu,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
upscore_layer_3d(
    inputs, inputs2, out_filters, in_filters=None, strides=(2, 2, 2),
    mode=tf.estimator.ModeKeys.EVAL, use_bias=False,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
residual_fcn_3d(
    inputs, num_classes, num_res_units=1,
    filters=(16, 32, 64, 128),
    strides=((1, 1, 1), (2, 2, 2), (2, 2, 2), (2, 2, 2)),
    mode=tf.estimator.ModeKeys.EVAL, use_bias=False,
    activation=tf.nn.relu6,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
```

All three complete segmentation networks require rank-5 input and return `logits`, `y_prob`, and `y_`. For multi-class segmentation, `logits` and `y_prob` are `[B, X, Y, Z, num_classes]` and `y_` is `[B, X, Y, Z]`. The one-class branch follows the package's thresholded-logit behavior. UNet concatenates the upsampled decoder with the encoder skip; asymmetric UNet uses one decoder residual unit per scale; FCN uses additive `upscore_layer_3d` skip paths and converts filters before upsampling when needed. In each case, `filters` and `strides` must have equal lengths and the cumulative spatial factors must make each skip branch match.

`deepmedic_3d` has a much larger signature with normal/subsampled pathway filter, kernel, stride, residual, crop, and factor sequences, followed by `fc_filters`, `first_fc_kernel`, `fc_residuals`, `padding='VALID'`, `use_prelu=True`, `mode='eval'`, `use_bias=True`, and initializer/regularizer parameters. Use `inspect.signature` in the installed package or the network smoke script's help-only path before overriding its defaults. It requires compatible static crops and is explicitly a work in progress; do not treat its result as original DeepMedic equivalence.

## Reconstruction, GAN, and super-resolution

```text
convolutional_autoencoder_3d(
    inputs, num_convolutions=1, num_hidden_units=128,
    filters=(16, 32, 64),
    strides=((2, 2, 2), (2, 2, 2), (2, 2, 2)),
    mode=tf.estimator.ModeKeys.TRAIN, use_bias=False,
    activation=tf.nn.relu6,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
dcgan_generator_3d(
    inputs, filters=(256, 128, 64, 32, 1),
    kernel_size=((4, 4, 4), (3, 3, 3), (3, 3, 3), (3, 3, 3), (4, 4, 4)),
    strides=((4, 4, 4), (1, 2, 2), (1, 2, 2), (1, 2, 2), (1, 2, 2)),
    mode=tf.estimator.ModeKeys.TRAIN, use_bias=False)
dcgan_discriminator_3d(
    inputs, filters=(64, 128, 256, 512),
    strides=((2, 2, 2), (2, 2, 2), (1, 2, 2), (1, 2, 2)),
    mode=tf.estimator.ModeKeys.EVAL, use_bias=False)
simple_super_resolution_3d(
    inputs, num_convolutions=1, filters=(16, 32, 64),
    upsampling_factor=(2, 2, 2), mode=tf.estimator.ModeKeys.EVAL,
    use_bias=False, activation=tf.nn.relu6,
    kernel_initializer=tf.initializers.variance_scaling(distribution='uniform'),
    bias_initializer=tf.zeros_initializer(),
    kernel_regularizer=None, bias_regularizer=None)
```

The autoencoder returns `hidden_units` and reconstructed `x_`; its dense bottleneck flattens the statically shaped encoded spatial tensor, so fully unknown spatial dimensions are unsuitable. The generator returns `gen`; the discriminator flattens its final rank-5 activation and returns `logits` `[B, 1]`, sigmoid `probs` `[B, 1]`, and int32 `pred`. Its `pred` comparison is against the discriminator logit at `0.5`, exactly as implemented; do not silently substitute a probability comparison in a compatibility-sensitive workflow.

The super-resolution network returns `x_` and uses `tf.layers.conv3d_transpose` with kernel sizes `2 * upsampling_factor`. The application workflow's low-resolution input is made by artificial downsampling. This is a demonstration/training setup, not a guarantee that arbitrary high-resolution detail can be inferred.
