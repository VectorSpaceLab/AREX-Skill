---
name: gradio-inference-apps
description: "Choose, inspect, configure, and safely adapt ControlNet 1.0 Gradio
  inference apps without importing launch scripts unless the user is
  intentionally running a prepared app."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ControlNet Gradio Inference Apps

Use this sub-skill when a user asks to run, compare, inspect, debug, or adapt a ControlNet 1.0 Gradio app such as Canny, M-LSD/Hough, HED, scribble, interactive scribble, fake scribble, pose, segmentation, depth, or normal-map image generation.

## Route The Request

- For app selection, process signatures, Gradio controls, checkpoint names, detector thresholds, output list conventions, and DDIM arguments, read [references/app-parameter-reference.md](references/app-parameter-reference.md).
- For a safe end-to-end workflow that prepares model files, chooses an app, configures prompts/seed/guess mode/control strength, enables low VRAM, or adapts a `process(...)` function, read [references/inference-workflows.md](references/inference-workflows.md).
- For missing checkpoints, missing Gradio, CUDA/OOM, top-level import side effects, network downloads, nondeterministic seed behavior, and guess-mode surprises, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect app signatures and checkpoint/config string references without launching Gradio, run [scripts/extract_gradio_signatures.py](scripts/extract_gradio_signatures.py) against a ControlNet checkout.

## Quick Selection Guide

- Use Canny for crisp edges and threshold tuning; use M-LSD/Hough for straight architectural or room lines; use HED for soft boundaries and stylization/recoloring.
- Use scribble or interactive scribble for user-drawn sparse controls; use fake scribble when the user wants scribble-like controls synthesized from an image.
- Use pose for human body layout from an input image; use segmentation for ADE20K-style scene layout; use depth or normal map when the user wants geometry preservation.
- Prefer normal map over depth when fine surface orientation matters; prefer depth when coarse scene layout and relative distance are enough.

## Safety Boundaries

- Do not import `gradio_*2image.py` just to inspect metadata: those scripts create models, load checkpoints, move models to CUDA, instantiate samplers/detectors, and launch a server at module top level.
- Do not instantiate detectors, load checkpoints, start Gradio servers, download Hugging Face assets, or generate images from bundled scripts in this sub-skill.
- For detector-only preprocessing details, route to [../annotators-and-preprocessing/SKILL.md](../annotators-and-preprocessing/SKILL.md).
- For checkpoint conversion, config internals, and weight utilities, route to [../model-and-weight-utilities/SKILL.md](../model-and-weight-utilities/SKILL.md).
- For training, fine-tuning, data preparation, or dataset debugging, route to [../training-and-datasets/SKILL.md](../training-and-datasets/SKILL.md).
