# Model and Config Family Overview

YOLOv7-d2 extends Detectron2 with several detector and segmentation families. Pick the workflow by `MODEL.META_ARCHITECTURE`, config path, and script family.

## Registered meta-architectures observed

- YOLO-style: `YOLO`, `YOLOV5`, `YOLOV6`, `YOLOV7`, `YOLOV7P`, `YOLOX`, `YOLOMask`, `YOLOF`.
- Instance segmentation: `SparseInst`, `SOLOv2`, plus `YOLOMask`.
- Transformer detectors: `Detr`, `AnchorDetr`, `SMCADetr`, `DetrD2go`.

## Representative config families

- Base YOLOv7: `MODEL.META_ARCHITECTURE: YOLOV7`, `configs/Base-YOLOv7.yaml` style.
- YOLOX: `MODEL.META_ARCHITECTURE: YOLOX`, e.g. COCO/custom YOLOX configs.
- YOLOv5/YOLOv6: same Detectron2 config pattern with the corresponding meta-architecture.
- SparseInst: `MODEL.META_ARCHITECTURE: SparseInst`, RGB image format, mask-specific evaluator needs.
- DETR-family: `Detr`, `AnchorDetr`, `SMCADetr`, `DetrD2go`, often RGB and `SOLVER.OPTIMIZER: ADAMW`.
- LazyConfig examples: Python configs under a Detectron2 LazyConfig shape with `model`, `dataloader`, `optimizer`, `lr_multiplier`, and `train` objects.

## Training route summary

- Standard YOLO-family detection: route to `training-and-configuration`; use the standard training launcher pattern and `MyDatasetMapper2`.
- SparseInst / mask-only instance segmentation: route to `training-and-configuration`; use the instance-segmentation trainer pattern and `COCOMaskEvaluator` behavior.
- DETR-family: route to `training-and-configuration`; use the DETR trainer pattern with `DetrDatasetMapper` and DETR optimizer settings.
- LazyConfig: route to `training-and-configuration`; use the LazyConfig launcher pattern, not the broken LazyConfig demo.

## Inference/deployment route summary

- PyTorch checkpoint demo visualization: route to `inference-and-evaluation`.
- COCO evaluation over an existing checkpoint: route to `inference-and-evaluation`.
- ONNX export or ONNXRuntime inference: route to `deployment-and-export`.
- DETR checkpoint conversion from external reference implementations: route to `deployment-and-export`.

## Known config caveats

Some config files use base-file names such as `Base-YoloV7.yaml` that differ in case from the observed `Base-YOLOv7.yaml`. On case-sensitive filesystems, this causes config merge failures. Fix the base path or use a config whose `_BASE_` resolves before debugging model code.

The README mentions WIP and closed-source features. Do not claim a model family is usable unless its config/source exists in the user's version and dependencies import successfully.
