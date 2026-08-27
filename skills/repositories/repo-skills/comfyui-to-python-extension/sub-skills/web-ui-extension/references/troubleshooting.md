# Web UI Extension Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Save As Script` never appears | The repository is not in a ComfyUI custom-node search path. | Clone or symlink it into `ComfyUI/custom_nodes`, or add the parent path through `extra_model_paths.yaml`, then restart ComfyUI. |
| The menu item appears only after a hard refresh | The frontend loaded stale assets. | Restart ComfyUI and refresh the browser. |
| `/saveasscript` returns a server error | The extension route raised an exception or the ComfyUI runtime is missing a dependency. | Check the ComfyUI console logs and make sure the extension dependencies are installed in the same interpreter ComfyUI uses. |
| The browser downloads `workflow_api.py` when you wanted another name | The UI path uses a fixed default filename. | Rename the downloaded file after the export completes. |
| `ImportError` from the repository root extension | The ComfyUI runtime is missing `black` or another required dependency. | Install the dependencies in the ComfyUI runtime environment and restart. |
| ComfyUI cannot load the extension on Windows portable builds | The repository was installed with the wrong Python. | Use the embedded portable Python that ships with ComfyUI. |

## Native checks that match these problems

- `tests/test_project_contracts.py`
- `tests/test_upscale_model_loader_export.py`
