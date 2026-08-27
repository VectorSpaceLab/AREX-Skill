---
name: efficientvit
description: "Routes EfficientViT classification plus downstream detection and
  segmentation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# EfficientViT

Use this sub-skill when the user wants to build, inspect, train, evaluate, or benchmark an EfficientViT model family member.
It covers both the lightweight ImageNet classification path and the heavier downstream MMDetection path.

## What this route owns

- EfficientViT-M0 through EfficientViT-M5 model builders.
- ImageNet classification evaluation, training, and throughput benchmarking.
- RetinaNet object detection and Mask R-CNN instance segmentation downstream workflows.

## When to use it

Choose this route for prompts like:

- "run EfficientViT M4 on ImageNet"
- "benchmark EfficientViT throughput"
- "train EfficientViT classification"
- "evaluate EfficientViT downstream on COCO"
- "fix a model builder / pretrained checkpoint issue"

## What to read next

- `references/api-reference.md` for the verified builder signatures and the key CLI flags.
- `references/workflows.md` for ImageNet and COCO launcher shapes.
- `references/troubleshooting.md` for model-name, checkpoint, mmcv/mmdet, and layout failures.
- `scripts/build_efficientvit_command.py` to print safe command templates.
- `scripts/benchmark_efficientvit.py` for a small, safe throughput check without the original long-running benchmark loop.

## Important boundaries

- Do not route AutoFormer, Cream, MiniViT, TinyCLIP, TinyViT, or iRPE here.
- Treat downstream detection / segmentation as a separate dependency stack; it needs MMDetection/MMCV and should not be assumed from the classification environment.
- The repository's original `classification/speed_test.py` runs long throughput loops; use the bundled benchmark helper when you need a smaller, configurable check.

## Working pattern

1. Decide whether the user needs classification or downstream detection / segmentation.
2. Read the API and workflow references for the correct builder names and launcher shape.
3. Use the benchmark helper for a quick throughput sanity check.
4. Use the command-builder script when the user wants a reproducible command string instead of an immediate run.

## Common signals

- `EfficientViT_M0` through `EfficientViT_M5` are the supported classification builders.
- The head is a `BN_Linear` wrapper, not a plain `nn.Linear`; inspect its `.l` member if you need the classification layer.
- Downstream detection and segmentation refer to `dist_train.sh` and `dist_test.sh` with MMDetection-style configs.
