---
name: web-ui-extension
description: "Install and troubleshoot the ComfyUI Save As Script extension."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Web UI Extension

Use this sub-skill when the task is about making **File -> Save As Script** appear inside ComfyUI or understanding the browser-side export route.

## Typical user requests

- Install the repository as a ComfyUI custom node.
- Make the Save As Script menu item appear after restarting ComfyUI.
- Explain how the browser export button works.
- Diagnose why `/saveasscript` or the extension route fails.
- Understand how `__init__.py` and `js/save-as-script.js` cooperate.
- Verify that the extension is discoverable through `custom_nodes`.

## What this sub-skill owns

- The repo root extension entrypoint in `__init__.py`.
- The frontend asset in `js/save-as-script.js`.
- ComfyUI discovery patterns and install placement.
- Browser-side default filename behavior.
- Extension-specific troubleshooting and restart guidance.

## What this sub-skill excludes

- CLI export flags and generated-script runtime details.
- Node ordering, seed handling, or `torch` bootstrap in exported Python.
- Generic ComfyUI model-serving or diffusion workflows unrelated to this extension.

## Read these first

- [`references/install-and-discovery.md`](references/install-and-discovery.md) for installation and browser flow.
- [`references/troubleshooting.md`](references/troubleshooting.md) for extension-specific failures.
- [`scripts/check_discovery.py`](scripts/check_discovery.py) for a quick layout check when you want to confirm the repo is discoverable.

## Workflow

1. Confirm that the user wants the in-UI export path rather than the CLI exporter.
2. Place the repository where ComfyUI can discover it through `custom_nodes` or an external path configuration.
3. Install the dependencies into the interpreter that launches ComfyUI.
4. Restart ComfyUI and look for **File -> Save As Script**.
5. If the menu item is present but the request fails, inspect the `/saveasscript` route and extension logs.

## Routing hints

Choose this sub-skill when you see any of these signals:

- `Save As Script`
- `File -> Save As Script`
- `custom_nodes`
- `extra_model_paths.yaml`
- `/saveasscript`
- `WEB_DIRECTORY`
- `workflow_api.py` as the browser download filename
- `ComfyUI` extension install or restart issues

## Success criteria

A future agent should be able to:

- explain where the repository must live for ComfyUI to load it,
- describe the browser command and the POST payload shape,
- and troubleshoot why the extension is not visible or the route does not respond.
