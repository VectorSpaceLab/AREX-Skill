# Install and Setup

## Shared prerequisites

- Python 3.12 or newer.
- `black` available in the interpreter that will execute the exporter or load the extension.
- A ComfyUI checkout when you want the extension or generated scripts to resolve ComfyUI modules at runtime.

## CLI export path

Use this path when you want to convert an API-format workflow into Python.

1. Keep the repository as a source checkout.
2. Install the runtime dependency set for the environment you will actually use.
3. Run the CLI from that environment:

```bash
python -m comfyui_to_python --help
python -m comfyui_to_python -f workflow_api.json -o workflow_api.py
```

If ComfyUI is not already discoverable from the current working directory, set `COMFYUI_PATH` to the ComfyUI checkout before running exported scripts.

## Web UI extension path

Use this path when you want the `File -> Save As Script` menu item inside ComfyUI.

1. Make this repository discoverable to ComfyUI through `custom_nodes`.
2. Choose one of the documented discovery patterns:
   - clone directly into `ComfyUI/custom_nodes`
   - symlink the repository into `ComfyUI/custom_nodes`
   - add the repository parent to `extra_model_paths.yaml`
3. Install the dependencies into the same Python interpreter that launches ComfyUI.
4. Restart ComfyUI so the extension is loaded.

## Important runtime note

A local environment created only for this repository does not automatically become the interpreter that ComfyUI uses. When the extension or a generated script needs ComfyUI modules, install or run it in the ComfyUI runtime environment itself.

## About editable installs

The repository is used as a source checkout, not as a conventional installable package project. If a direct editable install fails, do not treat that as a blocker for the normal workflows; use the checkout plus the documented ComfyUI runtime instead.
