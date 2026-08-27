---
name: classification
description: "Use MambaVision for image classification, feature extraction,
  pretrained checkpoint handling, ImageNet validation command construction, and
  safe inference or throughput smokes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MambaVision Classification

Use this sub-skill when a task is about the `mambavision` Python package API for ImageNet-style image classification, pooled feature extraction, pretrained checkpoint cache behavior, no-download dummy inference, ImageNet validation command construction, or lightweight throughput checks.

## Route here for

- Installing the classification package dependencies and importing `from mambavision import create_model`.
- Creating any registered factory: `mamba_vision_T`, `mamba_vision_T2`, `mamba_vision_S`, `mamba_vision_B`, `mamba_vision_B_21k`, `mamba_vision_L`, `mamba_vision_L_21k`, `mamba_vision_L2`, `mamba_vision_L2_512_21k`, `mamba_vision_L3_256_21k`, or `mamba_vision_L3_512_21k`.
- Running no-download inference smoke tests with arbitrary image height/width.
- Loading local checkpoints, intentionally triggering pretrained downloads, or diagnosing cache/model-path behavior.
- Building ImageNet/ImageFolder validation commands and optional CSV/JSON result output.
- Running a safer local throughput/FLOPs helper without using the original benchmark script.

## Route elsewhere

- ImageNet training, fine-tuning, YAML config tuning, distributed launch, AMP/EMA/MESA, and resume behavior: read `../training/SKILL.md`.
- Cascade Mask R-CNN / COCO / MMDetection workflows: read `../object-detection/SKILL.md`.
- UPerNet / ADE20K / MMSegmentation workflows: read `../semantic-segmentation/SKILL.md`.

Do not claim that the OpenMMLab stack is installed from this sub-skill. Classification package verification covered the base MambaVision package and CUDA model forward smoke only; downstream detection/segmentation dependencies are optional and routed to their own sub-skills.

## First steps

1. Check the package/import contract in `references/api-reference.md`.
2. Pick the factory and checkpoint family from `references/model-overview.md`.
3. For no-download API validation, run `scripts/smoke_mambavision_inference.py --help` and then run it with `--pretrained` omitted.
4. For ImageNet or custom ImageFolder validation, use `references/validation-workflows.md` to construct a command and verify dataset/checkpoint prerequisites before launching.
5. For benchmark questions, prefer `scripts/benchmark_mambavision.py` over the original throughput workflow because it fixes the batch-size variable bug, guards CUDA use, and makes FLOPs optional.
6. If installation, CUDA, checkpoint, data, shape, or timm warning issues appear, consult `references/troubleshooting.md`.

## Bundled helper guarantees

- Safe defaults: no downloads, no training, no dataset writes, no credentials, and tiny batch sizes by default.
- `--pretrained` is opt-in; without it, helpers call `create_model(..., pretrained=False)`.
- The smoke helper asserts finite logits and the expected output shape.
- The benchmark helper reports measured latency/throughput and skips optional FLOPs unless requested.
