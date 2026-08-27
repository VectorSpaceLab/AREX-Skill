---
name: generation
description: "Routes Stable Diffusion walk, music-video, still-image,
  audio-timing, and upsampling workflows for stable_diffusion_videos."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# generation

Use this sub-skill when the task is to create images or videos with the
Diffusers pipelines exposed by `stable_diffusion_videos`.

## What this route owns

- `StableDiffusionWalkPipeline.walk(...)`
- `StableDiffusionWalkPipeline.make_clip_frames(...)`
- `generate_images(...)`
- `generate_images_flax(...)` as an optional backend reference
- `get_timesteps_arr(...)`
- `make_video_pyav(...)`
- `RealESRGANModel` loading and folder upsampling
- prompt / seed validation, frame layouts, and audio-driven interpolation

## What this route excludes

- Gradio UI launchers and tab wiring, which belong to `ui`
- repository maintenance and packaging tasks
- heavyweight training or checkpoint creation

## Read these bundled files

- `references/workflows.md` for end-to-end command patterns and output layout.
- `references/troubleshooting.md` for generation-specific failures and recovery.
- `references/flax-and-tpu.md` if you need the optional JAX/Flax/TPU path.
- `../../references/api-reference.md` for exact public signatures.
- `../../references/repo-provenance.md` for source snapshot and evidence paths.

## Common tasks

### Make a prompt walk

Start with `references/workflows.md` or run the template script with `--dry-run`
first. Then switch to `--run` when you are ready to download the model and use
CUDA.

### Make a music video

Use the audio offsets recipe, compute interpolation steps from the offsets and
FPS, and confirm the frame count before generating.

### Generate still images

Use `generate_images(...)` when you want prompt-conditioned image batches
instead of a walk.

### Preview audio timing

Use `scripts/preview_audio_timesteps.py` to inspect the interpolation weights for
a local audio file before running a long generation.

### Upsample frames or folders

Use `RealESRGANModel` only when you really need the 4x upsampling path. It is
optional, heavier, and can be slow on CPU.

## Backends and prerequisites

- The main walk workflow is GPU-oriented.
- `height` and `width` must be multiples of 8.
- `ffmpeg` with `libx264` must be available for MP4 encoding.
- `librosa` is needed for audio-timed interpolation.
- `realesrgan` is only needed for the upsampling path.

## Workflow boundaries

If you are unsure whether a request is a generation or UI task, choose this
sub-skill when the user names `walk`, `generate_images`, `audio_filepath`,
`get_timesteps_arr`, `make_video_pyav`, `RealESRGANModel`, or `upsample`.
Choose `ui` when the request is about the Gradio demo or launch parameters.
