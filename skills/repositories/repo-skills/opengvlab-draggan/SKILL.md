---
name: opengvlab-draggan
description: "Routes DragGAN users to the browser demo and Python API workflows
  for point-based image editing, checkpoint loading, and CUDA troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# DragGAN

Use this skill when a task mentions DragGAN, the Gradio demo, point dragging, pretrained checkpoint selection, or scripted latent/image generation.

## Quick start

1. Install a CUDA-enabled PyTorch/TorchVision pair that matches your platform.
2. Install this package: `python -m pip install "draggan==1.1.6"`.
3. If you already have a checkout open for editing, `python -m pip install -e .` is also fine.
4. Run `scripts/check_install.py --mode web` before launching the browser UI, or `scripts/check_install.py --mode api` before scripting against the package.

## Routes

- `sub-skills/web-demo/` for the browser UI, checkpoint switching, point dragging, and saved image/video outputs.
- `sub-skills/python-api/` for `draggan.draggan` and `draggan.utils` usage from your own code.

## Shared references

- `references/deployment.md` for install and launch patterns, including the bundled launcher and Docker notes.
- `references/checkpoints.md` for checkpoint names, cache location, and auto-download behavior.
- `references/troubleshooting.md` for cross-cutting import, backend, and checkpoint failures.
- `references/repo-provenance.md` when checking whether this skill still matches the current repository snapshot.
- `references/repo-routing-metadata.json` for the route metadata used by repo-skills-router.

## Important limits

- The verified drag loop is CUDA-only in this snapshot.
- The mask tab shown in the UI is not enforced by the current optimizer.
- Uploaded-image inversion is experimental and may fail; prefer the seeded-image workflow unless you are specifically debugging that path.
- If the task is only about environment problems, read the root troubleshooting reference before choosing a route.

## Route selection hints

Choose `web-demo` when the request talks about the browser demo, clicking handle and target points, choosing checkpoints, saving outputs, or exposing the app on a host/port.

Choose `python-api` when the request talks about `load_model`, `generate_W`, `generate_image`, `drag_gan`, latent editing, or writing a script around the package.

If the task is unclear, inspect `references/deployment.md` first, then route to the sub-skill that matches the user-facing workflow.
