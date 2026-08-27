---
name: demo-and-model-setup
description: "Prepares InfiniteYou model files and operates the self-contained
  Gradio demo launcher safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Demo and Model Setup

Use this sub-skill when the request is about preparing, checking, or launching the local InfiniteYou demo environment. The generated skill includes a self-contained Gradio launcher that uses the bundled runtime instead of the original demo source file.

## Routes covered

- Expected model tree, download behavior, base-model access, and the layout validator: [references/model-layout-and-downloads.md](references/model-layout-and-downloads.md) and [scripts/check_model_layout.py](scripts/check_model_layout.py)
- Gradio controls, defaults, model switching, cache behavior, and launch cautions: [references/gradio-demo.md](references/gradio-demo.md)
- Self-contained demo preflight/launch entry point: [scripts/launch_infinite_you_gradio.py](scripts/launch_infinite_you_gradio.py)
- Failure modes and recovery tips: [references/troubleshooting.md](references/troubleshooting.md)

## Use this sub-skill for

- confirming the InfiniteYou model directory before a demo run
- understanding which files must exist locally
- preparing InsightFace support assets or optional LoRAs
- checking how the demo chooses and swaps model variants
- launching a private localhost Gradio UI from the generated skill runtime
- reasoning about the demo queue, model caching, server binding, and memory behavior

## Fast preflight

```bash
python scripts/launch_infinite_you_gradio.py --check-only \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev
```

Launch only after preflight passes and model/license/CUDA requirements are satisfied:

```bash
python scripts/launch_infinite_you_gradio.py \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev \
  --server-name localhost
```

Use `--allow-downloads` or `--share` only after explicit user approval.

## Do not use this sub-skill for

- CLI generation recipes or batch inference commands; use local-inference instead
- pipeline internals or code-level changes to the model stack; use pipeline-internals instead

## Safety notes

- The bundled validators and demo preflight never download models.
- The self-contained launcher defaults to local model paths and localhost binding.
- Treat the demo launcher as a runtime entry point, not as a source module to import.
- If the demo or validator reports missing model files, fix the local layout first; do not rely on startup to fetch everything implicitly unless `--allow-downloads` was explicitly approved.
