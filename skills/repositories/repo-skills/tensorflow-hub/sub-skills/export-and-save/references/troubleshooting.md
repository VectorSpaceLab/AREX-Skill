# Export and save troubleshooting

Use this matrix for TF2 `SavedModel` export failures, text embedding exporter failures, and validation errors with `tensorflow_hub.load` or `tensorflow_hub.KerasLayer`.

| Symptom or error fragment | Likely cause | Action |
| --- | --- | --- |
| `Inconsistent embedding dimension detected` | At least one token/vector row has a different number of numeric columns. | Normalize the embedding file so every usable row has the same dimension. If there is a metadata header, skip it with `--num-lines-to-ignore`. |
| `line ... has no vector values` or float parsing fails | A blank line, header line, token-only row, or non-numeric vector column was parsed as an embedding row. | Remove or skip non-embedding lines. Keep one token followed by floats on every usable line. |
| `no usable embedding rows` | `--num-lines-to-ignore` skipped all rows, `--num-lines-to-use` is too restrictive, or the file is empty. | Reduce skipped lines, increase the row limit, or provide a non-empty embedding file. |
| Exported unknown or empty text returns all zeros | Default OOV vectors are zero and empty strings are intentionally filled then reduced to zero. | Treat this as expected for OOV-only and empty inputs. If trainable nonzero OOV behavior is needed, fine-tune after export or customize the OOV initialization. |
| Known+unknown sentence magnitude seems lower than expected | Unknown tokens contribute zero vectors but can still affect the `sqrtn` combiner denominator. | Verify with known single-token calls, then account for `sqrtn` normalization in multi-token expectations. |
| Output path exists and contains files | The bundled exporter refuses to overwrite non-empty directories. | Choose a fresh export path or intentionally remove the existing directory before running. |
| `contains neither 'saved_model.pb' nor 'saved_model.pbtxt'` | Validation pointed at the wrong directory, an incomplete export, or a directory above/below the actual `SavedModel`. | Point `tensorflow_hub.load` at the directory that directly contains `saved_model.pb` or `saved_model.pbtxt`. Re-export if the file is missing. |
| `Loaded object is not callable and has no signatures` | The SavedModel did not export a callable `__call__` and has no usable signatures. | Add an `@tf.function` callable or pass explicit signatures to `tf.saved_model.save`. |
| `Signature name has to be specified for non-callable saved models` | `KerasLayer(handle)` was used on a signature-only SavedModel. | Use `KerasLayer(handle, signature="serving_default", output_key="...")` or export a callable `__call__`. |
| `When using a signature, either output_key or signature_outputs_as_dict=True should be set` | `KerasLayer` was given `signature=...` without choosing dict output behavior. | Set exactly one of `output_key="name"` or `signature_outputs_as_dict=True`. |
| `KerasLayer output does not contain the output key ...` | The selected output key does not match the signature output dict. | Inspect `hub.load(path).signatures[name].structured_outputs` and use an available key. |
| `Setting hub.KerasLayer.trainable = True is unsupported when calling a SavedModel signature` | Signature calls do not expose trainable behavior through `KerasLayer`. | Export a callable TF2 SavedModel with tracked variables if trainable Keras wrapping is required. |
| `Asset filename ... points outside assets_dir` or validation works only on the construction machine | The model captured an asset path incorrectly or did not track the asset for export. | Track files with `tf.saved_model.Asset` or TensorFlow lookup-table initializer attributes; validate after the source asset file outside the SavedModel is unavailable. |
| `AttributeError: module 'tensorflow_hub' has no attribute 'Module'` | Code is using legacy TF1 TensorFlow Hub Module APIs absent from this package. | Use TF2 `SavedModel` export guidance here, or stop and request an archived older environment if a TF1 Module artifact is mandatory. |
| `AttributeError` for `create_module_spec`, `load_module_spec`, `add_signature`, or `attach_message` | Same legacy TF1 publisher mismatch. | Do not add those calls to current recipes. Migrate to `tf.saved_model.save` and explicit TF2 signatures. |
| Top-level `hub.text_embedding_column_v2` or `hub.feature_column_v2` is missing after `import tensorflow_hub as hub` | Feature column helpers are not exposed as top-level attributes in this checkout. | Import the submodule directly in loading/feature-column tasks; export tasks should still write plain `SavedModel`s. |

## Triage sequence

1. Confirm whether the task is current TF2 export or legacy TF1 TensorFlow Hub Module reproduction.
2. For text embeddings, run the bundled exporter with `--verify` on a tiny subset before exporting a large file.
3. Check the export directory for `saved_model.pb` or `saved_model.pbtxt`.
4. Reload with `tensorflow_hub.load(export_path)` and call either the loaded object or the intended signature.
5. If `KerasLayer` is involved, decide whether the SavedModel is callable or signature-only, then set `signature`, `output_key`, `signature_outputs_as_dict`, `input_shape`, `dtype`, and `output_shape` consistently.
6. If assets are involved, move or hide the original asset source files and validate that the SavedModel still works from its own packaged assets.

## Quick text embedding sanity fixture

Use a three-row embedding file for smoke checks:

```text
cat 1.11 2.56 3.45
dog 1.0 2.0 3.0
mouse 0.5 0.1 0.6
```

Expected checks with one OOV bucket:

- `"cat"` returns approximately `[1.11, 2.56, 3.45]`.
- `"cat cat"` returns approximately `sqrt(2)` times the `cat` vector.
- `"lizard. dog"` removes punctuation, treats `lizard` as OOV, and combines with `dog` under `sqrtn`.
- `""` returns `[0.0, 0.0, 0.0]`.
