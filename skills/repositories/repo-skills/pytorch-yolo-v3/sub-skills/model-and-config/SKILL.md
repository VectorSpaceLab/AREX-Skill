---
name: model-and-config
description: "Inspect and adapt pytorch-yolo-v3 Darknet model configuration,
  class names, and binary weight handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# model-and-config

Use this sub-skill when a user needs to understand or safely inspect this repo's Darknet/YOLO model configuration surface: cfg parsing, model construction, supported cfg files, class-name alignment, Darknet binary weight loading/saving, or lightweight API inspection.

## Route by task

- For `parse_cfg`, `create_modules`, `Darknet`, `Darknet.forward`, `load_weights`, or `save_weights` behavior, use [references/api-reference.md](references/api-reference.md).
- For `cfg/yolov3.cfg`, class-count edits, names-file expectations, resolution constraints, and unsupported cfg variants, use [references/model-configs.md](references/model-configs.md).
- For failures such as `Something I dunno`, `AssertionError`, class/filter mismatch, invalid input size, missing weights, or legacy PyTorch behavior, use [references/troubleshooting.md](references/troubleshooting.md).
- To inspect a user's checkout without downloading weights or running inference, run the bundled script:

```bash
python scripts/inspect_darknet_config.py --repo-root <repo-root> --cfg cfg/yolov3.cfg --names data/coco.names
```

Add `--build-model` only when the user explicitly wants to prove that `Darknet(cfgfile)` instantiates in the current Python environment.

## Out-of-scope routing

- Image batch CLI usage, drawing, image preprocessing, and detection postprocessing belong in [../image-detection/SKILL.md](../image-detection/SKILL.md).
- Video files, webcam demos, half-precision display loops, GUI/display behavior, and camera handling belong in [../video-camera-demos/SKILL.md](../video-camera-demos/SKILL.md).
- Training is out of scope for this repo skill; this repo's documented surface is detection-only.

## Operating guardrails

- Do not download weights, datasets, or class files from this sub-skill. Require the user to provide local files.
- Do not run image/video inference or GUI/camera flows from this sub-skill.
- Treat cfg files with `region` or `reorg` blocks as parseable but not constructible by this repo's `create_modules` implementation.
- Before loading weights after class-count edits, inspect the cfg/names/filter relationship and warn that pretrained Darknet weights are tied to the original detection-head shapes.
