# Troubleshooting

## Shared issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'black'` | The runtime that executes the exporter or extension is missing `black`. | Install `black` into the same interpreter that loads the extension or runs the exporter. |
| `ComfyUI path not found` | `COMFYUI_PATH` is unset and no parent directory contains a `ComfyUI` folder. | Set `COMFYUI_PATH` or run from a checkout layout where ComfyUI is discoverable. |
| Generated script fails with `No module named 'torch'` | The exported script is being run in the wrong Python environment. | Use the same Python interpreter that launches ComfyUI, or install ComfyUI runtime dependencies into the target environment. |
| `Save As Script` is missing from the UI | The extension is not discoverable through `custom_nodes`, or ComfyUI has not been restarted. | Put the repository in `ComfyUI/custom_nodes`, symlink it there, or add the parent path in `extra_model_paths.yaml`, then restart ComfyUI. |
| `pip install -e .` fails with flat-layout package discovery | The repository is being treated like a conventional installable package, but the normal workflow is a source checkout plus the documented runtime environment. | Do not force editable install as the primary path; use the source checkout and the target runtime interpreter instead. |
| `workflow_api.py` downloads with the wrong name | The browser export uses a fixed default filename. | Rename the downloaded file after saving if you need a different local filename. |

## When to escalate to a sub-skill

- If the problem is about CLI flags, generated code shape, node ordering, runtime cleanup, or custom-node import inside exported scripts, go to `sub-skills/cli-export/troubleshooting.md`.
- If the problem is about ComfyUI discovery, browser menu visibility, the `/saveasscript` route, or custom-node installation, go to `sub-skills/web-ui-extension/troubleshooting.md`.
