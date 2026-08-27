# API Reference: Haiku Modules and Networks

This reference summarizes the Haiku public APIs most useful for model bodies. It assumes `import haiku as hk`, `import jax`, and `import jax.numpy as jnp`.

## Quick Decision Table

| Need | Prefer | State required? | Notes |
| --- | --- | --- | --- |
| Dense classifier/regressor | `hk.nets.MLP` or `hk.Sequential([hk.Linear, activation, ...])` | No, unless adding stateful layers | Use `hk.nets.MLP` for standard dense stacks; use `hk.Sequential` only when all layers form a simple chain. |
| Custom block with `is_training`, mask, or multiple inputs | A forward function or `hk.Module` subclass | Depends on layers | Avoid `hk.Sequential` when non-first layers need extra arguments. |
| Image/feature maps | `hk.Conv1D/2D/3D`, pooling, `hk.Flatten`, `hk.Linear` | No, unless normalization is stateful | Default image layout is channels-last (`NWC`, `NHWC`, `NDHWC`). |
| Batch statistics during training/eval | `hk.BatchNorm` | Yes | Requires `hk.transform_with_state`; carry state in and out of apply. |
| Per-example or per-token normalization | `hk.LayerNorm`, `hk.GroupNorm`, `hk.InstanceNorm`, `hk.RMSNorm` | No | Safer for small batches, sequence models, and no-state transforms. |
| Sequence recurrence | `hk.LSTM`, `hk.GRU`, `hk.dynamic_unroll` | No module state; explicit RNN state | RNN hidden/cell state is an argument/result, not Haiku mutable state. |
| Transformer attention | `hk.MultiHeadAttention`, `hk.Embed`, `hk.LayerNorm`, `hk.dropout` | No unless adding stateful layers | `MultiHeadAttention` needs an explicit weight initializer. Dropout needs RNG. |
| Full image backbone | `hk.nets.ResNet*`, `hk.nets.MobileNetV1` | Usually yes | Their BatchNorm layers require state and `is_training`. |
| VQ-VAE quantization | `hk.nets.VectorQuantizer` or `VectorQuantizerEMA` | EMA variant requires state | Inputs' final dimension must equal `embedding_dim`. |

## Dense, Bias, Dropout, and Simple Combinators

### `hk.Linear`

Constructor shape:

```python
hk.Linear(output_size, with_bias=True, w_init=None, b_init=None, name=None)
```

Call shape: input must have at least one dimension; the last input dimension is the feature dimension. Output shape is `inputs.shape[:-1] + (output_size,)`. Parameters are `w` with shape `[input_size, output_size]` and, when `with_bias=True`, `b` with shape `[output_size]` broadcast to the output.

Use `precision=` at call time only when you need to pass a JAX dot precision. Scalars are invalid inputs.

### `hk.nets.MLP`

Constructor shape:

```python
hk.nets.MLP(output_sizes, w_init=None, b_init=None, with_bias=True,
            activation=jax.nn.relu, activate_final=False, name=None)
```

Call shape:

```python
mlp(inputs, dropout_rate=None, rng=None)
```

- Creates one `hk.Linear` per entry in `output_sizes`, named `linear_0`, `linear_1`, and so on.
- Activates every hidden layer; activate the final layer only with `activate_final=True`.
- If `dropout_rate` is set, pass `rng`; if `dropout_rate` is `None`, do not pass `rng`.
- `b_init` must be `None` when `with_bias=False`.
- `reverse()` is available after the MLP has been called once, because input sizes must be known.

### `hk.Sequential`

Constructor shape:

```python
hk.Sequential(layers, name=None)
```

Use it for a chain where output of each layer becomes input to the next. Extra `*args` and `**kwargs` are forwarded only to the first layer. This is why `Sequential` is a poor fit for a chain containing `BatchNorm(is_training=...)` after the first layer, attention masks, or multiple inputs.

Good:

```python
net = hk.Sequential([hk.Flatten(), hk.Linear(300), jax.nn.relu, hk.Linear(10)])
logits = net(images)
```

Use a custom forward function instead when later layers need control flags:

```python
def forward(x, is_training):
    x = hk.Conv2D(32, 3)(x)
    x = hk.BatchNorm(True, True, 0.9)(x, is_training=is_training)
    return jax.nn.relu(x)
```

