---
name: tensorflow-hub
description: "Use TensorFlow Hub to resolve, load, wrap, and export
  Hub-compatible TensorFlow SavedModels."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow Hub

Use this repo skill when a task involves the `tensorflow-hub` package, the `tensorflow_hub` import, TensorFlow Hub/Kaggle Models handles, `tfhub.dev` URLs, local Hub-compatible `SavedModel` directories, `hub.load`, `hub.resolve`, or `hub.KerasLayer`.

The current package surface verified for this skill exposes only these top-level APIs:

```python
import tensorflow_hub as hub

hub.load
hub.resolve
hub.KerasLayer
```

Feature-column text embedding support is available through a submodule import, not as a top-level `hub` attribute:

```python
import tensorflow_hub.feature_column_v2 as hub_feature_column_v2
```

## Quick install and import check

Use a TensorFlow runtime that matches the Python environment. In Keras 3 environments, install the matching `tf-keras` compatibility package as well.

```bash
python -m pip install tensorflow-hub tensorflow tf-keras
python - <<'PY'
import tensorflow as tf
import tensorflow_hub as hub
print("tensorflow", tf.__version__)
print("tensorflow_hub", hub.__version__)
print("exports", hub.__all__)
PY
```

If the import check fails, read [references/troubleshooting.md](references/troubleshooting.md) before changing package versions.

## Route map

| User task or symptom | Read next |
| --- | --- |
| Resolve or load a Hub handle, local SavedModel path, `tfhub.dev`/Kaggle Models URL, or archive | [sub-skills/load-and-wrap/SKILL.md](sub-skills/load-and-wrap/SKILL.md) |
| Diagnose `TFHUB_CACHE_DIR`, `TFHUB_MODEL_LOAD_FORMAT`, download locks, corrupt archives, or certificate validation | [sub-skills/load-and-wrap/references/load-resolve-cache.md](sub-skills/load-and-wrap/references/load-resolve-cache.md) |
| Wrap a Hub SavedModel in Keras, choose `signature`, `output_key`, `signature_outputs_as_dict`, `output_shape`, or `trainable` | [sub-skills/load-and-wrap/references/keras-layer.md](sub-skills/load-and-wrap/references/keras-layer.md) |
| Use `text_embedding_column_v2`, `DenseFeatures`, or recover from `hub.text_embedding_column_v2` `AttributeError` | [sub-skills/load-and-wrap/references/feature-column-v2.md](sub-skills/load-and-wrap/references/feature-column-v2.md) |
| Create a TF2 `SavedModel` that can be consumed by TensorFlow Hub | [sub-skills/export-and-save/SKILL.md](sub-skills/export-and-save/SKILL.md) |
| Export text embeddings from a token/vector file | [sub-skills/export-and-save/references/text-embedding-export.md](sub-skills/export-and-save/references/text-embedding-export.md) |
| Migrate or triage old TF1 `hub.Module`, `create_module_spec`, or `add_signature` snippets | [sub-skills/export-and-save/references/legacy-tf1-notes.md](sub-skills/export-and-save/references/legacy-tf1-notes.md) |
| Check whether this skill matches the current source checkout | [references/repo-provenance.md](references/repo-provenance.md) |

## Safe local validation

Before using a network-backed handle or a large model, run the no-download smoke script from the loading sub-skill:

```bash
python sub-skills/load-and-wrap/scripts/smoke_load_and_wrap.py --feature-column
```

For text embedding export tasks, use the bundled exporter under the export sub-skill:

```bash
python sub-skills/export-and-save/scripts/export_text_embeddings_v2.py --help
```

Both scripts create only temporary/local outputs chosen by the caller and do not read the original repository checkout.

## Boundaries

Use this skill for:

- loading or resolving TensorFlow Hub handles and local SavedModels;
- Keras integration through `hub.KerasLayer`;
- feature-column text embedding workflows through `tensorflow_hub.feature_column_v2`;
- creating TF2 `SavedModel` exports that are meant to be reloaded by TensorFlow Hub;
- text embedding SavedModel export from small or production token/vector files;
- troubleshooting TensorFlow Hub import, cache, signature, and legacy API confusion.

Do not use this skill as the main route for:

- general TensorFlow model training unrelated to TensorFlow Hub handles or exports;
- deprecated TF1 image-retraining scripts;
- TensorFlow Hub repository maintenance, Bazel release builds, or pull-request policy;
- current code that assumes `hub.Module`, `hub.create_module_spec`, `hub.add_signature`, or top-level `hub.text_embedding_column_v2` exist without first checking an older archived runtime.
