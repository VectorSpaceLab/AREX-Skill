# Feature-column v2

## Direct import path

The text embedding helper is available only from the submodule import path in this package version:

```python
import tensorflow_hub.feature_column_v2 as hub_feature_column_v2
```

Do not expect a top-level `tensorflow_hub.text_embedding_column_v2` or `tensorflow_hub.feature_column_v2` symbol.

## Constructor and output selection

```python
column = hub_feature_column_v2.text_embedding_column_v2(
    key="text",
    module_path=module_path,
    output_key=None,
    trainable=False,
)
```

Use `output_key` when the exported SavedModel returns a dict and you need one named tensor from that dict. Leave it unset only when the SavedModel returns a single tensor or the default output is unambiguous.

`trainable=True` should be reserved for the case where the downstream model is intentionally fine-tuning the wrapped module and the surrounding training state is enabled. If the module is only being used as a frozen pretrained embedding, keep `trainable=False`.

## Parse-spec behavior

The returned column is a `DenseColumn` with a one-token string feature spec.

Key points:

- `parents` is the input key list.
- `parse_example_spec` is a `FixedLenFeature([1], tf.string)` entry for that key.
- The feature column is meant to be fed through `tf.feature_column.make_parse_example_spec([...])` when building `tf.Example` pipelines.

## DenseFeatures workflow

A typical flow is:

```python
import tensorflow as tf
import tensorflow_hub.feature_column_v2 as hub_feature_column_v2

# Keras 3 environments should use tf_keras for the model-side layers.
try:
    import tf_keras as keras
except ImportError:
    import tensorflow.keras as keras

column = hub_feature_column_v2.text_embedding_column_v2("text", module_path)
dense_features = keras.layers.DenseFeatures([column])
outputs = dense_features({"text": tf.constant(["hi", "there"])})
```

Use this path when the task is to feed text embeddings into `DenseFeatures`, a Keras model, or a feature-column-based input pipeline.

## Dict outputs and recovery

If the SavedModel returns a dict and the result is ambiguous, set `output_key` before building the column. If you do not, the helper cannot infer which tensor to use.

When the helper raises an error about the output not being a single result, the usual fix is to choose the correct `output_key` or to export a callable SavedModel that returns a single tensor.

## Top-level `AttributeError` recovery

If you see:

```text
AttributeError: module 'tensorflow_hub' has no attribute 'text_embedding_column_v2'
```

switch to the submodule import path shown above. That attribute is not exported at the top level in this package version.

## When to read this reference

Read this file after `keras-layer.md` if the task specifically mentions a text embedding column, `DenseFeatures`, or an import-path mistake.
