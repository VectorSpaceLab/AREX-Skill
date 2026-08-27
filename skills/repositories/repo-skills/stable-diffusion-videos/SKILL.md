---
name: stable-diffusion-videos
description: "Routes Stable Diffusion video, image, audio-synced interpolation,
  optional upsampling, and Gradio UI workflows for the stable_diffusion_videos
  package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# stable-diffusion-videos

Use this repo skill for the `stable_diffusion_videos` package when the task is about
prompt-to-video walks, music-synced interpolation, still-image generation, optional
Real-ESRGAN upsampling, or the bundled Gradio demo.

## Start here

- Read `references/api-reference.md` when you need exact public signatures,
  defaults, or output shapes.
- Read `references/troubleshooting.md` when imports fail, video encoding breaks,
  or dependency versions drift.
- Read `references/repo-provenance.md` before deciding whether this skill still
  matches the current repo snapshot or before refreshing it.
- Read `references/repo-routing-metadata.json` if you are updating router import
  metadata or need the scenario selection signals.

## Quick install and smoke check

Use the published package when you only need the runtime API:

```bash
python -m pip install stable_diffusion_videos
```

For the video workflows, make sure these runtime basics are present:

- `torch` + `torchvision` with a matching CUDA-capable build when you want to
  run the GPU video generation path.
- `ffmpeg` with a working `libx264` encoder for MP4 creation.
- Optional: `av` for `write_video`, `librosa` for audio-timed interpolation, and
  `realesrgan` for upsampling.

A minimal import check is:

```bash
python -I -c "from stable_diffusion_videos import StableDiffusionWalkPipeline, generate_images, Interface"
```

For a safer local smoke check, run the bundled helper:

```bash
python scripts/check_env.py --help
```

## Route map

### `generation`
Use this route for the core diffusion workflows:

- `StableDiffusionWalkPipeline.walk(...)`
- `generate_images(...)`
- audio-timed interpolation with `get_timesteps_arr(...)`
- video encoding with `make_video_pyav(...)`
- optional `RealESRGANModel` upsampling
- the Torch walk pipeline and its helper scripts

Common triggers:

- "make a Stable Diffusion video"
- "generate a music video"
- "walk between prompts"
- "upsample the generated frames"
- "convert audio energy into interpolation weights"
- "preview the walk inputs before running"

Read `sub-skills/generation/SKILL.md` for the workflow router, then use its
bundled references and scripts.

### `ui`
Use this route for the Gradio demo and the example launchers:

- `Interface`
- the packaged UI launcher pattern
- the image/video tabs and their launch parameters
- the experimental music-video UI only as reference material

Common triggers:

- "launch the demo"
- "start the Gradio interface"
- "open the image/video tabs"
- "adapt the example launcher"

Read `sub-skills/ui/SKILL.md` for launch patterns, input mappings, and UI
troubleshooting.

## Optional path

If the request is specifically about the experimental Flax/JAX/TPU notebook or
`generate_images_flax(...)`, read `sub-skills/generation/references/flax-and-tpu.md`.
That path is optional and is not part of the default Torch video workflow.

## Where the reusable helpers live

- `scripts/check_env.py` checks imports, GPU readiness, and tiny video/audio
  smokes.
- `sub-skills/generation/scripts/make_video_template.py` adapts the music-video
  recipe into a safer command-line helper.
- `sub-skills/generation/scripts/preview_audio_timesteps.py` previews audio-driven
  interpolation weights.
- `sub-skills/ui/scripts/launch_interface.py` adapts the Gradio launcher into a
  configurable helper.

## Operational reminders

- Video generation is GPU-oriented; CPU importability is not enough for the main
  walk workflow.
- `height` and `width` must be multiples of 8.
- `seeds` must match prompts, and `num_interpolation_steps` must match the number
  of prompt gaps.
- The skill is self-contained. Do not point future agents back to the original
  checkout for runtime instructions.
