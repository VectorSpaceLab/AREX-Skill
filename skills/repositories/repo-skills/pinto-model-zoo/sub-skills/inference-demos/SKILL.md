---
name: inference-demos
description: "Plan and troubleshoot PINTO_model_zoo inference/demo scripts
  without blindly running hardware- or network-heavy examples."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference Demos

Use this sub-skill when a user wants to understand, plan, or troubleshoot a selected PINTO_model_zoo demo script.

## Route here for

- "run this TFLite/ONNX/OpenVINO demo"
- "what runtime deps do I need for this script?"
- "can I turn this webcam sample into a deterministic CI fixture?"
- "the model file, label file, or test image is missing"
- "the script imports OpenCV, onnxruntime, tensorflow, openvino, tfjs, or edge hardware helpers"

If the request is really about fetching artifacts, route to `../model-acquisition/`.
If it is about conversion, quantization, or export, route to `../conversion-and-deployment/`.
If the user has not chosen a model folder yet, start from the bundled catalog at `../../references/model-catalog.json`.

## Operating pattern

1. Classify the script with `scripts/classify_runtime_script.py`.
2. Read the script's `--help`, default model path, and nearby asset names before planning execution.
3. Separate the inference backend from the input/output wrapper:
   - inference backend: TensorFlow/TFLite, ONNX Runtime, OpenVINO, TFJS/browser, or a closely related wrapper path;
   - wrapper/support: OpenCV camera/video, MediaPipe, Raspberry Pi/edge, or accelerator-specific flags.
4. Preflight local assets and optional dependencies before any runtime claim.
5. Replace live camera/video inputs with a fixed image, pinned clip, or saved frame set when possible.
6. Stop and hand off instead of guessing when the selected backend, artifact, or hardware is unavailable.

## What this skill returns

- backend family and the import/file clues behind it
- likely model file extensions and other asset types
- missing model, label, image, or video fixtures
- camera/video/display or edge-hardware risks
- a deterministic fixture plan when live input is unnecessary
- the next owner when this is really an acquisition or conversion task

## Owned failure modes

- missing or mismatched model/test assets
- webcam or video demos that fail in CI or headless environments
- import errors for optional backend runtimes
- browser/TFJS samples that are not Python-runnable
- Raspberry Pi / EdgeTPU / Myriad / CUDA / TensorRT paths that need concrete hardware
- scripts that are actually conversion/export helpers in disguise

## Bundled resources

- `references/inference-workflows.md`
- `references/runtime-dependencies.md`
- `references/troubleshooting.md`
- `scripts/classify_runtime_script.py`

This sub-skill plans inference/demo work. It does not claim native backend verification in Creator.
