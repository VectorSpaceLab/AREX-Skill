---
name: cli-export
description: "Export ComfyUI API workflows to Python and troubleshoot the
  generated script runtime."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CLI Export and Generated Script Runtime

Use this sub-skill when the task is about converting `workflow_api.json` into Python or understanding the standalone script that the exporter produces.

## Typical user requests

- Convert an exported ComfyUI workflow to a Python script.
- Run the exporter from the command line.
- Explain or debug the generated Python file.
- Check why a generated script cannot find ComfyUI, `torch`, or a model file.
- Understand how node ordering, seed sync, cleanup, or custom-node loading works.
- Create or run a small export smoke test.

## What this sub-skill owns

- `comfyui_to_python/` package behavior.
- The CLI parser and `python -m comfyui_to_python` entry point.
- Generated script layout, bootstrap, cleanup, and queue execution.
- Workflow loading, load-order planning, and renderer output.
- Generated-script troubleshooting for `COMFYUI_PATH`, `torch`, `black`, custom nodes, and model/runtime issues.

## What this sub-skill excludes

- Installing the repo as a ComfyUI custom node.
- The browser `File -> Save As Script` button and `/saveasscript` route.
- Frontend menu behavior or ComfyUI discovery mechanics beyond what the exporter needs at runtime.

## Read these first

- [`references/cli-reference.md`](references/cli-reference.md) for commands, flags, and defaults.
- [`references/generated-script-runtime.md`](references/generated-script-runtime.md) for the structure and runtime behavior of exported Python.
- [`references/troubleshooting.md`](references/troubleshooting.md) for exporter and generated-script failure modes.
- [`scripts/export_smoke.py`](scripts/export_smoke.py) for a fast end-to-end smoke check with a tiny workflow.

## Workflow

1. Confirm that the user has an API-format workflow or wants the exporter to produce one.
2. Use the CLI when the user wants a file-based export, or use `ComfyUItoPython(...)` programmatically when they are scripting the export.
3. If ComfyUI is not already discoverable, set `COMFYUI_PATH` before running the exported Python.
4. Make sure `black` is available in the runtime that renders the script.
5. If the user needs the generated script to unload models after each run, explain `COMFYUI_TOPYTHON_UNLOAD_MODELS=1` or `main(unload_models=True)`.
6. Use the smoke script for quick validation before you move to heavier runtime checks.

## Routing hints

Choose this sub-skill when you see any of these signals:

- `workflow_api.json`
- `workflow_api.py`
- `python -m comfyui_to_python`
- `comfyui_to_python.py`
- `--input_file`, `--output_file`, or `--queue_size`
- `COMFYUI_PATH`
- `No module named 'torch'`
- `custom node` import errors during generated-script execution
- `cleanup_comfyui_runtime`
- `bootstrap_comfyui_runtime`
- `File -> Export (API)`

## What the generated script does

The exported Python is a standalone workflow runner, not a generic API service.
It:

- embeds the workflow and optional frontend metadata
- bootstraps ComfyUI before importing `torch`
- loads ComfyUI model paths and custom nodes when needed
- executes the workflow in a bounded queue loop
- performs best-effort cleanup in a `finally` block

## Success criteria

A future agent should be able to:

- export a workflow to a Python file,
- understand the key sections in the generated source,
- explain why the script needs a ComfyUI runtime,
- and diagnose the common runtime failures without reopening the original repository.
