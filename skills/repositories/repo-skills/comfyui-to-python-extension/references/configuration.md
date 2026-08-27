# Configuration and Defaults

## Environment variables

| Variable | Used by | Meaning | Default / fallback |
| --- | --- | --- | --- |
| `COMFYUI_PATH` | exporter and generated scripts | Explicit path to the ComfyUI checkout | Search parent directories for a folder named `ComfyUI` |
| `COMFYUI_TOPYTHON_UNLOAD_MODELS` | generated scripts | Truthy flag to unload models during cleanup | `false` unless set to `1`, `true`, `yes`, or `on` |

## CLI defaults

| Setting | Value | Source |
| --- | --- | --- |
| Input workflow file | `workflow_api.json` | `comfyui_to_python.cli.DEFAULT_INPUT_FILE` |
| Output Python file | `workflow_api.py` | `comfyui_to_python.cli.DEFAULT_OUTPUT_FILE` |
| Queue size | `10` | `comfyui_to_python.cli.DEFAULT_QUEUE_SIZE` |

## Web UI defaults

| Setting | Value | Source |
| --- | --- | --- |
| Browser command | `File -> Save As Script` | `js/save-as-script.js` |
| Download filename | `workflow_api.py` | `js/save-as-script.js` |
| Workflow name sent to the server | `workflow_api.json` | `js/save-as-script.js` |
| Extension directory hint | `js` | repo root `__init__.py` |
| Server route | `/saveasscript` | repo root `__init__.py` |

## Runtime behavior to keep in mind

- The CLI exporter can infer ComfyUI from `COMFYUI_PATH` or from a parent directory lookup.
- Generated scripts import `torch` only at execution time, after the runtime bootstrap has added the ComfyUI checkout to `sys.path`.
- The browser-side save flow always uses the fixed default filename; it does not prompt for a custom save name.
