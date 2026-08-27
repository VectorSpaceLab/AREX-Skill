---
name: inference-and-evaluation
description: "Run and troubleshoot YOLOv7-d2 PyTorch demo inference,
  visualization, W&B logging, benchmark planning, and COCO evaluation
  workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Inference and Evaluation

Use this sub-skill when the user needs a YOLOv7-d2 PyTorch checkpoint demo, image/video visualization, confidence/NMS tuning, W&B inference logging, benchmark planning, COCO evaluation, or demo/eval troubleshooting.

## Start here

1. Confirm the user has a config file, checkpoint/weights, and input images/video or a registered validation dataset.
2. Use [scripts/check_demo_inputs.py](scripts/check_demo_inputs.py) to preflight config, input, output, and local weight paths.
3. Build a demo command with [scripts/build_demo_command.py](scripts/build_demo_command.py), then read [references/workflows.md](references/workflows.md).
4. For evaluation or benchmark tasks, read [references/evaluation.md](references/evaluation.md).
5. For predictor internals and flags, read [references/api-reference.md](references/api-reference.md).
6. Use [references/troubleshooting.md](references/troubleshooting.md) for headless OpenCV, missing weights, dataset registration, or LazyConfig demo issues.

## Common command shapes

Image or directory demo:

```bash
python demo.py --config-file path/to/config.yaml --input path/to/image_or_dir --output path/to/out_dir --opts MODEL.WEIGHTS path/to/model.pth
```

Force CPU for a small smoke run:

```bash
python demo.py --config-file path/to/config.yaml --input path/to/image.jpg --output path/to/out.jpg --opts MODEL.WEIGHTS path/to/model.pth MODEL.DEVICE cpu
```

COCO evaluation shape:

```bash
python train_det.py --config-file path/to/config.yaml --eval-only MODEL.WEIGHTS path/to/model.pth
```

## Boundaries

- For config selection, dataset registration, and training launchers, read [../training-and-configuration/SKILL.md](../training-and-configuration/SKILL.md).
- For ONNXRuntime inference rather than PyTorch checkpoint inference, read [../deployment-and-export/SKILL.md](../deployment-and-export/SKILL.md).

## Safety notes

Do not run demos without user-provided weights and input data. Do not run the benchmark loop as a default check; it repeats inference and is hardware/model dependent. Do not run data-cleaning workflows without explicit user approval because they can influence which data is kept or discarded.
