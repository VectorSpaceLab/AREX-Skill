# TF2 SavedModel export for TensorFlow Hub consumers

TensorFlow Hub consumers in this package load plain TF2 `SavedModel` directories. Author the model with TensorFlow APIs, save it with `tf.saved_model.save(...)`, then validate through `tensorflow_hub.load(...)` and, when relevant, `tensorflow_hub.KerasLayer(...)`.

## Current public boundary

| Task | Current API |
| --- | --- |
| Low-level reload validation | `tensorflow_hub.load(handle, tags=None, options=None)` |
| Path/remote handle resolution | `tensorflow_hub.resolve(handle)` |
| Keras wrapper validation | `tensorflow_hub.KerasLayer(handle, trainable=False, arguments=None, tags=None, signature=None, signature_outputs_as_dict=None, output_key=None, output_shape=None, load_options=None, **kwargs)` |
| Legacy TF1 module publishing | Not a current top-level API in this checkout |

A TensorFlow Hub handle can be a local `SavedModel` directory, a compatible archive/URL, or a tfhub.dev/Kaggle Models handle. This reference focuses on creating a local TF2 `SavedModel` directory that can later become such a handle.

## Pattern 1: callable `tf.Module`

Use this when the exported object should be directly callable by `hub.load(export_dir)(inputs)` and by `hub.KerasLayer(export_dir)` without naming a signature.

```python
import tensorflow as tf
import tensorflow_hub as hub

class ScaleAndShift(tf.Module):
    def __init__(self):
        super().__init__()
        self.scale = tf.Variable(0.5, trainable=True, name="scale")
        self.shift = tf.Variable(2.0, trainable=True, name="shift")

    @tf.function(input_signature=[tf.TensorSpec([None], tf.float32, name="x")])
    def __call__(self, x):
        return self.scale * x + self.shift

export_dir = "exported_scale_and_shift"
tf.saved_model.save(ScaleAndShift(), export_dir)

loaded = hub.load(export_dir)
print(loaded(tf.constant([0.0, 4.0])).numpy())  # [2.0, 4.0]

layer = hub.KerasLayer(export_dir, input_shape=[], dtype=tf.float32)
print(layer(tf.constant([0.0, 4.0])).numpy())
```

Why this works well for TensorFlow Hub:

- `@tf.function(input_signature=...)` freezes the public input contract.
- A callable `__call__` makes `hub.KerasLayer(handle)` straightforward.
- Variables tracked on the module become loadable variables; `KerasLayer(trainable=True)` can expose trainable variables only for callable TF2 SavedModels, not for signature-only calls.

## Pattern 2: Keras model saved as a TF2 SavedModel

For Keras models, build the model first, then save the object or a serving wrapper. Prefer an explicit input signature so downstream callers do not have to guess dtype or rank.

```python
import tensorflow as tf
import tensorflow_hub as hub

inputs = tf.keras.Input(shape=(4,), dtype=tf.float32)
outputs = tf.keras.layers.Dense(2, name="projection")(inputs)
model = tf.keras.Model(inputs, outputs)

@tf.function(input_signature=[tf.TensorSpec([None, 4], tf.float32, name="features")])
def serve(features):
    return model(features)

export_dir = "exported_projection"
tf.saved_model.save(model, export_dir, signatures=serve)

loaded = hub.load(export_dir)
print(loaded.signatures["serving_default"](features=tf.ones([1, 4])))
```

If the loaded object is not directly callable, use a named signature for validation and for `KerasLayer`:

```python
layer = hub.KerasLayer(
    export_dir,
    signature="serving_default",
    output_key="output_0",      # Replace with the actual output key.
    input_shape=(4,),
    dtype=tf.float32,
)
```

Inspect the actual keys first:

```python
loaded = hub.load(export_dir)
fn = loaded.signatures["serving_default"]
print(fn.structured_input_signature)
print(fn.structured_outputs)
```

## Pattern 3: explicit dict signatures

Create a dict signature when consumers need named outputs, multiple outputs, or a non-callable serving interface. Signature functions receive keyword arguments under their TensorSpec names and return a dict.

```python
import tensorflow as tf
import tensorflow_hub as hub

class Embedder(tf.Module):
    @tf.function(input_signature=[tf.TensorSpec([None, 8], tf.float32, name="features")])
    def embed(self, features):
        embedding = tf.math.l2_normalize(features, axis=-1)
        return {
            "embedding": embedding,
            "norm": tf.norm(features, axis=-1),
        }

module = Embedder()
export_dir = "exported_embedder"
tf.saved_model.save(module, export_dir, signatures={"serving_default": module.embed})

loaded = hub.load(export_dir)
result = loaded.signatures["serving_default"](features=tf.ones([2, 8]))
print(result["embedding"].shape, result["norm"].shape)
```

Consume a dict signature with `KerasLayer` by selecting an output key or asking for the whole dict:

```python
embedding_layer = hub.KerasLayer(
    export_dir,
    signature="serving_default",
    output_key="embedding",
    input_shape=(8,),
    dtype=tf.float32,
)

all_outputs_layer = hub.KerasLayer(
    export_dir,
    signature="serving_default",
    signature_outputs_as_dict=True,
    input_shape=(8,),
    dtype=tf.float32,
)
```

`KerasLayer` requires exactly one of `output_key` or `signature_outputs_as_dict=True` when `signature` is set. It does not support `trainable=True` for signature calls; use a callable `__call__` SavedModel if trainable Keras wrapping is required.

## Assets and lookup tables

If the model depends on a vocabulary, label map, or other file asset, track it through TensorFlow instead of embedding a local path in Python code.

Preferred TF2 asset pattern:

```python
import tensorflow as tf

class VocabularyModule(tf.Module):
    def __init__(self, vocab_path):
        super().__init__()
        self.vocab_asset = tf.saved_model.Asset(vocab_path)

    @tf.function(input_signature=[])
    def vocab_file(self):
        return self.vocab_asset.asset_path

module = VocabularyModule("tokens.txt")
tf.saved_model.save(module, "exported_vocab_module")
```

Lookup-table initializers can also be tracked as module attributes. The bundled text embedding exporter does this so the vocabulary is copied into the `SavedModel` assets area during `tf.saved_model.save(...)`.

Asset rules:

- Do not keep absolute construction-machine paths in callable code.
- Attach assets to the module as `tf.saved_model.Asset` or as TensorFlow trackable lookup-table components.
- After export, move only the `SavedModel` directory; validation should still work after the original asset source file is removed.

## Export validation checklist

Run these checks immediately after export:

1. The export directory contains `saved_model.pb` or `saved_model.pbtxt`.
2. `tensorflow_hub.load(export_dir)` succeeds.
3. The loaded object is either callable or exposes the expected `loaded.signatures` keys.
4. A representative tensor call returns the expected dtype, shape, and values.
5. If Keras usage is required, `tensorflow_hub.KerasLayer(export_dir, ...)` works with the intended callable or signature settings.
6. If the model has assets, validation still works after the source asset files outside the `SavedModel` are unavailable.

For deeper loading, cache, and Keras wrapper behavior, route to the sibling `load-and-wrap` sub-skill through the TensorFlow Hub root router.
