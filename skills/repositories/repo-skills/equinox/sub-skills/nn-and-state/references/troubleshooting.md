# Neural-Network and State Troubleshooting

## Layer receives batched data directly

Most `equinox.nn` layers expect one example. If `Linear` or `MLP` receives an
array with a leading batch dimension and returns a confusing shape or shape
error, wrap the call:

```python
y = jax.vmap(model)(x_batch)
```

Use `eqx.filter_vmap` if the model itself has a leading ensemble/parameter axis.

## `BatchNorm` raises `NameError` or returns a batched state

Symptom: training-time `BatchNorm` raises a named-axis `NameError`, or a vmapped
call appears to add an unwanted leading batch axis to the returned `State`.

Cause: `BatchNorm.axis_name` must match a surrounding named `vmap`/`pmap`, and
state should be threaded once for the whole batch rather than vmapped as an
output.

Recovery steps:

```python
bn, state = eqx.nn.make_with_state(eqx.nn.BatchNorm)(
    3, axis_name="batch", mode="batch"
)
vbn = jax.vmap(bn, axis_name="batch", in_axes=(0, None), out_axes=(0, None))
y, state = vbn(x_batch, state)
```

If no batching is intended, do not use `BatchNorm`; choose `LayerNorm`,
`GroupNorm`, or `RMSNorm` when appropriate.

## `Attempted to use old state`

`State.set` and `State.update` invalidate the old object as a safety guard.
Always thread the new state forward:

```python
x, state = layer1(x, state)
x, state = layer2(x, state)
```

Do not reuse `state0` after calling a layer that returned `state1`.

## `Do not call eqx.nn.State(model) directly`

Some stateful layers use deleted initial states after construction. Prefer:

```python
model, state = eqx.nn.make_with_state(ModelClass)(*args, **kwargs)
```

Call `eqx.nn.State(model)` directly only for simple inspection and only before
initial states have been removed.

## Dropout appears deterministic or random in the wrong mode

`Dropout` needs explicit keys for stochastic calls. It should be bypassed when
`inference=True`.

- Pass a fresh split key to each stochastic layer call.
- Use `eqx.nn.inference_mode(model)` for evaluation.
- Use `eqx.nn.inference_mode(model, value=False)` to return to training mode.

## `Sequential` fails around activations

`Sequential` expects layers to accept a `key=` keyword argument. Wrap plain
functions:

```python
seq = eqx.nn.Sequential([eqx.nn.Linear(...), eqx.nn.Lambda(jax.nn.relu)])
```

If the sequence contains stateful layers and you pass a `State`, it returns
`(output, state)`. If no state is passed, it returns only the output.

## `Shared` raises structure/shape/dtype errors

`Shared` validates source and destination using `filter_eval_shape` and
`tree_equal`. The target selected by `where` and source returned by `get` must
match as PyTrees.

Checklist:

- Does `where(pytree)` select the exact destination leaf or leaves?
- Does `get(pytree)` return the source with matching shape and dtype?
- If transposing a matrix is intentional, put the transpose inside `get`.
- If multiple nodes are tied, do `where` and `get` return sequences of the same
  length?

## MLP scanned hidden layers are confusing

`MLP(..., scan=True)` stores hidden layers with an extra leading axis and uses
`jax.lax.scan` internally. Do not call the hidden layer stack directly; call the
MLP object. Use `scan=True` for compile-time benefits when many same-shaped
hidden layers are chained.

## Training updates include static values

For optimizers, initialize and update only differentiable array leaves:

```python
opt_state = optim.init(eqx.filter(model, eqx.is_inexact_array))
```

Use `eqx.apply_updates` to apply Optax updates back to the full model while
leaving `None` update leaves unchanged.
