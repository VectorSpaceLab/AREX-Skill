# Network API

This repo exposes five optimizer-network classes plus two serialization helpers.
Use this reference when you need to pick a network, build a config for `networks.factory`,
or recover a saved optimizer from `networks.save`.

## Selection cheat sheet

- Use `CoordinateWiseDeepLSTM` for elementwise learned updates on arbitrary-shaped tensors.
- Use `KernelDeepLSTM` for convolution kernels with shape `[kernel_w, kernel_h, in_channels, out_channels]`.
- Use `Sgd` when you want a fixed first-order baseline with no state.
- Use `Adam` when you want a fixed baseline with moment state but no trainable variables.
- Use `StandardDeepLSTM` only when you need the raw 2D base class directly.

## `networks.factory`

`factory(net, net_options=(), net_path=None)` resolves the class by name, converts
`net_options` to a dict, and optionally loads an initializer from `net_path`.
If `net_path` is present, the loaded initializer replaces any `initializer`
entry already in `net_options`.

Supported `net` values are the class names:

- `StandardDeepLSTM`
- `CoordinateWiseDeepLSTM`
- `KernelDeepLSTM`
- `Sgd`
- `Adam`

If the name is wrong, the call fails early with an attribute lookup error.
Use the helper script in `scripts/inspect_network_config.py` to validate names
before you try to build a graph.

## `networks.save`

`save(network, sess, filename=None)` collects variables from the Sonnet module
and stores them as a nested dictionary:

```python
{
  "lstm_1": {"w_gates": ..., "b_gates": ...},
  "lstm_2": {"w_gates": ..., "b_gates": ...},
  "linear": {"w": ..., "b": ...},
}
```

For stateless nets such as `Sgd` and `Adam`, the saved mapping is empty.
If `filename` is given, the mapping is written with `dill` as a pickle file,
usually with a `.l2l` suffix.

## Initializer forms

`StandardDeepLSTM` and its subclasses accept several initializer shapes:

- string: `"zeros"` becomes `tf.zeros_initializer(dtype=tf.float32)`
- NumPy array: becomes `tf.constant_initializer(array)`
- TensorFlow initializer: used as-is
- dict: layer-specific or field-specific initializer mapping

Layer keys are the Sonnet module names:

- `lstm_1`, `lstm_2`, ... for recurrent layers
- `linear` for the output projection

Field keys are the variable names expected by the layer:

- `w_gates`, `b_gates` for `snt.LSTM`
- `w`, `b` for `snt.Linear`

Extra dict keys are ignored by the selection logic, so a typo can silently leave
some parameters on their default initializer. Check the resulting variables if
an initializer seems to have no effect.

Preprocess resolution works the same way: if `preprocess_name` matches a module
in `preprocess`, that module is constructed with `preprocess_options`; otherwise
the name is resolved on `tf`.

## Class contracts

| Class | Input shape | Output shape | Runtime state | Trainable vars | Notes |
| --- | --- | --- | --- | --- | --- |
| `StandardDeepLSTM` | 2D `[batch, features]` | `[batch, output_size]` | Nested `DeepRNN` state, one entry per LSTM layer | Yes | Applies preprocessing to `tf.expand_dims(inputs, -1)` then flattens before the RNN. |
| `CoordinateWiseDeepLSTM` | Any tensor shape | Same as input | Flattened `DeepRNN` state over `prod(input_shape)` coordinates | Yes | Reshapes to `[-1, 1]`, runs the base class, then reshapes back. |
| `KernelDeepLSTM` | 4D `[kernel_w, kernel_h, in_channels, out_channels]` | Same as input | Flattened `DeepRNN` state over `in_channels * out_channels` kernels | Yes | Transposes to `[in_channels, out_channels, kernel_w, kernel_h]` before the base class. |
| `Sgd` | Any tensor shape | Same as input | `[]` | No | Returns `-learning_rate * gradient`. |
| `Adam` | Any tensor shape with concrete static shape | Same as input | `(t, m, v)` | No | `t` is scalar; `m` and `v` are `[prod(shape), 1]`. |

### State and shape notes

- `CoordinateWiseDeepLSTM` and `KernelDeepLSTM` derive their state size from
  static shapes, so unknown dimensions can cause construction errors.
- `KernelDeepLSTM` requires a rank-4 input tensor. A different rank usually
  fails at the transpose or reshape step.
- `Adam.initial_state_for_inputs` also relies on static shape information.

## Example configs

```python
{
  "net": "CoordinateWiseDeepLSTM",
  "net_options": {
    "layers": (20, 20),
    "preprocess_name": "LogAndSign",
    "preprocess_options": {"k": 5},
    "scale": 0.01,
    "initializer": "zeros",
  },
}
```

```python
{
  "net": "KernelDeepLSTM",
  "net_options": {
    "kernel_shape": [5, 5],
    "layers": (20,),
    "preprocess_name": "Clamp",
    "preprocess_options": {"min_value": -1.0, "max_value": 1.0},
  },
}
```

## Serialization flow

1. Call `networks.save(network, sess, filename="optimizer.l2l")`.
2. Pass the saved file back into `networks.factory(..., net_path="optimizer.l2l")`.
3. The loaded file becomes the initializer spec for the new network instance.

For a stateless baseline, the file may contain an empty mapping; that is normal.
