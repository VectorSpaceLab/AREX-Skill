# Legacy TF1 TensorFlow Hub Module notes

This package version should use TF2 `SavedModel` export recipes first. The older TensorFlow Hub Module publishing flow is historical evidence, not a current runtime recipe for this checkout.

## Current absence of legacy top-level publishers

The installed public top-level API exposes `KerasLayer`, `load`, and `resolve`. The following legacy publisher attributes are absent at top level in this checkout:

- `tensorflow_hub.Module`
- `tensorflow_hub.create_module_spec`
- `tensorflow_hub.load_module_spec`
- `tensorflow_hub.add_signature`
- `tensorflow_hub.attach_message`
- `hub.text_embedding_column_v2` after `import tensorflow_hub as hub`
- `hub.feature_column_v2` after `import tensorflow_hub as hub` (the direct submodule import is separate)

Do not write new runtime instructions that call those attributes as if they exist. If user code raises `AttributeError` for one of them, translate the task to a TF2 `SavedModel` pattern from [savedmodel-export.md](savedmodel-export.md) or stop and ask whether the user intentionally needs an archived TF1 TensorFlow Hub Module environment.

## What the old exporters did

Historical TensorFlow Hub examples used TensorFlow 1 graph construction to create TF1 Hub Modules:

- A simple numeric module created variables in a graph, registered a default signature with `add_signature`, instantiated `Module(create_module_spec(...))`, assigned variables in a `tf.compat.v1.Session`, and called `module.export(...)`.
- The legacy text embedding exporter built placeholders and lookup tables, registered `default` signatures, optionally preprocessed text, assigned embedding variables through feed dictionaries, and exported a TF1 Hub Module.
- The old ModuleSpec layer documented deprecation and said TF2 should switch to plain `SavedModel` plus `hub.load()`.
- Internal SavedModel utilities handled TF1 collections, attached messages, tags, and asset rewriting for legacy module export/loading. Those internals are not the preferred public export API for current TF2 work.

These behaviors are useful for migration analysis but should not be copied into current guidance unless an explicit TF1 compatibility requirement is in scope.

## Migration mapping

| Legacy goal | Current default |
| --- | --- |
| `hub.create_module_spec(module_fn)` | Define a `tf.Module` or Keras model with `@tf.function` methods. |
| `hub.add_signature(...)` | Return a dict from an explicit TF2 signature passed to `tf.saved_model.save(..., signatures={...})`. |
| `hub.Module(spec)` and `module.export(path, session)` | Save the trackable object with `tf.saved_model.save(obj, path)`. |
| TF1 placeholder inputs | `tf.TensorSpec` input signatures. |
| TF1 Module default output key | Dict signature output key selected by `KerasLayer(..., output_key=...)`, or a callable `__call__` that returns a tensor. |
| TF1 session variable assignment | Track `tf.Variable` objects on the module/model and initialize them before saving. |
| TF1 text embedding exporter | Use [../scripts/export_text_embeddings_v2.py](../scripts/export_text_embeddings_v2.py). |

## When to stop for an older environment

Stop and ask for an archived/older environment only when the downstream task explicitly requires a TF1 TensorFlow Hub Module artifact rather than a TF2 `SavedModel`. Examples:

- The consuming system only accepts TF1 Hub Module metadata and collections.
- The user must reproduce behavior of a historical paper or application that loads with `hub.Module` under TensorFlow 1.
- The required artifact depends on TF1 graph collections, tags, attached messages, or ModuleSpec inspection APIs.

Before proceeding in that direction, make the risk explicit: the current package API in this checkout does not expose the legacy top-level publishers, so a separate pinned environment or archived package version is required. Do not silently downgrade or rewrite the runtime skill to depend on those missing APIs.

## Safe migration posture

- Prefer TF2 `SavedModel` plus `tensorflow_hub.load`/`KerasLayer` for all new exports.
- Keep legacy snippets as evidence for expected inputs, preprocessing, signatures, and outputs, not as commands to run.
- If an old snippet uses `preprocess_text`, map that behavior to the TF2 text embedding exporter tokenizer or implement equivalent preprocessing in a callable `tf.Module`.
- If an old snippet relies on `default` signature names, decide whether the TF2 model should be directly callable or expose `serving_default` with a named output.
