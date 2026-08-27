---
name: vision-and-apps
description: "Routes TensorLayer pretrained vision models, image apps, and
  visual inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Vision and Apps

Use this sub-skill for TensorLayer pretrained image constructors, object-detection and pose wrappers, spatial-transformer patterns, and image-centric application tutorials. This is the route for vision workflows that sit above the core model APIs.

## Typical requests

- Instantiate VGG16, MobileNetV1, ResNet50, or SqueezeNetV1.
- Inspect YOLOv4 or human-pose wrapper behavior.
- Understand image inference, drawing, or visualization workflows.
- Adapt a pretrained image example to a safe local smoke.

## Read first

- `references/model-overview.md` for constructor and wrapper notes.
- `references/workflows.md` for tiny vision smoke patterns.
- `references/troubleshooting.md` for missing weights, OpenCV, and headless display issues.

## Bundled check

- `scripts/smoke_vision_models.py` instantiates the main image constructors with `pretrained=False` and can optionally run a tiny forward pass.

## Boundaries

Include here:
- `tensorlayer.app`
- pretrained image constructors in `tensorlayer.models`
- object detection, pose estimation, and image app tutorials
- spatial-transformer and quantized image workflows when they are vision-centric

Exclude or route elsewhere:
- core serialization or layer mechanics -> `core-modeling`
- generic data loading or preprocessing helpers -> `data-and-utilities`
- training-loop orchestration and CLI help -> `training-and-cli`
- text or RL workflows -> `text-and-sequence` / `reinforcement-learning`

## Fast path

1. Decide whether the request is an image model, app wrapper, or visualization task.
2. Keep pretrained constructors on `pretrained=False` unless the user explicitly needs weights.
3. Use the smoke script before opening a large tutorial or external weight path.
