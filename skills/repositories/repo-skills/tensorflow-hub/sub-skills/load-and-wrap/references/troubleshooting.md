# Troubleshooting

Use this matrix when a load, resolve, wrap, or feature-column workflow fails.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: No module named tensorflow` | TensorFlow is not installed in the current environment | Install TensorFlow that matches the intended Hub workflow, then retry the smoke script. |
| `ImportError: No module named tf_keras` | The environment is using Keras 3 but the compatibility package is missing | Install `tf_keras` that matches TensorFlow, then rebuild the surrounding Keras model with `tf_keras` if needed. |
| `DeprecationWarning` or warning text about `pkg_resources` | The package imports `pkg_resources`, which depends on a setuptools version that still provides it | Use a setuptools version that still includes `pkg_resources`. The warning is not a Hub API failure by itself. |
| `ValueError: Expected a string, got ...` from `hub.load` | A non-string handle was passed to a string-handle API | Pass a string path or handle to `hub.load` / `hub.resolve`. Use a callable object only with `hub.KerasLayer`. |
| `IOError: ... does not exist.` | The local path or mounted filesystem path is wrong | Fix the path, permissions, or mount, then try again. |
| `ValueError: Trying to load a model of incompatible/unknown type...` | The target directory is not a SavedModel directory | Ensure the directory contains a valid SavedModel layout, including `saved_model.pb` or `saved_model.pbtxt`. |
| `IOError: ... does not appear to be a valid module.` | The archive is corrupt, truncated, or not actually a Hub-compatible module archive | Re-export the archive or point the handle at the correct SavedModel source. |
| Resolver waits on a `.lock` file for a long time | Another process is downloading the same cached module, or a previous download was interrupted | Use a writable temporary cache directory, wait for the other process, or clear only the stale cache after verifying no process still owns it. |
| HTTPS certificate validation fails | The endpoint uses a test certificate or a private trust chain | For trusted test endpoints only, set `TFHUB_DISABLE_CERT_VALIDATION=true`. Unset it for normal public URLs. |
| `UNCOMPRESSED` mode fails against a normal archive URL | The server is not returning a `303` redirect to a `gs://...` target | Switch back to `AUTO` or `COMPRESSED`, or use a server that explicitly serves the uncompressed redirect protocol. |
| `When using a signature, either output_key or signature_outputs_as_dict=True should be set.` | A signature was selected without output selection | Set exactly one of `output_key` or `signature_outputs_as_dict=True`. |
| `signature_outputs_as_dict is only valid if specifying a signature` | The dict-output flag was set without a signature | Add a signature or remove the flag. |
| `Specifying output_key is forbidden if output type ... is not a dict` | `output_key` was set for a non-dict output | Remove `output_key` or export a dict-valued signature. |
| `KerasLayer output does not contain the output key ...` | The selected key does not exist in the signature output dict | Choose the correct key or export a matching signature. |
| `Setting hub.KerasLayer.trainable = True is unsupported when calling a SavedModel signature.` | The export is being trained through a signature path | Export a callable `__call__` path instead, or keep the layer non-trainable. |
| `hub.KerasLayer is trainable but has zero trainable weights.` | The export did not expose trainable variables | Expose trainable variables in the exported callable, or leave the layer frozen. |
| `Loaded object is not callable and has no signatures.` | The SavedModel export did not provide a callable `__call__` or a named signature | Re-export with a callable `__call__` or pass the correct signature name. |
| `AttributeError: module tensorflow_hub has no attribute text_embedding_column_v2` | The feature-column helper was imported from the wrong place | Switch to `import tensorflow_hub.feature_column_v2 as hub_feature_column_v2`. |

If the failure still is not clear, read [keras-layer.md](keras-layer.md) or [feature-column-v2.md](feature-column-v2.md) for the workflow-specific rules.
