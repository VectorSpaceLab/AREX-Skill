---
name: setup-runtime
description: "Guides QualityScaler installation, launch readiness, asset
  validation, and runtime troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# setup-runtime

Use this sub-skill when the task is about getting QualityScaler ready to start, diagnosing import or launch failures, checking model and asset placement, or understanding the runtime prerequisites before image or video work begins.

## Read this when

- The app will not start.
- The source module fails to import on the current Python version.
- A dependency, model file, `ffmpeg.exe`, or `exiftool.exe` is missing.
- The AI provider is not available or the runtime only shows CPU providers.
- A preferences JSON problem prevents the GUI from loading.
- The user asks whether the repository is ready for the Windows DirectML path.

## What this sub-skill owns

- Runtime prerequisites and install sequencing.
- Asset layout checks for `AI-onnx/` and `Assets/`.
- Python version expectations for source inspection and app runtime.
- Provider/readiness checks before image or video work.
- Preferences-file loading and first-launch troubleshooting.

## What belongs elsewhere

- Still-image AI behavior, tiling, and output naming belong in `image-upscaling`.
- Video extraction, resume, encoding, and cleanup belong in `video-upscaling`.
- Shared model names, supported formats, and suffix rules live in the root references.

## Core workflow

1. Read `references/launch-and-dependency-checklist.md` for the install and startup order.
2. Read `references/provider-and-asset-validation.md` to confirm the DirectML provider and required files.
3. Use `../../scripts/inspect_qualityscaler_layout.py` when you need a safe existence check for the script, model slots, and bundled binaries.
4. Use `../../scripts/launch_qualityscaler.py` when you want a gated startup path that refuses to launch until the layout is ready.
5. If the app reaches the GUI but later fails, move to the image or video sub-skill that owns the workflow.

## Evidence-backed facts

- The app is Windows-oriented and expects Tk/CustomTkinter UI support.
- The source module requires Python 3.12 or newer.
- The runtime wheel on the intended path is the DirectML ONNX build, not a generic service backend.
- The code expects `ffmpeg.exe` and `exiftool.exe` in `Assets/` and model files in `AI-onnx/`.
- Preferences are saved to a versioned JSON file under the user's Documents folder.

## Common decision points

- If the provider is missing, do not route into image or video workflows yet.
- If the model slots are missing, the app cannot perform AI upscaling even if the GUI opens.
- If the preferences file is malformed, the quickest recovery is usually to fix or remove that JSON and relaunch.
- If the source cannot import on Linux, that is a platform limitation of the app runtime, not a generic package failure.

## Bundled references

- `references/launch-and-dependency-checklist.md`
- `references/provider-and-asset-validation.md`
- `references/runtime-troubleshooting.md`

## Bundled scripts

- `../../scripts/inspect_qualityscaler_layout.py` for layout and asset presence checks.
- `../../scripts/launch_qualityscaler.py` for preflight-gated GUI startup.

## Stop conditions

Stop here and escalate to troubleshooting when you need a missing dependency, a missing asset, or a provider that is not present on the target system. Do not try to solve image or video behavior before the runtime is ready.
