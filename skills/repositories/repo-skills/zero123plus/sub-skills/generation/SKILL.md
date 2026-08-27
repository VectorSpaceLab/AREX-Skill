---
name: generation
description: "Guides Zero123Plus single-image to multi-view generation,
  ControlNet variants, model choices, camera outputs, and postprocessing
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Zero123Plus Generation

Use this sub-skill when the task is about producing, adapting, or debugging
Zero123Plus multiview outputs from a single image: base v1.1/v1.2 runs, depth
ControlNet, normal ControlNet, six-view grid interpretation, matting
postprocess, or reference-only upstream image synthesis for inputs.

Do **not** use this sub-skill for serving or deployment surfaces such as
Streamlit, Gradio, Docker/Gitpod, or Cog. Route those questions to
[`../deployment/SKILL.md`](../deployment/SKILL.md) instead.

## Read first

- [`references/workflows.md`](references/workflows.md): copyable recipes for the
  base, depth ControlNet, normal ControlNet, matting, and the optional
  text-to-image input helper.
- [`references/api-reference.md`](references/api-reference.md): verified
  pipeline and helper signatures, parameter notes, and call behavior.
- [`references/model-and-camera.md`](references/model-and-camera.md): model ids,
  six fixed views, camera poses, field of view, and license notes.
- [`references/troubleshooting.md`](references/troubleshooting.md): cache,
  CUDA, VRAM, image-shape, diffusers version, and matting dependency failures.

## Bundled scripts

- [`scripts/run_img_to_mv.py`](scripts/run_img_to_mv.py): v1.1 base
  single-image-to-six-view runner.
- [`scripts/run_depth_controlnet.py`](scripts/run_depth_controlnet.py): v1.1
  depth ControlNet runner.
- [`scripts/run_normal_gen.py`](scripts/run_normal_gen.py): v1.2 normal
  generator runner with bundled matting postprocess.
- [`scripts/matting_postprocess.py`](scripts/matting_postprocess.py): CPU-safe
  alpha/normal postprocess helper and CLI.

## Routing procedure

1. Identify the requested flow: base multiview generation, depth ControlNet,
   normal ControlNet, postprocess-only work, or optional image synthesis before
   Zero123Plus.
2. Check GPU and cache readiness before a real run. The bundled scripts default
   to local-cache-only loading; pass `--allow-download` only when network access
   and model fetches are approved.
3. For a standard six-view grid, use the bundled script that matches the
   requested model family. The scripts already encode the source defaults for
   scheduler choice, width, height, and output layout.
4. For camera layout, view ordering, and license questions, use the
   model-and-camera reference. For exact callable signatures and preprocessing
   details, use the API reference.
5. If the user asks about Streamlit, Gradio, Docker, or Cog rather than the
   core generation path, switch to the deployment sub-skill instead of
   duplicating those details here.

## Stop conditions

- No CUDA GPU is available for a real generation run.
- The requested model or custom pipeline is not already cached and downloads are
  not approved.
- The user is asking about training or finetuning, which this repository does
  not expose.
- The issue is really about serving or deployment rather than generation.
