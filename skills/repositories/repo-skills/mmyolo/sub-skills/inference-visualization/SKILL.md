---
name: inference-visualization
description: "Guide MMYOLO image/video inference, LabelMe export, large-image
  tiling, feature-map visualization, and CAM analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# MMYOLO inference and visualization

Use this sub-skill when the task is to run or plan MMYOLO inference on images, folders, URLs, or videos; save visualized detections or LabelMe annotations; inspect `DetDataSample` predictions; tile large images with SAHI-style merging; or create feature-map / BoxAM / Grad-CAM visualizations.

## Read order

1. Read [references/inference-visualization.md](references/inference-visualization.md) for command recipes, output semantics, and validation checklists.
2. Read [references/api-reference.md](references/api-reference.md) when the user needs Python API access, `DetDataSample.pred_instances`, LabelMe writing, or large-image merge internals.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for device, dependency, TTA, LabelMe, video, SAHI, and Grad-CAM failures.
4. Use [scripts/mmyolo_infer_image_command.py](scripts/mmyolo_infer_image_command.py) to build a safe self-contained image/folder/URL inference command. The helper only emits a command/template; it does not run inference.

## Fast routing

- **Image, directory, or URL inference**: use the bundled command builder or the API recipe; set `--device cpu` for a CPU-only run and provide a matching config/checkpoint.
- **LabelMe export**: use `--to-labelme`; add `--class-name ...` only for class-filtered LabelMe shapes. `--show` and `--to-labelme` are mutually exclusive.
- **Programmatic results**: use `mmdet.apis.init_detector` and `inference_detector`; read `result.pred_instances.bboxes`, `.scores`, and `.labels`.
- **Video / large-image / feature-map / BoxAM**: use the reference recipes; they need media files, checkpoints, and sometimes optional packages.

## Route away

- Training, testing, AP metrics, prediction JSON/PKL dumps, distributed launch, AMP, or resume -> `training-evaluation`.
- Dataset conversion, COCO/YOLO/LabelMe data preparation, annotation browsing, or anchor optimization -> `data-tools`.
- ONNX/TensorRT/RKNN/MMDeploy/EasyDeploy export or inference from backend artifacts -> `deployment-conversion`.

## Operating boundaries

Do not rely on MMYOLO source-checkout demo scripts in runtime commands. Use installed MMYOLO/MMDetection APIs and the bundled helper/templates here. Avoid downloads unless the user explicitly supplied or approved the source URL/checkpoint acquisition.
