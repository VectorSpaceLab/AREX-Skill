# Workflows: Building and Validating Haiku Models

These workflows are distilled for future use without relying on source examples, notebooks, dataset downloads, or training scripts.

## Workflow 1: Validate a Tiny MLP Without Downloads

Use this when the user needs a quick proof that Haiku/JAX imports, `hk.nets.MLP` or `hk.Sequential`, `hk.transform`, init/apply, and parameter creation work.

Run the bundled script from the generated skill tree:

```bash
python sub-skills/modules-and-networks/scripts/haiku_mlp_smoke.py \
  --batch-size 8 \
  --input-size 784 \
  --hidden-sizes 300,100 \
  --num-classes 10
```

Expected signal:

- Prints a JSON summary containing `logits_shape`, `param_leaf_count`, module names, and JAX backend.
- Asserts logits shape `[batch_size, num_classes]`.
- Asserts at least one parameter leaf was created and all parameter leaves are non-empty.

Manual equivalent:

```python
def forward(x):
    x = x.astype(jnp.float32)
    return hk.nets.MLP([300, 100, 10], name="classifier")(x)

net = hk.without_apply_rng(hk.transform(forward))
x = jnp.ones([8, 784], jnp.float32)
params = net.init(jax.random.PRNGKey(0), x)
logits = net.apply(params, x)
assert logits.shape == (8, 10)
assert jax.tree_util.tree_leaves(params)
```

If this fails because `hk.transform`, apply RNG position, or `without_apply_rng` is confusing, route to `core-transforms`.

## Workflow 2: Choose BatchNorm State vs Stateless Normalization

Use this when a model must normalize activations.

Decision procedure:

1. Ask whether the layer must maintain train/eval moving averages.
2. If yes, use `hk.BatchNorm` and a stateful transform.
3. If no, use `LayerNorm`, `GroupNorm`, `InstanceNorm`, or `RMSNorm` and keep the model stateless.
4. If using a built-in `ResNet*` or `MobileNetV1(use_bn=True)`, treat it as BatchNorm/stateful even if the user did not mention BatchNorm explicitly.

Stateful BatchNorm pattern:

```python
def forward(x, is_training):
    x = hk.Conv2D(16, kernel_shape=3, padding="SAME", with_bias=False)(x)
    x = hk.BatchNorm(create_scale=True, create_offset=True, decay_rate=0.9)(
        x, is_training=is_training)
    return jax.nn.relu(x)

net = hk.transform_with_state(forward)
rng = jax.random.PRNGKey(0)
x = jnp.ones([4, 8, 8, 3])
params, state = net.init(rng, x, is_training=True)
y, state = net.apply(params, state, rng, x, is_training=True)
y_eval, _ = net.apply(params, state, rng, x, is_training=False)
assert y.shape == y_eval.shape == (4, 8, 8, 16)
```

Stateless LayerNorm replacement:

```python
def forward(x):
    x = hk.Conv2D(16, kernel_shape=3, padding="SAME")(x)
    x = hk.LayerNorm(axis=-1, param_axis=-1,
                     create_scale=True, create_offset=True)(x)
    return jax.nn.relu(x)

net = hk.without_apply_rng(hk.transform(forward))
```

Do not put `BatchNorm` as a later layer in `hk.Sequential` if it needs `is_training`; only the first `Sequential` layer receives extra call arguments.

## Workflow 3: MLP Classifier Pattern From Images or Features

Use this for image-like input where a simple MLP is enough or for fast validation before a larger CNN.

```python
def classifier(images):
    x = images.astype(jnp.float32)
    if x.ndim > 2:
        x = hk.Flatten()(x)
    return hk.Sequential([
        hk.Linear(300), jax.nn.relu,
        hk.Linear(100), jax.nn.relu,
        hk.Linear(num_classes),
    ])(x)
```

Training-loop pieces such as Optax, TFDS, TensorFlow, checkpointing, and real metrics are outside this sub-skill. The Haiku body can be validated entirely with synthetic arrays.

## Workflow 4: ResNet or MobileNet Body With Safe Synthetic Input

Use this when the user wants an image backbone. These bodies usually require state because they contain BatchNorm.

```python
def forward(images, is_training):
    model = hk.nets.ResNet50(
        num_classes=1000,
        bn_config={"decay_rate": 0.9, "eps": 1e-5},
    )
    return model(images, is_training=is_training)

net = hk.transform_with_state(forward)
images = jnp.ones([2, 64, 64, 3], jnp.float32)
params, state = net.init(jax.random.PRNGKey(0), images, is_training=True)
logits, state = net.apply(params, state, None, images, is_training=True)
assert logits.shape == (2, 1000)
```

For a smaller model:

```python
def forward(images, is_training):
    return hk.nets.MobileNetV1(num_classes=10, use_bn=True)(images, is_training)
```

If the user asks for full ImageNet training, distributed data loading, or mixed precision, document that these are large external workflows. This sub-skill supplies the Haiku model-body pattern and state expectations, not a full data pipeline.

## Workflow 5: RNN With Explicit Sequence State

Use this when the task has ordered sequences and needs an LSTM/GRU state.

