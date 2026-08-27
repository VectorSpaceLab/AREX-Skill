---
name: mmyolo
description: "Use MMYOLO for OpenMMLab YOLO object detection configs, datasets,
  training/testing, inference, model APIs, and deployment conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# MMYOLO repo skill

Use this skill when the task involves MMYOLO, OpenMMLab YOLO-family object detection, MMEngine configs, MIM train/test commands, detection datasets, MMYOLO inference/visualization, MMYOLO registries/model components, or MMYOLO deployment/export/conversion.

MMYOLO v0.6.0 is an OpenMMLab toolbox for YOLO-style object detection and related detection workflows. It builds on PyTorch, MMCV, MMEngine, and MMDetection.

## First checks

1. Read [repository provenance](references/repo-provenance.md) if you need to decide whether this skill matches a checkout or package version.
2. Read [installation notes](references/installation.md) before changing an environment or diagnosing imports.
3. Run [scripts/check_mmyolo_environment.py](scripts/check_mmyolo_environment.py) when you need a safe import/version/config parse check.
4. Use [cross-cutting troubleshooting](references/troubleshooting.md) for import/version/backend/MIM failures before entering a specific workflow.

Minimal import check:

```shell
python scripts/check_mmyolo_environment.py --json
```

Config parse check:

```shell
python scripts/check_mmyolo_environment.py --config CONFIG.py
```

## Route by user task

| User task | Read |
| --- | --- |
| Choose a YOLOv5/6/7/8, YOLOX, RTMDet, or PPYOLOE baseline; edit config inheritance, class counts, dataloaders, evaluators, hooks, TTA, or `--cfg-options`. | [config-customization](sub-skills/config-customization/SKILL.md) |
| Prepare or validate COCO/YOLO/VOC/DOTA/LabelMe data, convert labels, inspect annotation JSON, plan anchor optimization, or wire data paths into a config. | [data-tools](sub-skills/data-tools/SKILL.md) |
| Construct safe train/resume/AMP/test/evaluation/prediction-output commands, plan distributed/Slurm launch, analyze logs/schedulers/confusion matrices, or troubleshoot training/evaluation. | [training-evaluation](sub-skills/training-evaluation/SKILL.md) |
| Plan image/folder/URL/video inference, save visualized detections, export LabelMe annotations, inspect `DetDataSample`, use SAHI large-image recipes, or plan feature-map/CAM visualization. | [inference-visualization](sub-skills/inference-visualization/SKILL.md) |
| Inspect registries, public model/dataset components, backbones/necks/heads/losses/assigners, custom project patterns, plugins, or `switch_to_deploy`. | [model-api](sub-skills/model-api/SKILL.md) |
| Convert upstream YOLO checkpoints, plan ONNXRuntime/TensorRT/RKNN/MMDeploy export, check optional deployment dependencies, or reason about backend artifacts. | [deployment-conversion](sub-skills/deployment-conversion/SKILL.md) |

## Common workflow paths

### Fine-tune on a custom detection dataset

1. Use [data-tools](sub-skills/data-tools/SKILL.md) to validate annotation schema, category order, image paths, and dataset layout.
2. Use [config-customization](sub-skills/config-customization/SKILL.md) to create a child config with correct `metainfo`, `num_classes`, dataloaders, evaluators, epochs, hooks, and pretrained initialization.
3. Use [training-evaluation](sub-skills/training-evaluation/SKILL.md) to build a safe `mim train mmyolo` command and decide GPU/AMP/resume settings.
4. Return to [training-evaluation](sub-skills/training-evaluation/SKILL.md) for `mim test mmyolo`, prediction dumps, painted outputs, and metric troubleshooting.

### Run prediction and export labels

1. Use [config-customization](sub-skills/config-customization/SKILL.md) if the config/class metadata is uncertain.
2. Use [inference-visualization](sub-skills/inference-visualization/SKILL.md) for CPU/GPU image/folder/URL inference, score/class filters, and LabelMe output.
3. Use [data-tools](sub-skills/data-tools/SKILL.md) only when the produced labels need validation or conversion for a later training dataset.

### Prepare deployment

1. Use [training-evaluation](sub-skills/training-evaluation/SKILL.md) or [inference-visualization](sub-skills/inference-visualization/SKILL.md) to confirm the checkpoint/config pair works before export.
2. Use [deployment-conversion](sub-skills/deployment-conversion/SKILL.md) to select ONNXRuntime, TensorRT, RKNN, MMDeploy, or checkpoint-conversion paths.
3. Run the deployment dependency checker before proposing vendor-specific commands.

## Boundaries

- Do not launch training, evaluation, inference, downloads, exports, or vendor builds unless the caller explicitly asks for execution and the side effects are acceptable.
- Do not treat CPU import/config success as proof of CUDA, TensorRT, RKNN, or DeepStream readiness.
- Do not invent dataset paths, Slurm partitions, WandB credentials, checkpoint URLs, or vendor toolchain availability.
- Prefer package-level OpenMIM commands and bundled helpers over checkout-local source script paths.
- If the task is generic PyTorch, generic computer vision, or another OpenMMLab package without MMYOLO-specific configs/APIs, route to a more specific skill.
