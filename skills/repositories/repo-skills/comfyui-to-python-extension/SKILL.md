---
name: comfyui-to-python-extension
description: "Route ComfyUI Save As Script and workflow export tasks into the
  CLI and Web UI sub-skills."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# ComfyUI-to-Python Extension

Use this router for the repository that turns ComfyUI node graphs into runnable Python and adds the in-UI **Save As Script** extension command.

## Start here

- Read [`references/install-and-setup.md`](references/install-and-setup.md) when the user asks how to install, expose, or run the extension.
- Read [`references/api-reference.md`](references/api-reference.md) when you need exact public class, function, or module names.
- Read [`references/configuration.md`](references/configuration.md) when the question is about `COMFYUI_PATH`, default filenames, queue size, or generated-script runtime switches.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for shared failure modes before you route into a sub-skill.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) if you need to check freshness or source state.
- Read [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) if you need the router placement metadata for import.

## Route to `cli-export`

Go to [`sub-skills/cli-export/SKILL.md`](sub-skills/cli-export/SKILL.md) when the task is about any of these:

- converting `workflow_api.json` or another API-format workflow into Python
- running `python -m comfyui_to_python` or the legacy `comfyui_to_python.py` wrapper
- choosing `--input_file`, `--output_file`, or `--queue_size`
- understanding the generated script layout, bootstrap, cleanup, or seed handling
- running exported Python with ComfyUI, `torch`, or model files
- debugging `COMFYUI_PATH`, `No module named 'torch'`, custom-node import, or generated-script runtime failures
- smoke-testing export behavior with a tiny workflow

## Route to `web-ui-extension`

Go to [`sub-skills/web-ui-extension/SKILL.md`](sub-skills/web-ui-extension/SKILL.md) when the task is about any of these:

- installing the repo as a ComfyUI custom node
- making **File -> Save As Script** appear in the ComfyUI UI
- understanding `__init__.py`, the `/saveasscript` route, or the frontend menu command
- using `extra_model_paths.yaml`, symlinks, or `ComfyUI/custom_nodes` discovery
- diagnosing why the extension does not show up after restart
- the browser-side download flow and the default `workflow_api.py` filename

## Shared facts

- The project targets Python 3.12+.
- `black` is required by the exporter path.
- `COMFYUI_PATH` is the primary runtime locator when ComfyUI is not already discoverable from the current working directory.
- Generated scripts still need a real ComfyUI runtime, not just this repository checkout.

## Working rules

- Keep generated guidance self-contained. Use the bundled references and scripts under this skill tree instead of pointing back to the source checkout.
- Prefer the narrowest sub-skill that matches the request.
- If the user mixes UI installation and CLI export concerns, answer from the more specific route first and cross-reference the other route only when needed.
