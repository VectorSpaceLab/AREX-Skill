---
name: inference-visualization
description: "Run Detectron2 inference, inspect model outputs, and visualize
  predictions safely without depending on the source demo script."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detectron2 Inference & Visualization

Use this sub-skill when a task asks to run Detectron2 inference, call `DefaultPredictor`, call a built model directly, inspect `Instances`/`Boxes`/masks, visualize predictions, plan demo-style image/video/webcam commands, or validate COCO-style prediction JSON before drawing it.

## Fast Routing

- For simple single-image inference, read [references/inference-workflows.md](references/inference-workflows.md#defaultpredictor-single-image-inference) and use `DefaultPredictor(cfg)` only when weights are local or downloads are intentional.
- For batch/direct model calls, read [references/inference-workflows.md](references/inference-workflows.md#direct-model-inference) and use `build_model(cfg)`, `DetectionCheckpointer(model).load(...)`, `model.eval()`, and `model([input_dict])[0]`.
- For output parsing, field checks, JSON conversion, and visualization requirements, read [references/structures-and-outputs.md](references/structures-and-outputs.md).
- For broken demo imports, OpenCV issues, CPU/CUDA mismatches, empty predictions, metadata labels, or output side effects, read [references/troubleshooting.md](references/troubleshooting.md).
- Build a safe demo-style command without executing it through [scripts/demo_command_builder.py](scripts/demo_command_builder.py).
- Validate COCO-style prediction JSON without drawing or importing Detectron2 through [scripts/visualize_json_schema_check.py](scripts/visualize_json_schema_check.py).

## Safe Defaults

- Set inference device before model or predictor construction: Yacs configs use `cfg.MODEL.DEVICE = "cpu"` or the CLI override `MODEL.DEVICE cpu`.
- Do not instantiate `DefaultPredictor` during no-download validation if `cfg.MODEL.WEIGHTS` points to a URL or `detectron2://` URI; it loads weights during construction.
- Treat OpenCV images as BGR, but pass RGB images to `Visualizer`; convert with `image_rgb = image_bgr[:, :, ::-1]`.
- Move predictions to CPU before visualization: `instances = outputs["instances"].to("cpu")`.
- Check `instances.has("pred_boxes")`, `instances.has("scores")`, and metadata class names before assuming labels or boxes exist.

## Boundaries

This sub-skill owns inference calls, model input/output formats, `Instances`, `Boxes`, `BoxMode`, `BitMasks`, `PolygonMasks`, `ImageList`, `Visualizer`, `ColorMode`, demo-style flags, confidence thresholds, CPU overrides, and prediction JSON sanity checks.

Route model-zoo config/checkpoint selection to `../configuration-model-zoo/`. Route dataset registration, catalog metadata, and dataset dict validation to `../data-datasets/`. Route training, evaluation loops, evaluators, and metrics to `../training-evaluation/`. Route TorchScript, tracing, Caffe2, and deployment packaging to `../deployment-export/`.
