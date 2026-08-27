# Model Overview: Choosing Haiku Layers and Networks

Use this overview to pick a Haiku model body before digging into exact signatures in [api-reference.md](api-reference.md).

## First Questions

1. **What is the data shape?**
   - Tabular/features: `[B, F]` → dense MLP.
   - Images/features: `[B, H, W, C]` by default → convolutional blocks, pooling, ResNet/MobileNet.
   - Tokens: `[B, T]` → `hk.Embed`, positional parameters, attention or recurrent blocks.
   - Continuous sequences: `[T, B, F]` or `[B, T, F]` → recurrent cores or attention.
2. **Does the model need Haiku mutable state?**
   - Yes for BatchNorm moving averages, SpectralNorm state, and EMA vector quantization.
   - No for Linear, Conv, LayerNorm, GroupNorm, InstanceNorm, RMSNorm, Embed, MultiHeadAttention, and ordinary RNN hidden state.
3. **Can the model be a simple chain?**
   - Use `hk.Sequential` for simple one-input chains.
   - Use a function or `hk.Module` when later layers need `is_training`, masks, RNG, multiple inputs, residual connections, or returned auxiliary values.
4. **Can you validate without real data?**
   - Prefer synthetic arrays for shape, parameter, and state checks before adding datasets or training loops.

## Family Selection Guide

### Dense MLPs

Use `hk.nets.MLP` for standard feed-forward networks. It creates ordered `Linear` layers, applies an activation between layers, and optionally applies dropout when given both `dropout_rate` and `rng`.

Use `hk.Sequential` when you want explicit layers:

```python
def forward(x):
    x = hk.Flatten()(x)
    net = hk.Sequential([
        hk.Linear(300), jax.nn.relu,
        hk.Linear(100), jax.nn.relu,
        hk.Linear(10),
    ])
    return net(x)
```

Prefer this family for supervised classification/regression, small synthetic validation, and heads on top of convolutional or sequence encoders.

### Convolutional Models

Use `hk.Conv2D` for images unless the data is 1D or 3D. Haiku defaults to channels-last layouts (`NWC`, `NHWC`, `NDHWC`), matching most JAX image examples. Use channels-first only when input arrays and downstream operations are consistently laid out that way.

Common block:

```python
def conv_block(x, is_training):
    x = hk.Conv2D(32, kernel_shape=3, stride=1, padding="SAME")(x)
    x = hk.BatchNorm(True, True, decay_rate=0.9)(x, is_training)
    return jax.nn.relu(x)
```

If BatchNorm state is inconvenient or batch size is small, replace it with `LayerNorm`, `GroupNorm`, `InstanceNorm`, or `RMSNorm` depending on the shape and desired axes.

### Normalization Choice

| Situation | Prefer | Why |
| --- | --- | --- |
| Large image training with train/eval phases | `hk.BatchNorm` | Tracks moving averages and supports cross-replica statistics. |
| Tiny batch, sequence, transformer, or simple smoke | `hk.LayerNorm` | Stateless and stable across batch sizes. |
| Convolutional model where channels can be split into groups | `hk.GroupNorm` | Stateless alternative to BatchNorm; batch-size independent. |
| Per-instance image normalization over spatial axes | `hk.InstanceNorm` | Stateless spatial normalization. |
| Transformer-like models where mean recentering is unwanted | `hk.RMSNorm` | Stateless RMS-only normalization. |
| Weight or parameter-tree spectral constraints | `hk.SpectralNorm` / `hk.SNParamsTree` | Uses state for power iteration; requires stateful transform. |

Difficult usability decision: if a user asks for “normalization” but does not require batch moving averages, start with a stateless norm. Choose `BatchNorm` only when the task explicitly needs train/eval batch statistics or a built-in network uses it.

### Built-in Image Backbones

Use `hk.nets.ResNet50(num_classes, bn_config=...)` or other `ResNet*` variants for ImageNet-style classification bodies. These networks call BatchNorm internally and require `is_training` at apply time.

