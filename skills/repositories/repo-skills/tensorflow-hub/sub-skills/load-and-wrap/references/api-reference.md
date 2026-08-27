# API reference

## Verified public exports

`tensorflow_hub.__all__` is:

```python
['KerasLayer', 'load', 'resolve']
```

The current top-level public API is therefore:

- `tensorflow_hub.load`
- `tensorflow_hub.resolve`
- `tensorflow_hub.KerasLayer`

## Verified signatures

```python
hub.load(handle, tags=None, options=None)
hub.resolve(handle)
hub.KerasLayer(handle, trainable=False, arguments=None, _sentinel=None,
               tags=None, signature=None, signature_outputs_as_dict=None,
               output_key=None, output_shape=None, load_options=None, **kwargs)
tensorflow_hub.feature_column_v2.text_embedding_column_v2(
    key, module_path, output_key=None, trainable=False)
```

## Import paths to use

```python
import tensorflow_hub as hub
import tensorflow_hub.feature_column_v2 as hub_feature_column_v2
```

Use the submodule import for feature columns. Do not expect a top-level `text_embedding_column_v2` symbol.

## Absent top-level APIs

The following attributes are not present in this package version:

- `hub.Module`
- `hub.create_module_spec`
- `hub.load_module_spec`
- `hub.add_signature`
- `hub.attach_message`
- `hub.text_embedding_column_v2`
- `hub.feature_column_v2`

## Minimal examples

Load and call a local SavedModel:

```python
import tensorflow as tf
import tensorflow_hub as hub

loaded = hub.load(export_dir)
y = loaded(tf.constant([1.0, 2.0]))
```

Wrap the same model for Keras:

```python
import tensorflow as tf
import tensorflow_hub as hub

layer = hub.KerasLayer(export_dir)
y = layer(tf.constant([1.0, 2.0]))
```

Use the feature-column helper directly from the submodule:

```python
import tensorflow_hub.feature_column_v2 as hub_feature_column_v2

column = hub_feature_column_v2.text_embedding_column_v2("text", export_dir)
```

## Quick selection rule

- Use `load` when you want the loaded object itself.
- Use `resolve` when you want the on-disk path that a handle maps to.
- Use `KerasLayer` when you need Keras integration or serialization.
- Use the feature-column submodule when you need a text embedding `DenseColumn`.
