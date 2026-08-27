# Functional Transforms API Reference

The functional API lives under `sonnet.functional` and is commonly imported as:

```python
import sonnet as snt
fn = snt.functional
```

## Transforming modules

- `fn.variables()`: context manager in which ordinary `tf.Variable` creation produces TensorVariable-backed wrappers so parameters can be captured explicitly.
- `fn.transform(f)`: returns an object with `init(*args, **kwargs)` and `apply(params, *args, **kwargs)` for stateless functions.
- `fn.transform_with_state(f)`: returns `init` and `apply` that also thread mutable state.
- `fn.without_state(transformed)`: adapts a stateless transformed object when a stateful signature is not wanted.

## Differentiation and execution helpers

- `fn.grad(f)` and `fn.value_and_grad(f)` compute gradients with respect to transformed parameters.
- `fn.jit(f)` delegates to TensorFlow graph compilation semantics.
- `fn.device_put(x, device)` and `fn.device_get(x)` move/read tree structures.

## Functional optimizers

`fn.sgd`, `fn.momentum`, `fn.rmsprop`, and `fn.adam` provide functional forms of Sonnet optimizers. They keep optimizer state explicitly; call `optimizer.init(params)` once, then call `optimizer.apply(opt_state, grads, params)` to receive the updated parameter tree and optimizer state.

## TensorVariable caution

A TensorVariable is a placeholder for captured values. It has no usable value before `init` supplies parameters. Do not read it directly before initialization.