Use `hk.nets.MobileNetV1(num_classes=..., use_bn=True)` for a smaller depthwise-separable image model. `use_bn=True` is stateful; `use_bn=False` avoids BatchNorm but changes bias behavior and model quality assumptions.

Typical wrapper:

```python
def forward(images, is_training):
    net = hk.nets.ResNet50(num_classes=1000, bn_config={"decay_rate": 0.9})
    return net(images, is_training=is_training)
```

### Recurrent Models

Use `hk.LSTM`, `hk.GRU`, or `hk.VanillaRNN` when the model must maintain explicit sequence state. RNN state is not Haiku mutable state; it is an input/output of the recurrent core.

```python
def forward(xs):  # xs: [T, B, F]
    core = hk.LSTM(hidden_size=32)
    initial = core.initial_state(batch_size=xs.shape[1])
    outputs, final_state = hk.dynamic_unroll(core, xs, initial)
    return outputs, final_state
```

Use `dynamic_unroll` for scan-like loops and `static_unroll` only for short fixed sequences where unrolling the loop in the compiled program is acceptable.

### Attention and Transformers

Use `hk.Embed` for token IDs, learned positional parameters for position embeddings, `hk.MultiHeadAttention` for self/cross attention, `hk.LayerNorm` or `hk.RMSNorm` for stateless normalization, and `hk.dropout` for stochastic regularization.

Attention shape rule: `query` is `[..., T_query, D]`; `key` and `value` are `[..., T_key, D]`; mask rank must match attention logits and is commonly shaped `[B, 1, T_query, T_key]`.

Transformer block pattern:

```python
initializer = hk.initializers.VarianceScaling(2.0 / num_layers)
attn = hk.MultiHeadAttention(num_heads=4, key_size=32,
                             model_size=x.shape[-1], w_init=initializer)
h = hk.LayerNorm(axis=-1, create_scale=True, create_offset=True)(x)
h = attn(h, h, h, mask=mask)
h = hk.dropout(hk.next_rng_key(), dropout_rate, h)
x = x + h
```

Direct `hk.next_rng_key()` details belong to `params-state-rng`; JAX transform wrappers around attention blocks belong to `jax-interop-and-advanced`.

### VAE and VQ-VAE Patterns

For a VAE encoder/decoder, compose `hk.Flatten`, `hk.Linear`, `jax.nn.relu`, and output heads for mean/log-scale. Sampling uses `hk.next_rng_key()` inside a transformed apply, so route RNG troubleshooting to `params-state-rng`.

For VQ-VAE, use `hk.nets.VectorQuantizer` for a stateless quantizer with an auxiliary loss, or `hk.nets.VectorQuantizerEMA` for EMA-updated embeddings. The final input dimension must equal `embedding_dim`; the module returns a dictionary with quantized outputs and losses.

### IMPALA-Style and RL Model Bodies

IMPALA-style models in Haiku are ordinary model bodies combining convolutions, residual stacks, MLP heads, and sometimes recurrent cores. Treat environment loops, replay, RL losses, and dependencies as external. Keep the Haiku-specific part focused on:

- Input preprocessing and channel layout.
- Convolutional/residual torso.
- Optional RNN core with explicit state.
- Policy/value heads from `hk.Linear` or `hk.nets.MLP`.
- Synthetic shape validation before connecting an RL environment.

## Safe No-Download Validation Pattern

For any model family, create a minimal transformed function, initialize it on zeros or deterministic synthetic arrays, apply once, and assert:

- Output shape exactly matches the intended task shape.
- Parameter tree contains expected modules and non-empty leaves.
- State tree is empty for stateless models, or contains expected BatchNorm/EMA/SpectralNorm state for stateful models.
- Apply-time RNG is supplied only when the forward pass uses dropout or `hk.next_rng_key()`.

The bundled [synthetic MLP smoke script](../scripts/haiku_mlp_smoke.py) demonstrates this pattern without downloads or optimizer dependencies.
