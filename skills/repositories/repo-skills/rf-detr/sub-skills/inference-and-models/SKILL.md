---
name: inference-and-models
description: "Use RF-DETR model variants, checkpoints, prediction outputs, video
  and stream inference, labels, and inference troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RF-DETR Inference and Models

Use this sub-skill when the task is to run or diagnose RF-DETR prediction code, choose a detection / segmentation / keypoint model class, load a checkpoint, interpret `supervision` outputs, handle class names, tune inference memory, or explain Plus model boundaries.

Do not use this sub-skill for fine-tuning, Lightning CLI, dataset schema work, export/deployment formats, or source-repository contribution policy; route those tasks to sibling sub-skills when available:

- `../training-and-cli/SKILL.md` for `train()`, `evaluate()`, datasets, configs, and CLI.
- `../export-and-deployment/SKILL.md` for ONNX, TensorRT, TFLite, ExecuTorch, CoreML, and Roboflow deployment bundles.
- `../repository-development/SKILL.md` for modifying RF-DETR source, tests, docs, packaging, or CI.

## Runtime map

- API surface, class tables, signatures, checkpoint trust rules, output fields, and label mapping: [references/api-reference.md](references/api-reference.md)
- Recipes for image, batch, video, webcam, RTSP, keypoint visualization, checkpoint loading, and memory optimization: [references/workflows.md](references/workflows.md)
- Failure diagnosis for imports, downloads, checkpoints, shapes, labels, keypoints, video sources, devices, and Plus models: [references/troubleshooting.md](references/troubleshooting.md)
- Safe installed-package inspector that does not download weights or instantiate models: [scripts/inspect_rfdetr_models.py](scripts/inspect_rfdetr_models.py)

## Quick decision rules

1. Default new detection examples to `RFDETRSmall` / `"rfdetr-small"`; do not introduce new `RFDETRBase` or `"rfdetr-base"` examples.
2. Use a sized segmentation model (`RFDETRSegNano`, `RFDETRSegSmall`, `RFDETRSegMedium`, `RFDETRSegLarge`, `RFDETRSegXLarge`, `RFDETRSeg2XLarge`); do not use `RFDETRSegPreview` for new work.
3. Keypoints are preview-only: use `RFDETRKeypointPreview` / `"rfdetr-keypoint-preview"` only for keypoint tasks.
4. Prefer `detections.data["class_name"]` or `key_points.data["class_name"]` for labels. `COCO_CLASSES` is only for manually mapping COCO-pretrained sparse category IDs.
5. For fine-tuned checkpoints, load with `RFDETR.from_checkpoint(path)` or `rfdetr.from_checkpoint(path)` and leave `trust_checkpoint=False` unless the checkpoint source is fully trusted.
6. For memory-constrained prediction, consider `include_source_image=False` first; use `model.inference(compile=False, inplace=True, dtype="float16")` only when the destructive, inference-only trade-off is acceptable.
