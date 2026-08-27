---
name: load-and-wrap
description: "Resolve TensorFlow Hub handles, load or wrap SavedModels with
  KerasLayer, and use the feature-column text embedding submodule safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Load and Wrap

Use this sub-skill when the task is to inspect, resolve, or load a TensorFlow Hub handle, wrap a SavedModel with `KerasLayer`, or use the feature-column text embedding helper safely in current TensorFlow Hub workflows.

Do not use this sub-skill for exporting new SavedModels or text embedding modules. That workflow belongs to the sibling `export-and-save` route.

## Quick routing

- Read [references/api-reference.md](references/api-reference.md) for the verified public surface, import paths, and the APIs that are absent in this package version.
- Read [references/load-resolve-cache.md](references/load-resolve-cache.md) when the issue is about local paths, smart HTTP/HTTPS handles, cache location, compressed versus uncompressed model load format, locks, descriptors, or archive validation.
- Read [references/keras-layer.md](references/keras-layer.md) when the issue is about `signature`, `signature_outputs_as_dict`, `output_key`, `output_shape`, `arguments`, `load_options`, trainability, or Keras 3 / `tf_keras` compatibility.
- Read [references/feature-column-v2.md](references/feature-column-v2.md) when the issue is about `tensorflow_hub.feature_column_v2.text_embedding_column_v2`, `DenseFeatures`, parse specs, or the top-level `AttributeError` recovery path.
- Read [references/troubleshooting.md](references/troubleshooting.md) when the symptom is an import failure, handle/path failure, cache/download lock problem, corrupt archive, signature mismatch, `trainable=True` error, or feature-column import mistake.
- Run [scripts/smoke_load_and_wrap.py](scripts/smoke_load_and_wrap.py) for a local no-download sanity check. Add `--feature-column` when you also want to verify the feature-column path.

## Quick workflow

1. Decide whether the input is a local SavedModel directory, a remote handle, or an already-loaded callable object.
2. If you need to inspect or normalize a handle, call `hub.resolve(handle)` first.
3. If you need the raw loaded object, call `hub.load(handle)` on a string handle.
4. If you need a Keras layer, wrap the handle with `hub.KerasLayer(...)` and choose the right output-selection mode before training or serialization.
5. If you need text embeddings inside feature columns, import `tensorflow_hub.feature_column_v2` directly and build `DenseFeatures` around the returned column.
6. Validate the smallest possible local SavedModel with the bundled smoke script before touching any network-backed handle or large model.

## Route notes

- `hub.load` and `hub.resolve` are string-handle APIs.
- `KerasLayer` can accept either a callable object or a string handle. Use the reference doc when you need to decide which one fits the export you have.
- A SavedModel that only exposes a signature needs explicit output selection. A callable SavedModel usually does not.
- `trainable=True` is not a general fix for signatures. If a model must be fine-tuned, the export has to support that path.
- The feature-column helper is only available through the submodule import path in this package version.

## Keep in scope

- Loading and wrapping existing TensorFlow Hub assets.
- Diagnosing how the current package interprets handles, signatures, outputs, and cache settings.
- Safe feature-column consumption of text embedding SavedModels.

## Route elsewhere

- Exporting or refreshing a SavedModel, module, or embedding archive -> `export-and-save`
- Broader package install or import problems -> `references/troubleshooting.md`
- Any workflow that depends on a public symbol not listed in `references/api-reference.md`
