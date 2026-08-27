---
name: quality-scaler
description: "Routes QualityScaler tasks for Windows image and video upscaling,
  setup, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# QualityScaler

QualityScaler is a Windows-oriented image and video AI upscaler. Use this repo skill when a task mentions the app, its bundled model slots, its DirectML-backed runtime, or its image/video output naming and troubleshooting behavior.

## Start here

- Read `references/repo-provenance.md` when you need to check whether this skill still matches the repository snapshot.
- Read `references/shared-runtime-and-assets.md` for the common Windows/runtime asset contract.
- Read `references/shared-settings-and-output-contract.md` for model names, supported formats, and output naming rules.
- Run `scripts/inspect_qualityscaler_layout.py` when you need a safe file-layout check before launch or import work.
- Run `scripts/launch_qualityscaler.py` when you want a preflight-gated way to start the GUI on a Windows machine.
- Run `scripts/derive_qualityscaler_paths.py` when you need to preview image, video, or frame output names without launching the GUI.

## Route map

| User intent | Go to |
| --- | --- |
| Install, launch, dependency, asset, or provider readiness | `sub-skills/setup-runtime/SKILL.md` |
| Still-image upscaling, model selection, tiling, metadata copy, or output naming | `sub-skills/image-upscaling/SKILL.md` |
| Video frame extraction, resume, encoding, codec fallback, or keep-frames behavior | `sub-skills/video-upscaling/SKILL.md` |

## Shared facts to keep in mind

- The repository is a single main Python file plus assets and model slots.
- The public runtime depends on Windows Tk/CustomTkinter, the DirectML ONNX provider, `ffmpeg.exe`, and `exiftool.exe`.
- The source module requires Python 3.12 or newer to import cleanly.
- The bundled launcher script can preflight the layout before attempting the GUI entrypoint.
- The app stores preferences in a versioned JSON file under the user's Documents folder.
- Image and video outputs follow the same suffix contract: model name, input resize, output resize, and optional blending tag.
- `QualityScaler.py` distinguishes image and video workflows by input extension, then dispatches into the image or video sub-skill paths.

## How to use this skill

1. Start with `setup-runtime` when the app does not start, the provider is missing, or the asset layout is incomplete.
2. Use `image-upscaling` when the task is about still photos, alpha/grayscale handling, or output file naming for images.
3. Use `video-upscaling` when the task is about videos, resume logic, frame folders, or codec fallback.
4. If the problem is generic rather than workflow-specific, read `references/troubleshooting.md` first and then route to the owning sub-skill.

## What not to do

- Do not assume Linux GUI runtime support for the app itself.
- Do not claim DirectML runtime verification unless the target system actually exposes it.
- Do not tell future agents to depend on the original repository checkout for runtime behavior; use the bundled references and scripts.
- Do not mix image-core and video-pipeline details into the root router when a sub-skill owns the workflow.

## Useful bundled files

- `references/source-map.md` for the source-to-skill ownership map.
- `references/troubleshooting.md` for cross-cutting failure modes.
- `scripts/inspect_qualityscaler_layout.py` for layout checks.
- `scripts/launch_qualityscaler.py` for gated GUI startup.
- `scripts/derive_qualityscaler_paths.py` for output-name previews.

## Minimal import sanity check

Before deeper inspection, confirm that the environment can parse the source with Python 3.12+ and that the expected runtime packages are available. If the environment is only for read-only inspection, use the bundled layout script and the shared references instead of trying to launch the GUI.