```python
def forward(xs):  # [T, B, F]
    core = hk.LSTM(hidden_size=32)
    initial_state = core.initial_state(batch_size=xs.shape[1])
    outputs, final_state = hk.dynamic_unroll(
        core, xs, initial_state, time_major=True)
    return outputs, final_state

net = hk.transform(forward)
xs = jnp.ones([5, 3, 7], jnp.float32)
params = net.init(jax.random.PRNGKey(0), xs)
outputs, final_state = net.apply(params, None, xs)
assert outputs.shape == (5, 3, 32)
assert final_state.hidden.shape == (3, 32)
```

Use `time_major=False` for `[B, T, F]` inputs. Use `static_unroll` for short fixed sequences when compile-size expansion is acceptable; otherwise use `dynamic_unroll`.

## Workflow 6: Transformer Block With Attention, Embed, Dropout

Use this for token models or attention blocks. This recipe is self-contained and uses synthetic token IDs.

```python
def forward(tokens, dropout_rate):  # tokens: [B, T]
    vocab_size = 128
    model_size = 32
    num_heads = 4
    key_size = 8

    embed_init = hk.initializers.TruncatedNormal(stddev=0.02)
    token_embed = hk.Embed(vocab_size, embed_dim=model_size, w_init=embed_init)
    x = token_embed(tokens)

    seq_len = tokens.shape[1]
    pos = hk.get_parameter("positional_embeddings", [seq_len, model_size],
                           init=embed_init)
    x = x + pos

    mask = tokens != 0
    mask = mask[:, None, None, :] * jnp.tril(jnp.ones([1, 1, seq_len, seq_len]))

    initializer = hk.initializers.VarianceScaling(1.0)
    h = hk.LayerNorm(axis=-1, create_scale=True, create_offset=True)(x)
    h = hk.MultiHeadAttention(num_heads=num_heads, key_size=key_size,
                              model_size=model_size, w_init=initializer)(
        h, h, h, mask=mask)
    h = hk.dropout(hk.next_rng_key(), dropout_rate, h)
    x = x + h

    h = hk.LayerNorm(axis=-1, create_scale=True, create_offset=True)(x)
    h = hk.Sequential([
        hk.Linear(4 * model_size), jax.nn.gelu,
        hk.Linear(model_size),
    ])(h)
    h = hk.dropout(hk.next_rng_key(), dropout_rate, h)
    return hk.Linear(vocab_size)(x + h)

net = hk.transform(forward)
tokens = jnp.ones([2, 6], jnp.int32)
params = net.init(jax.random.PRNGKey(0), tokens, 0.1)
logits = net.apply(params, jax.random.PRNGKey(1), tokens, 0.1)
assert logits.shape == (2, 6, 128)
```

Troubleshoot attention with these checks:

- `w_init` must be explicit for `MultiHeadAttention`.
- Mask rank must match attention logits rank; `[B, 1, T, T]` is usually safe for self-attention.
- Apply must receive an RNG if the block calls `hk.dropout(hk.next_rng_key(), ...)`.

## Workflow 7: VAE and VQ-VAE Model Bodies

VAE body sketch:

```python
class Encoder(hk.Module):
    def __init__(self, latent_size, hidden_size=512):
        super().__init__()
        self.latent_size = latent_size
        self.hidden_size = hidden_size

    def __call__(self, x):
        x = hk.Flatten()(x)
        x = jax.nn.relu(hk.Linear(self.hidden_size)(x))
        return hk.Linear(self.latent_size)(x), hk.Linear(self.latent_size)(x)

class Decoder(hk.Module):
    def __init__(self, output_shape, hidden_size=512):
        super().__init__()
        self.output_shape = tuple(output_shape)
        self.hidden_size = hidden_size

    def __call__(self, z):
        z = jax.nn.relu(hk.Linear(self.hidden_size)(z))
        logits = hk.Linear(int(np.prod(self.output_shape)))(z)
        return jnp.reshape(logits, (-1, *self.output_shape))
```

Sampling uses `hk.next_rng_key()` and should be handled as an apply-time stochastic model. Route RNG sequence failures to `params-state-rng`.

VQ-VAE quantizer body:

```python
def forward(z_e):
    vq = hk.nets.VectorQuantizer(
        embedding_dim=z_e.shape[-1], num_embeddings=64, commitment_cost=0.25)
    out = vq(z_e, is_training=True)
    return out["quantize"], out["loss"], out["perplexity"]
```

Use `VectorQuantizerEMA` only with a stateful transform because it tracks EMA statistics.

## Workflow 8: IMPALA-Style Model Body Without RL Dependencies

Use this only for the Haiku network part of an RL task:

```python
def torso(obs):
    x = obs.astype(jnp.float32) / 255.0
    for channels in (16, 32, 32):
        x = hk.Conv2D(channels, 3, stride=1, padding="SAME")(x)
        x = jax.nn.relu(x)
        x = hk.max_pool(x, window_shape=(1, 3, 3, 1),
                        strides=(1, 2, 2, 1), padding="SAME")
    return hk.Flatten()(x)

def forward(obs):
    features = torso(obs)
    policy_logits = hk.Linear(num_actions, name="policy")(features)
    value = hk.Linear(1, name="value")(features)[..., 0]
    return policy_logits, value
```

Do not bundle or run RL environments, replay systems, or long training as part of this sub-skill. Validate shapes with synthetic observations and action counts.
