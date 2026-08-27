---
name: export-and-save
description: "Create TensorFlow Hub-consumable TF2 SavedModels and export text
  embedding SavedModels."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Export and Save

Use this sub-skill when the task is to create a TensorFlow Hub-consumable TF2 `SavedModel`, prepare a local model for later use with `tensorflow_hub.load` or `tensorflow_hub.KerasLayer`, or export a text embedding model from token/vector text files.

Do not use this sub-skill as a current recipe for legacy TF1 TensorFlow Hub Module publishing. In this package version, the current top-level public API is `tensorflow_hub.load`, `tensorflow_hub.resolve`, and `tensorflow_hub.KerasLayer`; legacy top-level publishers such as `Module`, `create_module_spec`, `load_module_spec`, `add_signature`, and `attach_message` are absent.

## Quick routing

- For general TF2 `tf.Module` or Keras `SavedModel` export patterns, read [references/savedmodel-export.md](references/savedmodel-export.md).
- For token/vector text embedding export, read [references/text-embedding-export.md](references/text-embedding-export.md) and use [scripts/export_text_embeddings_v2.py](scripts/export_text_embeddings_v2.py).
- For old TF1 TensorFlow Hub Module exporter snippets, read [references/legacy-tf1-notes.md](references/legacy-tf1-notes.md) before deciding whether to stop or request an archived runtime.
- For export, reload, signature, asset, OOV, and path failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Quick workflow

1. Decide the export shape: a callable `tf.Module`/Keras object, an explicit signature, or the bundled text embedding workflow.
2. Save a plain TF2 `SavedModel` with `tf.saved_model.save(...)`. Give callable models an `@tf.function` `__call__` with an `input_signature`; give signature-only models explicit named signatures.
3. Validate from the public TensorFlow Hub side with `tensorflow_hub.load(export_path)`. For Keras integration, validate with `tensorflow_hub.KerasLayer(...)` using `signature` and `output_key` when the SavedModel exposes only a dict signature.
4. If validation needs deeper loader, cache, or KerasLayer diagnosis, route through the sibling `load-and-wrap` sub-skill via the TensorFlow Hub root router.

## Minimal bundled text embedding command

```bash
python scripts/export_text_embeddings_v2.py \
  --embedding-file embeddings.txt \
  --export-path exported_text_embedding \
  --verify \
  --sample-text "cat dog" --sample-text "unknown-token" ""
```

The embedding file must contain one whitespace-separated token and numeric vector per line. The exporter writes a TF2 `SavedModel`, not a legacy TF1 TensorFlow Hub Module.
