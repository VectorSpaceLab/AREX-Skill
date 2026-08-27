---
name: detection
description: "Object detection and instance segmentation with InternImage in
  MMDetection 2.x, including config selection, command templates, custom plugin
  registration, SAM-prompted masks, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# InternImage Detection Sub-skill

Use this sub-skill when the user is working with InternImage object detection or instance segmentation on the repository's MMDetection 2.x stack: choosing COCO, LVIS, OpenImages, VOC, or CrowdHuman configs; building train/test/demo commands; diagnosing custom MMDetection registry issues; or planning SAM-prompted masks from detector boxes.

## Operating flow

1. Identify the user's goal: train, distributed train, test/evaluate, distributed test, single-image demo, or SAM-prompted instance segmentation.
2. Choose a compatible config family from `references/config-catalog.md`; keep the dataset, detector head, backbone size, checkpoint, and evaluation metric aligned.
3. Generate a dry-run shell template with `scripts/build_detection_command.py` instead of copying source launch snippets by hand. The helper prints commands only and never runs training, inference, downloads, or CUDA builds.
4. Before execution, check `references/workflows.md` for environment, data, output, distributed, Slurm, and custom-plugin requirements.
5. For SAM workflows, read `references/sam-integration.md` before choosing a detector config or SAM checkpoint.
6. If an import, registry, DCNv3, dataset, checkpoint, output, distributed, or SAM error occurs, use `references/troubleshooting.md` first.

## Runtime guardrails

- Full detection training/evaluation/demo/SAM runs require a prepared OpenMMLab environment, local datasets, checkpoints, GPU-compatible PyTorch, and usually the DCNv3 CUDA extension. This generated skill only verified self-contained files and helper behavior.
- The detection stack is the MMDetection 2.28-era API. Do not silently translate these configs to MMDetection 3.x commands.
- Preserve custom registration: the source entrypoints import `mmcv_custom` and `mmdet_custom` before model or dataset construction, and InternImage backbones import the local `ops_dcnv3` package.
- TensorRT/mmdeploy export is a deployment workflow. Route detailed export/build tasks to the sibling deployment sub-skill; keep only detection config/checkpoint selection here.
- Do not ask users to open original repository docs or scripts for instructions; use the bundled references and helper script.

## Command-builder examples

```bash
# List distilled detection config keys.
python scripts/build_detection_command.py --list-configs

# Build a one-GPU COCO Mask R-CNN evaluation template.
python scripts/build_detection_command.py test \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/mask_rcnn_internimage_t_fpn_1x_coco \
  --checkpoint checkpoints/mask_rcnn_internimage_t_fpn_1x_coco.pth \
  --eval bbox segm

# Build a distributed DINO evaluation template.
python scripts/build_detection_command.py dist-test \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/dino_4scale_internimage_t_1x_coco_layer_wise_lr \
  --checkpoint checkpoints/dino_4scale_internimage_t_1x_coco.pth \
  --gpus 8 --eval bbox

# Build a single-image visualization template.
python scripts/build_detection_command.py image-demo \
  --repo-root <INTERNIMAGE_REPO> \
  --image images/example.jpg \
  --config-key coco/mask_rcnn_internimage_t_fpn_1x_coco \
  --checkpoint checkpoints/mask_rcnn_internimage_t_fpn_1x_coco.pth \
  --device cuda:0 --palette coco --out demo

# Build a SAM-prompted mask-evaluation template.
python scripts/build_detection_command.py sam \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/mask_rcnn_internimage_t_fpn_1x_coco \
  --checkpoint checkpoints/mask_rcnn_internimage_t_fpn_1x_coco.pth \
  --sam-checkpoint checkpoints/sam_vit_b.pth \
  --sam-type vit_b --eval segm --out sam_results.pkl
```

## Bundled materials

- `references/workflows.md` - train/test/demo/distributed/Slurm workflows, output semantics, custom plugin registration, and export routing.
- `references/config-catalog.md` - distilled model/config families, dataset roots, metric choices, and checkpoint compatibility notes.
- `references/sam-integration.md` - detector plus Segment Anything route, requirements, command shape, and limitations.
- `references/troubleshooting.md` - detection-specific failure modes and fixes.
- `scripts/build_detection_command.py` - standalone dry-run command builder for `train`, `dist-train`, `test`, `dist-test`, `image-demo`, and `sam` modes.
