# TensorFlow Hub troubleshooting

Read this first when the failure happens before you know whether the task belongs to loading/wrapping or exporting. For workflow-specific details, continue to the loading sub-skill or export sub-skill references linked below.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: No module named tensorflow` while importing `tensorflow_hub` | TensorFlow is not available in the active Python environment. | Install a TensorFlow runtime compatible with the Python version, then rerun the import check from the root skill. |
| `ImportError: No module named tf_keras` | TensorFlow is using Keras 3 and TensorFlow Hub needs Keras 2 compatibility. | Install a matching `tf-keras` package. If the surrounding model also uses Keras 2 style layers such as `DenseFeatures`, import and use `tf_keras` consistently. |
| `ModuleNotFoundError: No module named 'pkg_resources'` | The package version still imports `pkg_resources`, but the active setuptools version no longer provides it. | Install a setuptools release that still includes `pkg_resources` or use a newer TensorFlow Hub package that removed that dependency. A deprecation warning from `pkg_resources` alone is not a Hub workflow failure. |
| TensorFlow logs `Could not find cuda drivers` or `GPU will not be used` | The runtime is CPU-only or GPU libraries are unavailable. | For the workflows in this skill, CPU execution is sufficient unless the user's own model requires GPU. Do not treat this as a TensorFlow Hub failure by itself. |
| Import succeeds but `hub.__all__` lacks expected symbols | User code is written for an older or different TensorFlow Hub API. | Check [../sub-skills/load-and-wrap/references/api-reference.md](../sub-skills/load-and-wrap/references/api-reference.md) and migrate to the current public surface. |

## API confusion

Current top-level exports are `KerasLayer`, `load`, and `resolve`. The following names are not top-level APIs for this checkout:

- `hub.Module`
- `hub.create_module_spec`
- `hub.load_module_spec`
- `hub.add_signature`
- `hub.attach_message`
- `hub.text_embedding_column_v2`
- `hub.feature_column_v2`

Use [../sub-skills/export-and-save/references/legacy-tf1-notes.md](../sub-skills/export-and-save/references/legacy-tf1-notes.md) for TF1 Module migration notes. Use [../sub-skills/load-and-wrap/references/feature-column-v2.md](../sub-skills/load-and-wrap/references/feature-column-v2.md) for the direct feature-column submodule import path.

## Loading and cache failures

If a handle, URL, local path, cache directory, lock file, archive, or certificate setting is involved, read [../sub-skills/load-and-wrap/references/load-resolve-cache.md](../sub-skills/load-and-wrap/references/load-resolve-cache.md).

Fast triage:

1. Prove a local no-download SavedModel works with `python sub-skills/load-and-wrap/scripts/smoke_load_and_wrap.py`.
2. If local loading works, set `TFHUB_CACHE_DIR` to a writable task-local cache before trying a remote handle.
3. Use `TFHUB_MODEL_LOAD_FORMAT=AUTO` or `COMPRESSED` unless the server explicitly supports the uncompressed `303` to `gs://...` protocol.
4. Do not delete cache locks until you are sure no other process owns the download.
5. Do not set `TFHUB_DISABLE_CERT_VALIDATION=true` except for trusted test endpoints.

## Keras and signature failures

If the task uses `hub.KerasLayer`, read [../sub-skills/load-and-wrap/references/keras-layer.md](../sub-skills/load-and-wrap/references/keras-layer.md).

Common rules:

- Signature-based layers require exactly one of `output_key` or `signature_outputs_as_dict=True`.
- `trainable=True` is unsupported for signature calls and legacy TF1 Hub format loading.
- Use `output_shape` when static shape inference is weak.
- Use `arguments` only for JSON-serializable callable keyword arguments.

## Export failures

If the task creates a `SavedModel` or text embedding module, read [../sub-skills/export-and-save/SKILL.md](../sub-skills/export-and-save/SKILL.md).

Fast triage:

1. Confirm the export is a current TF2 `SavedModel`, not a TF1 Hub Module recipe.
2. Confirm the output directory directly contains `saved_model.pb` or `saved_model.pbtxt`.
3. Reload with `tensorflow_hub.load(export_path)`.
4. For Keras, decide whether the export is callable or signature-only before setting `KerasLayer` arguments.
5. For text embeddings, validate a tiny subset with `--verify` before exporting a large file.

## When to stop and ask for more context

Stop before continuing if the task requires:

- a legacy TF1 TensorFlow Hub Module artifact rather than a TF2 `SavedModel`;
- credentials, private model repositories, or restricted Kaggle/Cloud access;
- a large model download, benchmark, or training run not explicitly approved;
- a GPU-only model workflow where CPU behavior is not an acceptable substitute.
