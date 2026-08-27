# Troubleshooting: Modules and Networks

Use this guide when a Haiku model body fails before or during synthetic validation. For transform signatures, direct parameter/state/RNG calls, or JAX wrapper internals, route to the sibling sub-skill named in the fix.

## Shape, Layout, and Data-Format Mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Input to ConvND needs to have rank ...` | Missing batch/channel dimension or wrong spatial rank | For `Conv2D`, use `[H, W, C]` or `[B, H, W, C]` by default; for `Conv3D`, use `[D, H, W, C]` or `[B, D, H, W, C]`. |
| Convolution output shape is unexpected | Mixed `NHWC` and `NCHW`, stride/rate/padding confusion | Pick one layout and pass matching `data_format`. For NHWC, default `data_format="NHWC"` and pooling shapes like `(1, 2, 2, 1)`. |
| Bias broadcasts over wrong axes | `hk.Bias(bias_dims=...)` did not match intended dimensions | `bias_dims=None` biases all non-batch dims; `[]` is scalar; `[-1]` is final feature/channel bias. |
| Pooling changes channels or batch | `window_shape` / `strides` forgot batch/channel axes | Pooling shapes should match input rank; set size/stride `1` for batch and channel axes. |
| GroupNorm raises that channels are not divisible by groups | `groups` does not evenly split the channel dimension | Change group count or channel count; verify `data_format` so Haiku finds the intended channel axis. |
| LayerNorm asks for `param_axis` or creates odd parameter shapes | Normalization axis is not the final dimension | When `axis` is not `-1`, pass explicit `param_axis` for learnable scale/offset. |
| VectorQuantizer reshape error | Input final dimension does not equal `embedding_dim` | Set `embedding_dim=z.shape[-1]` or project inputs with `hk.Linear(embedding_dim)` first. |

Quick shape check:

```python
params = net.init(rng, synthetic_x, ...)
y = net.apply(params, rng_or_none, synthetic_x, ...)
assert y.shape == expected_shape
```

If `net.apply` argument order is uncertain, route to `core-transforms`.

## Stateful Layers Need a Stateful Transform

### Symptoms

- Error mentions `hk.transform_with_state`, mutable state, or dropping state.
- `BatchNorm` moving averages are missing or never update.
- `ResNet*` or `MobileNetV1(use_bn=True)` initializes but apply signatures do not match.
- `SpectralNorm`, `SNParamsTree`, `EMAParamsTree`, or `VectorQuantizerEMA` creates hidden state unexpectedly.

### Cause

Some modules call `hk.get_state` / `hk.set_state` internally. A stateless `hk.transform` cannot carry this state. The common stateful modules in this sub-skill are:

- `hk.BatchNorm`
- `hk.SpectralNorm` and `hk.SNParamsTree`
- `hk.EMAParamsTree`
- `hk.nets.VectorQuantizerEMA`
- Built-in networks that contain BatchNorm, including `hk.nets.ResNet*` and `hk.nets.MobileNetV1(use_bn=True)`

### Fix

Use `hk.transform_with_state` and carry both params and state:

```python
net = hk.transform_with_state(forward)
params, state = net.init(rng, x, is_training=True)
y, state = net.apply(params, state, rng, x, is_training=True)
y_eval, _ = net.apply(params, state, rng, x, is_training=False)
```

If the model does not truly need moving-average state, replace BatchNorm with a stateless normalizer:

```python
hk.LayerNorm(axis=-1, param_axis=-1, create_scale=True, create_offset=True)
hk.GroupNorm(groups=8, create_scale=True, create_offset=True)
hk.InstanceNorm(create_scale=True, create_offset=True)
hk.RMSNorm(axis=-1)
```

## `hk.Sequential` Argument Routing Problems

### Symptom

A chain containing `BatchNorm`, attention, masks, or custom layers fails with missing `is_training`, `mask`, or `rng` arguments.

### Cause

`hk.Sequential` forwards extra `*args` / `**kwargs` only to the first layer. Later layers receive only the previous output.

### Fix

Use an explicit forward function or `hk.Module`:

```python
def forward(x, is_training):
    x = hk.Conv2D(32, 3)(x)
    x = hk.BatchNorm(True, True, 0.9)(x, is_training)
    x = jax.nn.relu(x)
    return hk.Linear(10)(hk.Flatten()(x))
```

## Dropout and RNG Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Error says a non-`None` PRNGKey is required | Forward calls `hk.next_rng_key()` or `hk.dropout`, but apply was called with `rng=None` or wrapped with `without_apply_rng` | Pass an apply RNG, or remove dropout from the forward. Route exact transform wrapper mechanics to `core-transforms`. |
| `hk.nets.MLP` says an RNG key must be passed | `dropout_rate` was set but `rng` was omitted from `mlp(...)` | Call `mlp(x, dropout_rate=rate, rng=hk.next_rng_key())` inside the transformed function, or pass a direct key if already managing it. |
| `hk.nets.MLP` says RNG should only be passed with dropout | `rng` was passed while `dropout_rate=None` | Pass both `dropout_rate` and `rng`, or neither. |
| Dropout mask broadcasts over wrong axes | `broadcast_dims` mismatches input shape | Make each broadcast dimension valid for `x.ndim`; use broadcast dims only when intentionally sharing the mask. |

