# Pipeline Troubleshooting

| Symptom | Likely cause | Recovery | Next step |
| --- | --- | --- | --- |
| Unknown app name | The request does not match the `SUPPORTED_APPS` registry. | Choose one of `dataset-stats`, `dataset-visual`, `generate-emb`, `oagbert`, or `recommendation`. | If the task sounds similar but not exact, route back to the experiment or data sub-skill. |
| A dataset-stats or dataset-visual call downloads data | Built-in datasets are cache/network dependent. | Use a custom fixture or get explicit approval for cache/network writes. | Do not claim an offline run if the dataset is missing. |
| `dataset-visual` produces no file | The visualizer writes a PNG in the current working directory, and the path may not be writable. | Choose a writable directory or confirm the script's save location. | Keep the file-write surface explicit in your answer. |
| `generate-emb` says a feature width is needed | The selected embedding path is a GNN-style model that expects `num_features` when `x` is omitted. | Use an embedding model like `prone` for the safe smoke path or supply features for the GNN path. | If the user wanted only a no-download smoke, stay with the embedding-model route. |
| `Please provide recommendation data!` | The recommendation pipeline was called without a custom NumPy array or built-in dataset. | Pass a 2D interaction array or a supported recommendation dataset. | The recommendation sub-skill should explain the expected shape before any run starts. |
| OAG-BERT archive/unpack failure | The model archive is remote, missing, or incomplete. | Treat the model as optional, verify the cache or download URL, and stop if the environment cannot fetch the archive. | Keep the failure visible instead of pretending the model loaded. |
| `transformers` or `sentencepiece` import errors | The optional OAG-BERT dependency stack is incomplete. | Install the missing package only when the user actually wants OAG-BERT. | Otherwise leave OAG as an optional capability. |
| `generate-emb` with a built-in dataset pulls data | The app path is using the repository's normal dataset loader. | Prefer the bundled tiny edge-list smoke or a custom fixture when no network is allowed. | Keep the app on the safe path. |
| `mvgrl` or another training-backed embedding path fails with `module 'numpy' has no attribute 'int'` | Older CogDL preprocessing code still uses the removed `np.int` alias. | Prefer the bundled `prone` smoke path for no-download checks, or pin `numpy<1.24` / apply a compatibility patch if you truly need the older embedding model. | Treat the failure as a version-compatibility issue rather than a data bug. |

## Recovery order

1. Confirm the app name.
2. Confirm whether the workflow is dataset-backed or no-download.
3. Confirm the output location for image or embedding artifacts.
4. Confirm whether OAG-BERT is really required.
5. Only then choose the pipeline call or stop with a network/cache note.