### `hk.dropout`

Signature:

```python
hk.dropout(rng, rate, x, broadcast_dims=())
```

- `rate` must be in `[0, 1)` and output is scaled by `1 / (1 - rate)`.
- Use `broadcast_dims` to share a mask along dimensions, for example along a time or spatial axis.
- Inside a transformed function, the common pattern is `hk.dropout(hk.next_rng_key(), rate, x)`. Direct RNG sequence mechanics are covered by `params-state-rng`.
- Dropout is an apply-time stochastic operation, so applying with `rng=None` will fail if the forward pass calls `hk.next_rng_key()`.

### `hk.Bias`

Constructor shape:

```python
hk.Bias(output_size=None, bias_dims=None, b_init=None, name=None)
```

Adds a learned bias broadcast over input dimensions. Inputs must include a leading batch dimension. `bias_dims=None` creates a bias over all non-batch dimensions; `bias_dims=[]` creates a scalar bias; `bias_dims=[-1]` creates a channel/feature bias. The optional `multiplier` argument can add or subtract the same learned bias.

### `hk.one_hot` and `hk.multinomial`

These compatibility helpers exist but are deprecated in favor of JAX APIs:

```python
hk.one_hot(x, num_classes, dtype=jnp.float32)       # prefer jax.nn.one_hot
hk.multinomial(rng, logits, num_samples)           # prefer jax.random.categorical
```

`hk.one_hot` returns shape `x.shape + (num_classes,)`. `hk.multinomial` samples categories from logits whose last dimension is classes and returns `logits.shape[:-1] + (num_samples,)`.

## Shape Helpers and Pooling

| API | Use | Key shape notes |
| --- | --- | --- |
| `hk.Flatten(preserve_dims=1)` | Flatten non-leading dimensions before dense layers | Default preserves the batch dimension; negative `preserve_dims` can flatten trailing element dimensions for batched/unbatched reuse. |
| `hk.Reshape(output_shape, preserve_dims=1)` | Reshape while preserving leading dimensions | `-1` can appear once in `output_shape`; `preserve_dims=0` is invalid. |
| `hk.avg_pool(value, window_shape, strides, padding, channel_axis=-1)` | Functional average pooling | `window_shape` and `strides` are expanded to input rank; channel axis is skipped. |
| `hk.max_pool(value, window_shape, strides, padding, channel_axis=-1)` | Functional max pooling | `padding` must be `"SAME"` or `"VALID"`. |
| `hk.AvgPool(...)`, `hk.MaxPool(...)` | Module wrappers around pooling | Store pooling settings and call on a value. |

For NHWC images, include batch and channel axes in pooling shapes, e.g. `window_shape=(1, 2, 2, 1)`, `strides=(1, 2, 2, 1)`, `channel_axis=-1`.

## Convolutions

| API | Default layout | Typical input rank | Output-channel argument | Notes |
| --- | --- | --- | --- | --- |
| `hk.Conv1D` | `NWC` | unbatched `[W, C]` or batched `[N, W, C]` | `output_channels` | `kernel_shape`, `stride`, and `rate` may be int or length-1 sequence. |
| `hk.Conv2D` | `NHWC` | unbatched `[H, W, C]` or batched `[N, H, W, C]` | `output_channels` | Common image convolution. |
| `hk.Conv3D` | `NDHWC` | unbatched `[D, H, W, C]` or batched `[N, D, H, W, C]` | `output_channels` | Volumetric convolution. |
| `hk.ConvND` | `channels_last` | unbatched rank `num_spatial_dims + 1` or batched rank `num_spatial_dims + 2` | `output_channels` | General form; pass `num_spatial_dims`. |
| `hk.Conv1DTranspose/2DTranspose/3DTranspose` | matching channels-last layouts | same rank convention as non-transposed | `output_channels` | Use `output_shape` only for spatial dimensions; padding must be `SAME` or `VALID` when output shape is explicit. |
| `hk.ConvNDTranspose` | `channels_last` | general transposed convolution | `output_channels` | General transposed form. |
| `hk.DepthwiseConv1D/2D/3D` | `NWC`, `NHWC`, `NDHWC` | batched feature maps | `channel_multiplier` | Output channels are input channels times `channel_multiplier`. |

