# Install and Discovery

The Web UI path turns this repository into a ComfyUI custom node.

## Discovery patterns

ComfyUI must be able to see the repository through one of its custom-node search paths:

- clone the repository directly into `ComfyUI/custom_nodes`
- symlink the repository into `ComfyUI/custom_nodes`
- add the repository parent directory to `extra_model_paths.yaml`

## Install flow

1. Make the repository discoverable to ComfyUI.
2. Install the extension dependencies into the same Python interpreter that launches ComfyUI.
3. Restart ComfyUI.
4. Open the **File** menu and choose **Save As Script**.

## What the browser button does

- The frontend command is registered as a ComfyUI menu action.
- It sends the current workflow and frontend metadata to the `/saveasscript` route.
- The server returns generated Python as text.
- The browser downloads that response as `workflow_api.py`.

## Windows portable note

For the portable build, install the extension with the embedded Python that ships with ComfyUI, not with an unrelated interpreter.

## Practical checks

- `__init__.py` exists in the repository root.
- `js/save-as-script.js` exists and loads as the frontend extension.
- ComfyUI has been restarted after installing or linking the repository.
- The browser is looking under the **File** menu, not another menu location.
