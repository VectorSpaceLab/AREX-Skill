---
name: web-demo
description: "Routes DragGAN browser-demo tasks such as launching the Gradio UI,
  selecting checkpoints, dragging points, and saving edited outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# web-demo

Use this sub-skill when the task is about the browser experience: launch the demo, open the web UI, choose a checkpoint, click handle and target points, save an image or video, or troubleshoot the demo runtime.

## Start here

1. Run the bundled preflight:
   `../../scripts/check_install.py --mode web`
2. Launch the demo with the bundled wrapper:
   `../../scripts/launch_web_demo.py --device cuda --ip 0.0.0.0 --port 7860`
3. Read `references/workflows.md` for the point-drag sequence and UI controls.
4. Read `../../references/checkpoints.md` if you need model names or cache behavior.
5. Read `references/troubleshooting.md` if the UI opens but the interaction fails.

## This sub-skill covers

- Launching the browser demo with the supported launch flags.
- Switching between checkpoints in the model dropdown.
- Creating a seeded image, placing handle and target points, and running `Drag it`.
- Resetting, undoing, and saving edited outputs.
- Understanding the saved `draggan_tmp/` files and checkpoint cache usage.

## This sub-skill does not cover

- Writing a custom Python script around `draggan.draggan` functions.
- Low-level tensor shapes, point encoding, or latent manipulation details.
- Claims that CPU or MPS is a verified drag backend.

## Important cautions

- The verified drag path in this snapshot requires CUDA.
- The `Draw a Mask` tab is present in the UI, but the current optimizer does not enforce the mask.
- Uploaded-image inversion is experimental; treat it as a best-effort path rather than the default workflow.
- If you only need the install check or environment diagnosis, use the root scripts and troubleshooting reference first.

## Helpful references

- `references/workflows.md` for the user-facing browser steps.
- `references/troubleshooting.md` for launch, model-download, and UI-specific failures.
- `../../references/deployment.md` for install and launch modes shared with the root skill.
- `../../references/checkpoints.md` for checkpoint names and the cache root.