Constructor pattern for normal convolutions:

```python
hk.Conv2D(output_channels, kernel_shape, stride=1, rate=1, padding="SAME",
          with_bias=True, w_init=None, b_init=None, data_format="NHWC",
          mask=None, feature_group_count=1, name=None)
```

Important rules:

- `padding` can be `"SAME"`, `"VALID"`, explicit `(low, high)` pairs per spatial dimension, or compatible padding callables for non-transposed convolutions.
- `feature_group_count > 1` performs grouped convolution; input channels must be divisible by the group count.
- A `mask` must match the computed weight shape exactly.
- For `channels_first` / `NC...` data, bias parameters are shaped for channel-first broadcasting.
- If the input rank is one less than the batched rank, Haiku treats it as unbatched, temporarily adds a batch axis, and squeezes it at the end.

## Normalization

| API | Constructor core | Call core | Haiku mutable state? | Prefer when |
| --- | --- | --- | --- | --- |
| `hk.BatchNorm` | `create_scale`, `create_offset`, `decay_rate`, `eps=1e-5`, `axis=None`, `cross_replica_axis=None`, `data_format="channels_last"` | `(inputs, is_training, test_local_stats=False, scale=None, offset=None)` | Yes: moving averages | You need training/eval batch statistics, ResNet/MobileNet-style image models, or cross-replica stats. |
| `hk.LayerNorm` | `axis`, `create_scale`, `create_offset`, `eps=1e-5`, `param_axis=None` | `(inputs, scale=None, offset=None)` | No | Transformers, MLPs, sequence models, small batches. |
| `hk.GroupNorm` | `groups`, `axis=slice(1, None)`, `create_scale=True`, `create_offset=True`, `data_format="channels_last"` | `(x, scale=None, offset=None)` | No | Convolutional models when batch statistics are undesirable. Channels must divide by groups. |
| `hk.InstanceNorm` | `create_scale`, `create_offset`, `eps=1e-5`, `data_format="channels_last"` | `(inputs, scale=None, offset=None)` | No | Normalize spatial dimensions per instance. |
| `hk.RMSNorm` | `axis`, `eps=1e-5`, `create_scale=True`, `param_axis=None` | `(inputs)` | No | Transformer-like models where recentering is not desired. |
| `hk.SpectralNorm` | `eps=1e-4`, `n_steps=1` | `(value, update_stats=True, error_on_non_matrix=False)` | Yes: power-iteration vectors/statistics | Normalize weights/arrays by approximate top singular value. |

Scale/offset convention: if `create_scale=True` or `create_offset=True`, Haiku owns the parameter and you must not pass external `scale` or `offset` at call time. If creation is disabled, you may pass external values or accept scalar defaults.

State decision: use `hk.transform_with_state` for any model body containing `BatchNorm`, `SpectralNorm`, `SNParamsTree`, `EMAParamsTree`, or `VectorQuantizerEMA`. Stateless normalization can use `hk.transform`.

## Embedding and Attention

### `hk.Embed`

Constructor:

```python
hk.Embed(vocab_size=None, embed_dim=None, embedding_matrix=None, w_init=None,
         lookup_style="ARRAY_INDEX", name=None, precision=jax.lax.Precision.HIGHEST)
```

Call:

```python
embeddings = embed(ids, lookup_style=None, precision=None)
```

- Pass integer `ids`; output shape is `ids.shape + (embed_dim,)`.
- Provide either `vocab_size` with `embed_dim`, or an `embedding_matrix` shaped `[vocab_size, embed_dim]`.
- Lookup style `ARRAY_INDEX` is generally the default; `ONE_HOT` can be useful for small vocabularies on some accelerators.

### `hk.MultiHeadAttention`

Constructor:

```python
hk.MultiHeadAttention(num_heads, key_size, w_init_scale=None, *, w_init=None,
                      with_bias=True, b_init=None, value_size=None,
                      model_size=None, name=None)
```

Call:

```python
out = mha(query, key, value, mask=None)
```

Shape glossary: `T` is key/value length, `T'` is query length, `D` is embedding size, and `H` is number of heads.

