---
name: web-demo
description: "Routes DreamOmni2 Gradio demo launchers for editing and generation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DreamOmni2 web demo

Use this sub-skill when the user wants to launch the DreamOmni2 browser UI instead of the one-shot CLI scripts.

## Typical triggers
- "launch the DreamOmni2 demo"
- "start the Gradio app"
- "run the editing web UI"
- "run the generation web UI"
- "what port does the demo use?"

## What belongs here
- The editing Gradio launcher
- The generation Gradio launcher
- Port, host, and browser-access troubleshooting
- UI-specific input-order guidance and demo startup checks

## What does not belong here
- One-shot command-line inference; use `sub-skills/inference/`
- Training or fine-tuning helpers
- Generic Gradio applications that are not DreamOmni2-specific

## Read these files first
- `references/workflows.md` for the launch commands and UI behavior
- `references/troubleshooting.md` for port, browser, model-load, and upload failures
- `../../references/model-setup.md` for the expected model directories
- `../../scripts/dreamomni2_common.py` for the shared model and prompt helpers used by the launchers

## Bundled scripts
- `scripts/web_edit.py` for the editing UI
- `scripts/web_generate.py` for the generation UI

## Workflow outline
1. Confirm which UI mode is needed: editing or generation.
2. Confirm the model paths and that the CUDA environment is ready.
3. Launch the chosen script with the desired host and port.
4. Open the browser, upload two images, and enter the instruction.
5. If the result is wrong, check the image order and the model-path configuration before touching the UI code.

## Decision points
- **Port selection**: the bundled launchers default to 7860 for editing and 7861 for generation, but both accept overrides.
- **Input order**: the editing UI still expects the source image first.
- **Examples**: the bundled launchers are intentionally not tied to the source checkout's sample images, so users should upload their own images or add local examples of their own.

## If you need more detail
Read the linked reference files when you need exact launch options, browser recovery steps, or a model-path check before starting the app.
