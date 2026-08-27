---
name: ui
description: "Routes Gradio Interface launch, example app adaptation, and UI
  troubleshooting workflows for stable_diffusion_videos."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ui

Use this sub-skill when the task is about the `Interface` class, the image/video
Gradio tabs, or adapting the repository's app launch examples.

## What this route owns

- `Interface(pipeline, params=None)`
- `Interface.launch(...)`
- image-tab inputs that route to `generate_images(...)`
- video-tab inputs that route to `pipeline.walk(...)`
- adapting the simple app launcher into a safe, configurable script
- understanding why the experimental music-video UI is reference-only

## What this route excludes

- Low-level walk, image-generation, audio-timing, and upsampling details, which
  belong to `generation`.
- Generic Gradio app design that does not use `stable_diffusion_videos`.
- Full production deployment, auth, or queue infrastructure.

## Read these bundled files

- `references/workflows.md` for launch recipes and UI input mappings.
- `references/troubleshooting.md` for Gradio, model-loading, and experimental
  music-app issues.
- `scripts/launch_interface.py` for a configurable launcher with a safe dry-run
  mode.
- `../../references/api-reference.md` for exact `Interface` and generation API
  signatures.
- `../../references/repo-provenance.md` for source snapshot and evidence paths.

## Common tasks

### Launch the basic UI

Use `scripts/launch_interface.py --dry-run` first to check model/device choices.
Pass `--run` only when the environment is ready to download or load the model
and start a long-running Gradio process.

### Explain the UI tabs

The image tab passes prompt, batch, inference, guidance, size, upsampling, and
output-directory settings to `generate_images(...)`. The video tab parses
newline-separated prompts/seeds and passes them to `pipeline.walk(...)`.

### Adapt the music-video UI

Treat the experimental music-video app as reference material. It includes audio
slicing, timestep plotting, image preview, and a downloader example, but it also
loads GPU models and can use network access. Prefer the generation helper
scripts when you only need audio timing or a command-line recipe.

## Route decision

Choose this sub-skill when the request names `Interface`, `Gradio`, `run_app`,
`run_music_video_app`, "image tab", "video tab", or "launch the demo".
Choose `generation` when the request is primarily about `walk(...)`,
`generate_images(...)`, audio weights, frame generation, or video encoding.