- `query`: `[..., T', D_q]`; `key`: `[..., T, D_k]`; `value`: `[..., T, D_v]`.
- Optional `mask`: `[..., H_or_1, T', T]` and must have the same rank as the attention logits.
- Return shape: `[..., T', model_size]`; default `model_size = num_heads * value_size` and default `value_size = key_size`.
- Provide explicit `w_init`; legacy `w_init_scale` exists but is deprecated and cannot be combined with `w_init`.

## Recurrent Modules

| API | Use | Shape/state notes |
| --- | --- | --- |
| `hk.RNNCore` | Base protocol | Implement `__call__(inputs, prev_state) -> (output, next_state)` and `initial_state(batch_size)`. |
| `hk.VanillaRNN(hidden_size)` | Basic ReLU RNN | State/output shape is hidden size, with optional batch dimension. |
| `hk.LSTM(hidden_size)` | LSTM | State is `hk.LSTMState(hidden, cell)`. Inputs must be rank 1 or 2. |
| `hk.GRU(hidden_size, ...)` | GRU | Inputs must be rank 1 or 2. |
| `hk.DeepRNN(layers)` | Stack cores and callables | State is one element per `RNNCore`; callables have no recurrent state. |
| `hk.deep_rnn_with_skip_connections(layers)` | Stack RNN cores with skip connections | All layers must be `RNNCore` instances. |
| `hk.ResetCore(core)` | Per-batch timestep resets | Inputs are `(inputs, should_reset)`. Reset shapes must prefix state shapes. |
| `hk.IdentityCore()` | Feedforward/recurrent interface compatibility | Forwards inputs and has empty state. |
| `hk.Conv1DLSTM/2DLSTM/3DLSTM` | Convolutional recurrent models | Constructor includes `input_shape`, `output_channels`, and `kernel_shape`. |
| `hk.static_unroll(core, input_sequence, initial_state, time_major=True)` | Python/static unroll | Useful for small fixed sequence lengths; can increase compiled graph size. |
| `hk.dynamic_unroll(core, input_sequence, initial_state, time_major=True, reverse=False, return_all_states=False, unroll=1)` | Scan/dynamic unroll | Preserves loop structure; inside Haiku transform it uses Haiku's scan wrapper. |

Input sequence shapes: with `time_major=True`, arrays are `[T, ...]`; with `time_major=False`, arrays are `[B, T, ...]`. For batched RNN state, call `core.initial_state(batch_size)`.

## Built-in Network Families

| API | Constructor highlights | Call shape/state | Notes |
| --- | --- | --- | --- |
| `hk.nets.MLP` | `output_sizes`, optional initializers, activation, `activate_final` | `mlp(inputs, dropout_rate=None, rng=None)`; stateless | Standard dense stack. See dense section. |
| `hk.nets.ResNet` | `blocks_per_group`, `num_classes`, `bn_config`, `resnet_v2`, `bottleneck`, channel/projection/stride configs | `net(images, is_training, test_local_stats=False)`; stateful because BatchNorm | Base configurable ResNet. Constructor validates group lengths. |
| `hk.nets.ResNet18/34/50/101/152/200` | `num_classes`, `bn_config=None`, `resnet_v2=False`, optional logits/initial conv config and strides | same as `ResNet`; stateful | Preset block configurations. `ResNet50` is the common ImageNet-style choice. |
| `hk.nets.MobileNetV1` | `strides`, `channels`, `num_classes=1000`, `use_bn=True` | `net(images, is_training)`; stateful when `use_bn=True` | Uses depthwise separable blocks; `strides` and `channels` lengths must match. |
| `hk.nets.VectorQuantizer` | `embedding_dim`, `num_embeddings`, `commitment_cost`, `dtype`, `cross_replica_axis=None` | `vq(inputs, is_training)`; stateless | Returns dict with `quantize`, `loss`, `perplexity`, `encodings`, `encoding_indices`, `distances`. |
| `hk.nets.VectorQuantizerEMA` | same plus `decay`, `epsilon` | `vq_ema(inputs, is_training)`; stateful | Uses exponential moving averages for embeddings, so state must be carried. |

Vector quantizer input rule: the final input dimension must equal `embedding_dim`; all leading dimensions are flattened for quantization and restored afterward.
