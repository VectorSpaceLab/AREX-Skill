# Inference and Visualization Troubleshooting

## Original Demo Import Fails

Symptom:

```text
ModuleNotFoundError: No module named 'vision'
```

Cause: this checkout's demo script imports `vision.fair.detectron2.demo.predictor`, so it is not a reliable runtime dependency.

Fix:

- Do not instruct future agents to run the original demo script from the repository checkout.
- Use `scripts/demo_command_builder.py` to validate flags and print a safe command shape.
- For real inference, write a small wrapper using `DefaultPredictor` or direct model calls from [inference-workflows.md](inference-workflows.md).

## OpenCV Missing or GUI Unavailable

Symptoms:

- `ImportError` or `ModuleNotFoundError` for `cv2`.
- OpenCV window calls fail in headless environments.
- Video codec errors when writing `.mp4` or `.mkv`.

Fix:

- Install an OpenCV package appropriate for the environment; headless environments usually need an OpenCV headless build.
- Prefer saving image/video outputs over `cv2.imshow` in non-interactive sessions.
- Avoid webcam mode unless the user confirms camera access and interactivity.
- Treat codec support as environment-dependent; do not overwrite existing video outputs.

## CPU and CUDA Device Mismatch

Symptoms:

- Tensor/device mismatch errors.
- CUDA unavailable errors on a CPU-only machine.
- Inference silently planned for the wrong device.

Fix:

- Set `cfg.MODEL.DEVICE = "cpu"` before constructing `DefaultPredictor` or `build_model(cfg)` for CPU-only work.
- For commands, include `--opts MODEL.DEVICE cpu`.
- Move visualization data to CPU: `outputs["instances"].to("cpu")`, `sem_seg.to("cpu")`, and `panoptic_seg.to("cpu")`.
- For direct calls, put image tensors on the same device expected by the model.

## Missing Weights or Unexpected Downloads

Symptoms:

- `DetectionCheckpointer` cannot find a local path.
- Runtime tries to download `detectron2://` or URL weights.
- Validation unexpectedly becomes slow or network-dependent.

Fix:

- Remember that `DefaultPredictor(cfg)` loads `cfg.MODEL.WEIGHTS` during construction.
- For no-download validation, inspect configs only and leave `cfg.MODEL.WEIGHTS = ""` or point it to an existing local checkpoint.
- Route model-zoo config/checkpoint selection to `../configuration-model-zoo/`.
- Ask before allowing network downloads in constrained or reproducibility-sensitive workflows.

## BGR/RGB Channel Confusion

Symptoms:

- Output colors look swapped.
- Visualizations have blue/red inversions.

Fix:

- OpenCV reads BGR; `DefaultPredictor` expects BGR and converts internally when `cfg.INPUT.FORMAT == "RGB"`.
- `Visualizer` expects RGB; convert with `image_rgb = image_bgr[:, :, ::-1]`.
- If saving through OpenCV, convert visualizer RGB output back to BGR.

## Instances Field Access Errors

Symptoms:

```text
AttributeError: Cannot find field 'pred_boxes' in the given Instances!
NotImplementedError: Empty Instances does not support len()!
```

Fix:

- Use `instances.has("pred_boxes")` before `instances.pred_boxes`.
- Use `instances.get_fields().keys()` to inspect available fields.
- Do not call `len()` on an `Instances` object with no fields.
- For visualization, ensure at least one drawable field exists: `pred_boxes`, `pred_masks`, or keypoints with compatible labels.
- If the object has proposal fields (`proposal_boxes`, `objectness_logits`) instead of prediction fields, it is probably a proposal/debug output, not final detections.

## Missing Metadata Class Names or Colors

Symptoms:

- Labels are numeric ids instead of class names.
- `ColorMode.SEGMENTATION` does not use expected class colors.
- Class index is out of range for metadata labels.

Fix:

- Confirm `cfg.DATASETS.TEST` points to a registered dataset when using `DefaultPredictor.metadata`.
- Use `MetadataCatalog.get(dataset_name).set(thing_classes=[...])` for custom labels; route dataset registration details to `../data-datasets/`.
- Check that `pred_classes` are contiguous ids aligned with `thing_classes`, not raw COCO dataset ids.
- For JSON rows, map `category_id` through dataset metadata before setting `pred_classes`.

## Empty Predictions After Inference

Symptoms:

- `outputs` contains `instances`, but it has zero detections.
- Visualizer returns the original image or very little overlay.

Fix:

- Lower score thresholds only after confirming the correct weights, class count, input channel order, and device.
- Check `instances.has("scores")` and inspect score ranges before changing thresholds.
- Confirm the image actually contains target classes and is not too small or heavily resized.
- Empty predictions can be valid; do not treat them as a schema error by themselves.

## Output Path and Side Effects

Symptoms:

- Image output path is a directory when a single file was expected, or vice versa.
- Video output overwrites an existing file.
- Webcam mode is requested with `--output`.

Fix:

- For image inputs, use an output directory for multiple images and a file path for one image.
- For video input, use a file output path or an output directory where a derived filename can be created.
- Avoid output for webcam mode unless a custom wrapper explicitly supports it.
- Use `scripts/demo_command_builder.py` to catch mutually exclusive or unsafe flag combinations before execution.

## JSON Prediction Schema Problems

Symptoms:

- Drawing JSON predictions fails with missing `image_id`, `bbox`, `score`, or `category_id`.
- Boxes appear in the wrong location.
- Metadata class ids do not match labels.

Fix:

- Validate with `scripts/visualize_json_schema_check.py` before drawing.
- Treat COCO JSON `bbox` as `XYWH_ABS` and convert to `XYXY_ABS` before creating `Boxes`.
- Confirm `score` is numeric and within the expected range.
- Confirm `category_id` uses the dataset id space and map it to contiguous ids when needed.
