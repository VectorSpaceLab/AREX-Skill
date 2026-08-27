# Layers and Nets API Reference

## Dense and shape modules

- `snt.Linear(output_size, with_bias=True, w_init=None, b_init=None, name=None)`: maps `[..., input_size]` to `[..., output_size]`. Final input dimension must be known on first call.
- `snt.Bias(bias_dims=None, b_init=None)`: adds trainable bias over selected trailing dimensions.
- `snt.Flatten()`, `snt.Reshape(output_shape)`: TensorFlow reshape modules with Sonnet variable/submodule tracking.
- `snt.Embed(vocab_size, embed_dim, existing_vocab=None)`: integer ids to embedding vectors.

## Convolutions

- `snt.Conv1D/2D/3D(output_channels, kernel_shape, stride=1, rate=1, padding='SAME', with_bias=True, data_format='NHWC')`.
- `snt.Conv1DTranspose/2DTranspose/3DTranspose(...)` for transpose convolutions.
- `snt.DepthwiseConv2D(channel_multiplier, kernel_shape, stride=1, rate=1, padding='SAME')`.

Check data format and channel dimension. Unknown channels at first call cause variable-shape failures.

## Normalization and stateful modules

- `snt.BatchNorm(create_scale=True, create_offset=True, decay_rate=0.999, data_format='channels_last')` requires `is_training` on call and owns moving mean/variance.
- `snt.LayerNorm(axis, create_scale=True, create_offset=True)` and `snt.GroupNorm(groups, axis, create_scale=True, create_offset=True)` normalize current inputs without BatchNorm moving-average semantics.
- `snt.Dropout(rate)` must be called with `is_training` and is typically used inside an explicit module.

## Nets

- `snt.nets.MLP(output_sizes, activate_final=False, activation=tf.nn.relu, dropout_rate=None)` outputs `[..., output_sizes[-1]]`.
- `snt.nets.ResNet`, `ResNet18`, `ResNet34`, `ResNet50`, `ResNet101`, `ResNet152`, and `Cifar10ConvNet` provide image-model building blocks.
- `snt.nets.VectorQuantizer`, `VectorQuantizerEMA`, and `ResidualStack` support VQ-VAE-style workflows.
