# Neural-Network and State Workflows

`equinox.nn` provides PyTree modules for neural-network building blocks. They
compose with normal JAX transforms because each layer is an `eqx.Module`.

## Layer catalog

| Family | Symbols | Primary use |
| --- | --- | --- |
| Dense | `Linear`, `Identity`, `MLP` | Feed-forward modules and scalar/vector affine maps. |
| Composition | `Sequential`, `Lambda`, `StatefulLayer` | Ordered callable stacks, activation wrapping, and state-aware composition. |
| Convolution | `Conv`, `Conv1d`, `Conv2d`, `Conv3d`, `ConvTranspose*` | Single-example convolution and transposed convolution layers. |
| Pooling | `Pool`, `MaxPool*`, `AvgPool*`, `AdaptivePool`, `AdaptiveAvgPool*`, `AdaptiveMaxPool*` | Single-example pooling and adaptive pooling. |
| Sequence/attention | `GRUCell`, `LSTMCell`, `MultiheadAttention` | Recurrent cells and attention blocks. |
| Embedding | `Embedding`, `RotaryPositionalEmbedding` | Token/position embeddings and RoPE values. |
| Normalization | `LayerNorm`, `GroupNorm`, `RMSNorm`, `BatchNorm` | Stateless and stateful normalization. |
| Regularization/inference | `Dropout`, `inference_mode` | Stochastic dropout and global inference toggles. |
| State and sharing | `State`, `StateIndex`, `make_with_state`, `delete_init_state`, `Shared` | Stateful layers and tied leaves. |
| Parameter wrappers | `WeightNorm`, `SpectralNorm`, `PReLU` | Reparameterized or trainable helper layers. |

## Single-example convention

Most Equinox layers act on one example. Batch over data with `jax.vmap`:

```python
layer = eqx.nn.Linear(in_size, out_size, key=key)
y_batch = jax.vmap(layer)(x_batch)  # x_batch shape: (batch, in_size)
```

Use `eqx.filter_vmap` when vectorizing over module parameters, ensembles, or
mixed PyTree arguments.

## Basic model composition

```python
model = eqx.nn.Sequential(
    [
        eqx.nn.Linear(2, 16, key=k1),
        eqx.nn.Lambda(jax.nn.relu),
        eqx.nn.Linear(16, 1, key=k2),
    ]
)

y = model(jnp.ones(2))
```

`Sequential` splits a provided key across layers. `Lambda` wraps ordinary
functions so they accept the layer-style `key=` argument.

## MLP notes

Useful signature:

```python
eqx.nn.MLP(in_size, out_size, width_size, depth,
           activation=jax.nn.relu,
           final_activation=lambda x: x,
           use_bias=True, use_final_bias=True, dtype=None,
           *, scan=False, key=key)
```

- `depth=0` creates a single linear layer.
- `depth=1` creates input and output layers.
- `scan=True` stores identical hidden layers in a scanned representation to
  reduce compile-time overhead for deep stacks.
- `in_size="scalar"` or `out_size="scalar"` supports scalar inputs/outputs.

## Training-step skeleton

```python
optim = optax.adam(1e-3)
opt_state = optim.init(eqx.filter(model, eqx.is_inexact_array))

@eqx.filter_jit
def make_step(model, opt_state, x, y):
    def loss_fn(model):
        pred = jax.vmap(model)(x)
        return ((pred - y) ** 2).mean()

    loss, grads = eqx.filter_value_and_grad(loss_fn)(model)
    updates, opt_state = optim.update(grads, opt_state, model)
    model = eqx.apply_updates(model, updates)
    return model, opt_state, loss
```

Use the `module-and-trees` sub-skill for trainable parameter filtering and the
`filtered-transformations` sub-skill for transform/donation choices.

## Stateful layer pattern

Create state with `make_with_state`, then thread it functionally.

```python
class Counter(eqx.Module):
    index: eqx.nn.StateIndex

    def __init__(self):
        self.index = eqx.nn.StateIndex(jnp.array(0))

    def __call__(self, x, state):
        count = state.get(self.index)
        return x + count, state.set(self.index, count + 1)

counter, state = eqx.nn.make_with_state(Counter)()
y, state = counter(jnp.array(1.0), state)
```

For `Sequential`, stateful members subclass `StatefulLayer`; if a state is
passed, `Sequential` calls stateful layers as `(x, state) = layer(x, state=state)`.

## BatchNorm pattern

`BatchNorm` is stateful and expects a named batch axis for training statistics.

```python
class Model(eqx.Module):
    norm: eqx.nn.BatchNorm

    def __init__(self):
        self.norm = eqx.nn.BatchNorm(3, axis_name="batch", mode="batch")

    def __call__(self, x, state):
        return self.norm(x, state)

model, state = eqx.nn.make_with_state(Model)()
vmodel = jax.vmap(
    model, axis_name="batch", in_axes=(0, None), out_axes=(0, None)
)
y, state = vmodel(x_batch, state)
```

Use `out_axes=(0, None)` so the output is batched but the returned `State`
remains a single threaded state object.

Toggle inference mode after training:

```python
inference_model = eqx.nn.inference_mode(model)
```

## Tied weights with `Shared`

Use `Shared` when two positions in a PyTree should refer to the same value.

```python
pair = (embedding, linear)
shared = eqx.nn.Shared(pair, where=lambda p: p[1].weight, get=lambda p: p[0].weight)
embedding, linear = shared()
```

`Shared` validates that the source and destination have compatible structure,
shape, and dtype.

## Validation checklist

- Each layer is called with a single-example shape unless explicitly vmapped.
- Stochastic calls receive a key.
- Stateful calls return and reuse the new `State`, never the old one.
- `BatchNorm.axis_name` matches the `vmap`/`pmap` axis name, and vmapped
  stateful calls use `out_axes=(0, None)`.
- Inference mode is toggled out-of-place and preserved through tree surgery.
- Training steps use filtered transforms for models with static/non-array leaves.
