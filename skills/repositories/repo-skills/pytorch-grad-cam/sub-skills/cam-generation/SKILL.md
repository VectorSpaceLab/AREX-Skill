---
name: cam-generation
description: "Routes core pytorch-grad-cam heatmap generation, target layer
  selection, smoothing, guided backprop, and safe smoke-test workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CAM Generation

Use this sub-skill when a user wants to create class activation maps for a
PyTorch image/classification-style model, overlay heatmaps on images, choose
class targets, apply smoothing, combine CAM with guided backpropagation, or run
a safe no-download smoke test.

## First read/run

- Read [`references/cam-workflows.md`](references/cam-workflows.md) for the
  core GradCAM pattern, target layer choices, smoothing, guided backprop, batch
  behavior, and output validation.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when a
  CAM is blank, slow, wrong-shaped, on the wrong device, or leaking hooks.
- Run [`scripts/tiny_cam_smoke.py`](scripts/tiny_cam_smoke.py) to verify the
  installed package with a tiny in-memory CNN and no external weights.

## Core workflow

1. Put the model in `eval()` mode and choose one or more spatial target layers.
2. Prepare an input tensor shaped like the model expects, usually `B x C x H x W`.
3. Choose targets. Use `targets=None` for each batch member's top class, or a
   list such as `[ClassifierOutputTarget(class_id) for _ in range(batch_size)]`.
4. Construct the CAM object once, preferably in a `with` block:

   ```python
   from pytorch_grad_cam import GradCAM
   from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

   target_layers = [model.layer4[-1]]
   targets = [ClassifierOutputTarget(281)]
   with GradCAM(model=model, target_layers=target_layers) as cam:
       grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
   ```

5. Overlay a single CAM using `show_cam_on_image`, ensuring the base image is
   `np.float32` in `[0, 1]`.

## Common decisions

- Use `aug_smooth=True` for test-time augmentation smoothing; expect slower
  runtime.
- Use `eigen_smooth=True` to denoise by projecting `activations * weights`.
- Set `cam.batch_size` for `ScoreCAM` and `AblationCAM` because they perform
  many forward passes.
- Use a list of target layers when uncertain; outputs are averaged across
  selected layers.
- Route ViT/Swin/CLIP, detection, segmentation, and embeddings to
  `model-task-adaptation` because they need reshape transforms or custom
  target callables.
- Route method tradeoffs and exact signatures to `methods-and-api`.
- Route ROAD/ARCC/DFF and explanation scoring to `metrics-and-evaluation`.
