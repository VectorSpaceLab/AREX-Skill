---
name: deployment
description: "Guides Zero123Plus demo, serving, and Cog deployment workflows,
  including Gradio, Streamlit, checkpoints, UI options, and deployment
  failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Zero123Plus Deployment

Use this sub-skill when a task is about launching, adapting, packaging, or
troubleshooting Zero123Plus demos and service surfaces: Streamlit, Gradio,
Docker/Gitpod-style environments, Cog/Replicate predictors, checkpoint caches,
ports, sharing, queues, and UI options.

Do **not** use this sub-skill as the main source for image-to-multiview
algorithm details, ControlNets, camera poses, or batch generation code. Route
those questions to the sibling generation sub-skill at
[`../generation/SKILL.md`](../generation/SKILL.md), then return here for serving
and deployment decisions.

## Read first

- [`references/deployment.md`](references/deployment.md): deployment surfaces,
  dependency/bootstrap patterns, Docker/Gitpod/Cog behavior, and how the surfaces
  differ.
- [`references/demo-options.md`](references/demo-options.md): Streamlit and
  Gradio UI inputs, preprocessing options, examples, and output behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md): deployment
  failure modes for checkpoints, rembg/SAM, ports, queues, Cog weights, pget,
  CUDA, and source demo side effects.

## Bundled deployment templates

- [`scripts/launch_gradio_demo.py`](scripts/launch_gradio_demo.py): a compact,
  self-contained Gradio launcher template. It avoids model downloads by default;
  pass `--allow-download` only when network/model fetching is approved.
- [`scripts/cog_predictor.py`](scripts/cog_predictor.py): a self-contained Cog
  predictor template with configurable cache/model paths and no model loading on
  import.

## Routing procedure

1. Identify the requested surface: local Streamlit demo, Gradio demo, container
   image, Gitpod-style workspace, Cog/Replicate predictor, or a custom service.
2. Check whether the user has approved network downloads and whether the runtime
   has a CUDA GPU. Stop or ask before triggering Hugging Face model downloads,
   SAM checkpoint downloads, rembg/ONNX model downloads, or Cog weight archive
   fetches.
3. For a safer local Gradio launch, prefer the bundled launcher template over
   importing source UI modules. For Cog, adapt the bundled predictor template and
   configure its environment variables instead of relying on checkout-relative
   paths.
4. For UI behavior, input preprocessing, background removal, and output layout,
   read `references/demo-options.md`. For exact pipeline arguments and generated
   view semantics, route to `../generation/SKILL.md`.
5. If a failure involves missing CUDA, unavailable weights, missing SAM/rembg
   components, blocked Gradio share tunnels, or Cog cache/download issues, use
   `references/troubleshooting.md` before proposing code changes.

## Stop conditions

- No CUDA GPU is available for an actual generation-backed demo or Cog run.
- The required model/checkpoint/cache is absent and downloads are not approved.
- Background removal is required but `rembg`, `segment_anything`, or the SAM
  checkpoint is missing and the user has not approved installing/downloading it.
- The request is really about generation APIs, ControlNet variants, or camera
  outputs; route to the generation sub-skill instead of duplicating that logic
  here.
