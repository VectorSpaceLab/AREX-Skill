# Training workflow

`provider.FrustumDataset` reads generated pickle files, samples `num_point`
points, rotates frustums to center, and supplies segmentation labels, centers,
heading class/residuals, size class/residuals, rotation angles, and a three-way
one-hot object vector. The default training path uses augmented train data and
validation data without random augmentation.

The graph creates model placeholders, segmentation and box losses, IoU metrics,
learning-rate/BN decay, an Adam or Momentum optimizer, and a TensorFlow saver.
Training evaluates each epoch and saves a checkpoint every ten epochs. A
restore path must be a checkpoint prefix, not an arbitrary directory.

For v1, TensorFlow operators are ordinary graph ops and CPU soft placement may
be useful for a bounded smoke. For v2, `pointnet_util` imports the custom
sampling/grouping/interpolation libraries; treat missing `.so` files or CUDA
errors as a setup block. Do not start a full run merely to discover this.

A safe smoke plan uses a tiny copied fixture, one batch, a new temporary log
directory, and an explicit stop condition. It does not claim convergence or
benchmark accuracy. Full training is long-running, data-heavy, and hardware-
dependent; native execution was intentionally not used as final skill proof.
