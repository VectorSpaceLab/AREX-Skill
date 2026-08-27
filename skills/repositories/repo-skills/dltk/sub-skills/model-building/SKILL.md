---
name: model-building
description: "Select and construct DLTK 0.2.1 TensorFlow 1.x 3D networks and
  core model-building blocks from explicit rank-5 tensor contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DLTK model building

Use this route when the task is to choose or instantiate a DLTK network, residual unit, activation, loss, metric, or 3D upsampling layer. This is an operating guide for the public DLTK 0.2.1 API; it assumes Python 3.7 with TensorFlow 1.15.0 and graph-mode APIs such as `tf.Session`, `tf.layers`, `tf.contrib`, and `tf.estimator`. Keep these legacy API calls unchanged unless a separate migration task is explicitly requested.

## Route the request

- **Classification or scalar regression:** `dltk.networks.regression_classification.resnet.resnet_3d`.
- **Dense multi-class segmentation:** `residual_unet_3d`, `asymmetric_residual_unet_3d`, or `residual_fcn_3d` from `dltk.networks.segmentation`; choose UNet for concatenated skip features, asymmetric UNet for one decoder residual unit per scale, and FCN for additive upscore skips.
- **Multi-scale segmentation experiment:** `deepmedic_3d`, only with an explicit WIP acceptance; this implementation warns that it is not accuracy-equivalent to the original DeepMedic and uses linear/bilinear-style upsampling rather than the original repeat upsampling.
- **Representation learning/reconstruction:** `convolutional_autoencoder_3d`.
- **GAN graph:** `dcgan_generator_3d` and `dcgan_discriminator_3d`; the network functions only construct the generator/discriminator dictionaries, not a complete training loop.
- **Resolution increase:** `simple_super_resolution_3d`; its transpose-convolution output is only meaningful when the input is an intentionally downsampled low-resolution view of a target, not as evidence that arbitrary full-resolution data can be recovered.
- **Reusable blocks:** `vanilla_residual_unit_3d`, `linear_upsample_3d`, `get_linear_upsampling_kernel`, `prelu`, `leaky_relu`, `dice_loss`, `sparse_balanced_crossentropy`, and NumPy metrics. See [api-reference.md](references/api-reference.md) and [model-overview.md](references/model-overview.md).

## Construct safely

1. Confirm a TensorFlow 1.x graph and a static rank-5 input `[batch, x, y, z, channels]`. Network functions assert rank 5; channel count must be statically known for residual padding/conversion, flattening, and transpose-convolution output shapes.
2. Set `num_classes`, `filters`, and `strides` deliberately. For ResNet, UNet, FCN, autoencoder, and both GAN functions, `len(filters)` must equal `len(strides)`. Each spatial stride is a 3-tuple. For a tiny graph, use all-one strides first; non-unit strides must leave compatible encoder/decoder spatial sizes and provide enough input extent for the chosen convolution/padding.
3. Pass `mode=mode` from the surrounding Estimator `model_fn`. Batch normalization uses `training=(mode == tf.estimator.ModeKeys.TRAIN)`; `TRAIN` therefore requires the caller to run `tf.GraphKeys.UPDATE_OPS` under control dependencies. The network itself does not create the optimizer or `EstimatorSpec`.
4. Treat the returned dictionary as the public handoff. Segmentation and ResNet return `logits`, `y_prob`, and `y_`; the autoencoder and super-resolution networks return `hidden_units`/`x_`; the GAN generator returns `gen`, while the discriminator returns `logits`, `probs`, and `pred`. Preserve these keys when wiring prediction/export code.
5. For a real training workflow, hand feature/label shape and Reader concerns to [data-pipelines](../data-pipelines/SKILL.md), and hand Estimator loss/optimizer/update-op/export orchestration to [training-and-estimators](../training-and-estimators/SKILL.md). Do not put file I/O or training loops in this route.
6. Run the bounded graph-only check when TensorFlow 1.15.0 is available:
   `python scripts/network_smoke.py --family all` from the `model-building/` sub-skill directory
   The check creates tiny graphs and executes one forward pass; it never downloads data, trains, exports, or writes checkpoints. `--help` is safe in any working directory.

## Loss and metric choices

- `dice_loss(logits, labels, num_classes, smooth=1e-5, include_background=True, only_present=False)` applies softmax internally and reduces Dice over batch/class spatial axes `[1, 2, 3]`; labels are sparse integer maps. `only_present=True` removes absent classes, and `include_background=False` removes class zero. It returns `1 - mean(Dice)`, not a per-class vector.
- `sparse_balanced_crossentropy(logits, labels)` expects sparse labels and inverse-frequency weights from the labels in the current tensor. A class absent from that tensor receives a stabilized weight; inspect batch composition before interpreting the value.
- `dltk.core.metrics.dice`, `abs_vol_difference`, and `crossentropy` are NumPy metrics. `dice` returns one value per class and may produce `NaN` for an absent class because its denominator is zero; `crossentropy` takes one-hot labels and interprets its first argument as logits unless `logits=False`.

## Guardrails

- A rank-4 image or a missing channel dimension is not a valid network input. Fix the Reader/example shape to `[B, X, Y, Z, C]`; do not reshape labels into a fake channel merely to bypass an assertion.
- A `len(filters) != len(strides)` error means the architecture schedule is malformed. A concat/add shape error means cumulative encoder strides, input spatial dimensions, or skip branch sizes do not match; first use all-one strides, then introduce one spatial factor at a time.
- `dcgan_discriminator_3d` compares `x > 0.5` on its **logit** tensor for `pred`; this is the package behavior, not a calibrated probability threshold. Use `probs` only when sigmoid probabilities are intended.
- `deepmedic_3d` is explicitly WIP and should not be presented as a reproduction of the original model or accuracy. Keep it out of routine smoke checks unless a task supplies compatible crop/pathway shapes.
- `simple_super_resolution_3d` performs learned transpose-convolution upsampling; the application workflow obtains a low-resolution input by artificial downsampling. It does not establish recovery of information absent from a genuinely low-resolution measurement.

For owned shape, mode, batch-normalization, output-key, and legacy-runtime failures, use [troubleshooting.md](references/troubleshooting.md). For complete verified signatures and family details, use [api-reference.md](references/api-reference.md) and [model-overview.md](references/model-overview.md).
