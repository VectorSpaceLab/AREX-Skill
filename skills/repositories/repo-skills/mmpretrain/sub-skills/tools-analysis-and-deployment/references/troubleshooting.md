# Troubleshooting

This reference collects the most common failure modes for analysis, visualization, conversion, publishing, and serving.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` for `grad-cam` | Optional CAM dependency is missing. | Install the CAM package before using CAM methods. If the environment is headless, also save the image with `--save-path`. |
| `ImportError` for `scikit-learn` | Optional t-SNE dependency is missing. | Install `scikit-learn` before running t-SNE. Reduce the number of classes or samples if the visualization is slow. |
| Plot windows never appear or the command hangs | The environment has no display server. | Use file output flags such as `--out`, `--save-path`, or `--output-dir`, and disable live display with the tool's headless option. |
| A log key cannot be found | The key is absent from the train or validation records. | Choose a key that appears in the log, or inspect the available keys before plotting. |
| `analyze_results` or `confusion_matrix` cannot resolve images or class names | The config does not match the result file, or dataset metainfo is missing. | Make sure the config uses the same dataset family as the prediction file and that class names are available in the dataset metadata. |
| `get_flops` reports unsupported or suspicious numbers | The model uses unsupported operators, or the chosen shape does not match the real input. | Treat FLOPs as an estimate, keep the input shape consistent with the model, and compare only similar models. |
| `vis_cam` cannot find a target layer | The chosen layer name does not exist in the model. | Use the preview option to list layers, then set the exact layer path. |
| `vis_cam` fails on a ViT-like backbone with a reshape error | The backbone is flattening tokens, but the command did not get the right token layout. | Enable the ViT-like mode and provide the correct extra-token count when the backbone does not expose it. |
| `publish_checkpoint` or a converter reports key mismatches | The checkpoint family does not match the target architecture. | Pick the converter that matches the source checkpoint family. If EMA keys are present, merge them only when their names line up with the base state dict. |
| A publish helper appears to overwrite a checkpoint | The target path already exists. | Use a new target path or a target directory, or set the explicit overwrite flag only when you really want to replace the file. |
| TorchServe returns connection errors or `404` | The service is not running, the wrong port is used, or the archive was not loaded. | Confirm the server is up, the archive exists in the model store, and the requested model name matches the archive name. |
| TorchServe packaging fails because the archiver is missing | The serving toolchain is not installed. | Install `torchserve` and `torch-model-archiver` before building a `.mar` archive. |
| `mmpretrain2torchserve` succeeds but inference still fails | Handler, model store, or runtime configuration mismatch. | Check the archive contents, the handler path, and the service runtime before retrying. |
| `browse_dataset` or `vis_scheduler` is too slow | The dataset is large or the browser is building the full dataset. | Limit the number of samples, provide a dataset size when possible, or run only the plot you need. |

## Safety reminders

- Never mutate the source checkpoint in place when publishing or converting.
- Prefer a new output directory or a new file name for every published artifact.
- Treat family-specific converters as format bridges, not generic checkpoint loaders.
- When a command can run without a screen, prefer saving the result instead of opening a GUI window.
