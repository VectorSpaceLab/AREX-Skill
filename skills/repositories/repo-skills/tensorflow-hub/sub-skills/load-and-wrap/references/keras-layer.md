# KerasLayer patterns

## Choose the right input form

`hub.KerasLayer` accepts either:

- a string handle, which it loads itself; or
- an already-loaded callable object, which it wraps directly.

Use a string when you need `tags` or `load_options`. Use a callable object when loading has already happened upstream.

## Basic callable SavedModel

If the exported object is callable, the simplest form is:

```python
import tensorflow as tf
import tensorflow_hub as hub

layer = hub.KerasLayer(export_dir)
y = layer(tf.constant([1.0, 2.0]))
```

This is the preferred current pattern when the SavedModel exposes a callable `__call__` and the output is a single tensor or a well-behaved nest.

## Signature-based loading

If the SavedModel exposes a named signature, select it explicitly:

```python
layer = hub.KerasLayer(
    export_dir,
    signature="serving_default",
    output_key="output",
)
```

Use `signature_outputs_as_dict=True` when you want the full signature output dict instead of a single tensor:

```python
layer = hub.KerasLayer(
    export_dir,
    signature="serving_default",
    signature_outputs_as_dict=True,
)
```

Rules to remember:

- When using a signature, choose exactly one output-selection mode: `output_key` or `signature_outputs_as_dict=True`.
- `output_key` is only valid when the output is a dict.
- `signature_outputs_as_dict=True` is only valid when a signature is being used.
- If the loaded object is not callable and has no signatures, the layer cannot infer a callable path.

## Trainability limits

`trainable=True` is only meaningful when the wrapped object is callable and exposes trainable variables in a way that Keras can use.

Do not expect signatures to support fine-tuning. The current package rejects `trainable=True` when the layer is calling a SavedModel signature.

Useful symptoms:

- A trainable signature-based layer raises a `ValueError` at call time.
- A trainable layer with zero trainable weights logs an error once, which usually means the export did not expose trainable variables.

If a model must be trained end-to-end, export a callable SavedModel that exposes the training path directly instead of trying to train through a signature.

## Output shape hints

Use `output_shape` when shape inference is weak or unavailable.

```python
hub.KerasLayer(
    export_dir,
    output_shape=(20,),
    input_shape=(),
    dtype=tf.string,
)
```

Guidelines:

- `output_shape` is the shape *without* the leading batch dimension.
- The structure of `output_shape` must match the structure of the callable output.
- It can be a tuple or a nest of tuples.
- If the output is nested, every output tensor needs a matching shape entry.

## Additional arguments

`arguments` forwards extra keyword arguments to the callable:

```python
hub.KerasLayer(export_dir, arguments={"temperature": 0.1})
```

Use this only for JSON-serializable values. These values are not checkpointed as mutable layer state.

## Load options

`load_options` passes a `tf.saved_model.LoadOptions` object through when the handle is a string.

Notes:

- It is only relevant on TensorFlow versions that support `LoadOptions`.
- It does not make sense for a callable handle that was already loaded upstream.
- When a callable object is passed instead of a string, `tags` and `load_options` are mutually exclusive with that callable input.

## Keras 3 and `tf_keras`

When `tf.keras.version()` starts with `3.`, TensorFlow Hub uses the `tf_keras` compatibility package internally.

Practical rule:

- If the surrounding model also needs `DenseFeatures`, `Sequential`, serialization, or other Keras 2 style layers, use `tf_keras` in that model too.
- If `tf_keras` is missing in a Keras 3 environment, import-time or layer-construction failures are expected until the compatibility package is installed.

## Minimal patterns

Callable SavedModel:

```python
layer = hub.KerasLayer(export_dir)
```

Dict-valued signature, return one output:

```python
layer = hub.KerasLayer(export_dir, signature="serving_default", output_key="output")
```

Dict-valued signature, return all outputs:

```python
layer = hub.KerasLayer(
    export_dir,
    signature="serving_default",
    signature_outputs_as_dict=True,
)
```

If you need more detail on the failure modes, read [troubleshooting.md](troubleshooting.md).
