---
name: intern-image
description: "Guides InternImage vision foundation-model workflows across image
  classification, object detection, semantic segmentation, autonomous driving,
  DCNv3 operators, and TensorRT deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# InternImage Repo Skill

Use this skill when a task mentions InternImage, OpenGVLab InternImage, DCNv3-based vision foundation models, InternImage classification/detection/segmentation configs, InternImage autonomous-driving baselines, or InternImage TensorRT/mmdeploy export.

InternImage is a large-scale vision backbone family built around DCNv3 deformable convolution. The repository is not a single installable Python package: it is a multi-workflow research codebase with separate classification, MMDetection, MMSegmentation, autonomous-driving, and deployment/operator surfaces. Route aggressively before giving commands.

## First steps

1. Identify the user's workflow family, dataset, model size, config/checkpoint, execution backend, and whether they want a command plan, debugging help, or an actual run.
2. Read [references/model-and-config-overview.md](references/model-and-config-overview.md) when the model family, config name, dataset, or checkpoint pairing is unclear.
3. Use [scripts/check_internimage_environment.py](scripts/check_internimage_environment.py) for a safe dependency/backend diagnostic before any GPU-heavy run.
4. Route to the nearest sub-skill and use that sub-skill's bundled command builder instead of copying long source launch snippets by hand.
5. For CUDA, DCNv3, mmdeploy, or TensorRT blockers, route to `sub-skills/deployment/` even when the original task is classification, detection, or segmentation.

## Route map

| User task signal | Read this next | Use when |
| --- | --- | --- |
| ImageNet, iNaturalist, classification config YAML, `main.py`, DeepSpeed, Accelerate, feature extraction, Hugging Face `OpenGVLab/internimage_*` | [sub-skills/classification/SKILL.md](sub-skills/classification/SKILL.md) | The task is image classification, backbone hidden states, classification training/evaluation, or Transformers usage. |
| COCO, LVIS, OpenImages, VOC, CrowdHuman, MMDetection, Mask R-CNN, Cascade, DINO, bbox/mask mAP, detection image demo, SAM-prompted masks | [sub-skills/detection/SKILL.md](sub-skills/detection/SKILL.md) | The task is object detection or instance segmentation with the MMDetection 2.x InternImage stack. |
| ADE20K, Cityscapes, COCO-Stuff, Mapillary, NYU Depth V2, Pascal Context, MMSegmentation, UperNet, SegFormer, Mask2Former, mIoU, segmentation image demo | [sub-skills/segmentation/SKILL.md](sub-skills/segmentation/SKILL.md) | The task is semantic segmentation with the MMSegmentation 0.x InternImage stack. |
| Occupancy prediction, BEVFormerOcc, Online HD Map Construction, VectorMapNet, OpenLane-V2, topology metrics, lane centerlines, traffic elements, OpenLane submission validation | [sub-skills/autonomous-driving/SKILL.md](sub-skills/autonomous-driving/SKILL.md) | The task is an InternImage autonomous-driving challenge baseline or OpenLane-V2 devkit/schema/metric workflow. |
| DCNv3, `Cuda is not availabel`, `nvcc`, CUDA toolkit, custom operators, ONNX, TensorRT, mmdeploy, export, deployment | [sub-skills/deployment/SKILL.md](sub-skills/deployment/SKILL.md) | The task is backend readiness, operator build, ONNX/TensorRT export, or cross-workflow deployment. |

## Install and backend posture

- The repository's documented runtime stacks are older OpenMMLab-era stacks. Avoid silently upgrading to MMDetection 3.x, MMSegmentation 1.x/2.x, or NumPy 2.x unless the user is intentionally porting the code.
- Common pins from repo evidence include PyTorch 1.10-1.12 with CUDA, `timm==0.6.11`, `mmcv-full==1.5.x`, `mmdet==2.28.1`, `mmsegmentation==0.27.0` or 0.29.1 for autonomous OpenLane, `numpy<2`, `pydantic==1.10.13`, and `yapf==0.40.1` for detection config formatting.
- Full model execution normally requires CUDA and the DCNv3 operator. A CPU-only command-builder check is not proof of GPU/model runtime.
- Source DCNv3 builds require a PyTorch CUDA wheel, visible CUDA devices, `CUDA_HOME`, and `nvcc`/toolkit compatibility. A GPU driver alone is not enough.
- TensorRT export additionally requires mmdeploy, TensorRT, CUDNN, and the DCNv3 TensorRT custom backend operator.

Run a safe environment summary from the root skill directory:

```bash
python scripts/check_internimage_environment.py --profile detection --profile deployment
```

For machine-readable output:

```bash
python scripts/check_internimage_environment.py --profile autonomous --json
```

## Runtime guardrails

- Do not claim that this generated skill verified full training/evaluation/export. The verified scope covered static self-containment, helper parser/dry-run checks, and a CPU OpenLane-V2 schema-validation environment; model-scale GPU work remains a user-approved runtime action.
- Do not tell users to reopen this skill's source evidence. If a command is needed, use the bundled helper in the relevant sub-skill and fill in the user's checkout, data root, checkpoints, and output paths.
- Keep checkpoint/config/data families aligned. A classification checkpoint is not a full detector/segmentor checkpoint unless the selected config explicitly uses it as a pretrained backbone.
- Treat network downloads, challenge datasets, pretrained weights, cluster launches, TensorRT builds, and long training as explicit user-controlled actions.

## Cross-cutting references

- [references/model-and-config-overview.md](references/model-and-config-overview.md) - model families, task/config families, checkpoint pairing, and routing hints.
- [references/troubleshooting.md](references/troubleshooting.md) - install/import/backend/config/data/checkpoint failures that span multiple workflows.
- [references/repo-provenance.md](references/repo-provenance.md) - source repository snapshot and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) - structured router metadata for managed repo-skill import.