Direct use of `hk.next_rng_key`, `hk.PRNGSequence`, or apply-time RNG splitting belongs to `params-state-rng`.

## Attention and Transformer Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MultiHeadAttention` asks for a weight initializer | `w_init` was omitted | Pass `w_init=hk.initializers.VarianceScaling(...)` or another initializer. Do not combine `w_init` and legacy `w_init_scale`. |
| Mask dimensionality error | Mask rank differs from attention logits rank | For self-attention over `[B, T, D]`, use mask shape `[B, 1, T, T]` or broadcast-compatible equivalent with same rank. |
| Output feature size unexpected | `model_size` defaulted to `num_heads * value_size` | Pass `model_size=input_embedding_size` when residual-adding attention output back to input. |
| Apply with dropout fails | Transformer block calls `hk.dropout(hk.next_rng_key(), ...)` | Pass a valid apply RNG; do not use `hk.without_apply_rng` for stochastic transformer blocks. |

## RNN Shape and State Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| LSTM/GRU input rank error | Cell input is not rank 1 or rank 2 at one timestep | For unrolls, use input sequence `[T, B, F]` or `[B, T, F]`; each step then has `[B, F]`. |
| Output sequence axes swapped | Wrong `time_major` value | Use `time_major=True` for `[T, B, F]`; `False` for `[B, T, F]`. |
| State shape mismatch | `initial_state` used wrong batch size or state carried across incompatible batch shapes | Call `core.initial_state(batch_size)` from the same synthetic batch shape used for the unroll. |
| ResetCore broadcasting resets wrong elements | `should_reset` shape does not prefix state shape | Use `should_reset` shape `[B]` for batched state or a tree matching the state structure. |
| Compiled graph is too large | `static_unroll` used for long sequences | Use `dynamic_unroll` for scan-like loops. |

## Missing Example Dependencies

### Symptoms

- Import errors for `optax`, `tensorflow`, `tensorflow_datasets`, RL libraries, notebook tooling, or dataset packages.
- Training scripts attempt to download MNIST, ImageNet, language modeling data, or RL environments.
- Example setup wants broad optional requirements that are unrelated to model-body validation.

### Expected behavior

This sub-skill intentionally does not require full example dependencies. Use synthetic validation for Haiku model construction and shape checks. Add Optax, TFDS, TensorFlow, RL libraries, or dataset code only when the user's task explicitly needs training or data loading beyond Haiku model construction.

Safe fallback:

```bash
python sub-skills/modules-and-networks/scripts/haiku_mlp_smoke.py --batch-size 4 --input-size 32 --hidden-sizes 16 --num-classes 3
```

If this passes, Haiku model-body basics work; the missing dependency is outside this sub-skill's runtime contract.

## Full Downloads or Long Training Are Skipped

Full MNIST, VAE, ImageNet, transformer language-model, and IMPALA-style examples demonstrate useful Haiku patterns but can require downloads, TensorFlow/TFDS, Optax, RL environments, multiple devices, or long training. For this repo skill:

- Adapt the model body and validation shape checks.
- Do not treat full dataset training as required for Haiku API usability.
- Clearly separate Haiku model construction from optimizer, dataset, and infrastructure tasks.

When a user specifically asks to train one of these examples, first validate a tiny synthetic model, then ask for dataset/runtime constraints if they are missing.

## JAX Backend and Performance Expectations

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| First apply or jit is slow | JAX compilation overhead | Run a small warm-up; do not judge steady-state speed from the first compiled call. |
| CPU run is slow for large images/models | CPU JAX backend is being used | Install the JAX backend matching the user's accelerator if acceleration is required; Haiku itself delegates backend support to JAX. |
| GPU/TPU visible but not used | JAX/JAXLIB accelerator build is missing or incompatible | Verify `jax.default_backend()` and `jax.devices()` in the user's environment. This is an environment issue, not a Haiku layer API issue. |
| Out-of-memory with ResNet/MobileNet/attention | Model/input too large for backend memory | Reduce batch size, image size, sequence length, hidden size, or number of heads before changing Haiku APIs. |
| Channels-first model slower than expected | Backend/layout mismatch | Prefer default channels-last layouts unless the surrounding pipeline has a strong reason for channels-first. |

For Haiku-specific wrappers around `jax.vmap`, `jax.scan`, `jax.grad`, `jax.remat`, or `jax.pmap` interactions inside transformed functions, route to `jax-interop-and-advanced`.
