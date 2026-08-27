# Troubleshooting

| Symptom | Likely cause | Recovery | Stop condition |
| --- | --- | --- | --- |
| `InputMode.TENSORFLOW is deprecated` | The Spark ML pipeline API is SPARK-only. | Keep `TFEstimator`/`TFModel` on `InputMode.SPARK`; route queue semantics to the sibling skill instead. | The pipeline never calls `setInputMode(TENSORFLOW)`. |
| Training sees the wrong columns or tensors | The mapping dict keys do not match the DataFrame columns, or you expected insertion order. | Verify `setInputMapping(...)`; remember training input columns are selected in lexicographic order by DataFrame column name. | A small batch reaches `train_fn` with the intended tensors. |
| Output columns come back in a surprising order | `output_mapping` is sorted by tensor name, not insertion order. | Rename tensors or reorder columns downstream after `transform()`. | `preds.columns` matches the intended schema. |
| `Inferencing requires either --model_dir or --export_dir argument` | Inference path lacks a checkpoint or SavedModel. | Set the correct artifact path. | `transform()` opens the artifact. |
| `Inferencing from a saved_model requires --tag_set` or `Inferencing with signature_def_key requires --export_dir argument` | SavedModel fields are incomplete. | Set `export_dir`, `tag_set`, and `signature_def_key` together. | SavedModel loads by tag and signature. |
| `KeyError` for `serving_default` or a missing output tensor | The exported signature name or tensor names do not match the mapping. | Inspect the SavedModel signatures and align `signature_def_key` and `output_mapping` with the loaded signature. | A one-row batch transforms and returns the expected columns. |
| `Please use native TF2.x APIs to export a saved_model.` | `TFEstimator(export_fn=...)` is used on TF2. | Export inside your TF2 training code or with `compat.export_saved_model`. | A TF2 SavedModel appears in the export directory. |
| `Output array sizes ... must match input size` or reshape assertions fail | The model emits the wrong number of rows or expects shaped tensors, while Spark passes flat arrays. | Ensure one output row per input row and reshape inputs to the signature shape before inference. | A sample partition transforms cleanly. |
| SavedModel seems stale or reloads unexpectedly | The Python worker cache stores one model/session per args object. | Keep args stable for a given artifact; restart the job if you need a fresh model. | New partitions reuse the intended cached model. |
| Export directory is missing after a successful train | `grace_secs` was too short, or export only ran on the wrong node. | Raise `grace_secs` and ensure only the chief exports the SavedModel. | The export leaf contains `saved_model.pb` or checkpoint files. |
