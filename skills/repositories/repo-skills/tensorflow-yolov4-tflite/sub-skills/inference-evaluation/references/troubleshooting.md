# Inference and Evaluation Troubleshooting

## `detect.py` or `detectvideo.py` cannot load a model

**Symptoms**

- `OSError` or `NotFoundError` from `tf.saved_model.load`.
- `ValueError` from TFLite interpreter creation.
- Input/output tensor details do not match expected YOLO outputs.

**Recovery**

1. Confirm `--framework`: use `tf` for SavedModel, `tflite` for `.tflite`, and
   `trt` only for TF-TRT SavedModel paths that the script treats like SavedModel.
2. Confirm the artifact exists and was produced with matching `--model`,
   `--tiny`, and `--input_size` choices.
3. For TFLite, run a minimal `tf.lite.Interpreter(...).allocate_tensors()` check
   before running full detection.
4. If the model was custom trained, confirm class count and class-file order
   before interpreting labels.

## OpenCV cannot read the input image or video

**Symptoms**

- `cv2.cvtColor` fails after `cv2.imread` returned `None`.
- Video route raises `ValueError: No image! Try with another video format`.
- Output image/video is not created.

**Recovery**

- Check the path and file extension before launching TensorFlow.
- Use absolute input paths when the command is not launched from the checkout
  root.
- On headless systems, use video `--dis_cv2_window` and supply `--output`.
- For video output, try a codec available on the host, such as `XVID`, or change
  the container format.

## Boxes appear shifted, scaled, or missing

**Likely causes**

- Input size mismatch between conversion and inference.
- Wrong model family/tiny flag.
- TFLite output tensor order mismatch.
- Thresholds too strict for a poorly calibrated or quantized model.

**Recovery**

1. Re-run on a known image with the float32 SavedModel baseline.
2. Confirm `--size` matches the conversion `--input_size`.
3. Lower `--score` temporarily to inspect whether boxes exist before NMS.
4. Compare TFLite output order against the branch in `detect.py` for the exact
   model/tiny combination.
5. For int8 artifacts, compare against float32/float16 before deployment.

## Evaluation uses the wrong annotation file

**Symptom**: `--annotation_path` appears ignored or the line count differs from
processed examples.

**Cause**: `evaluate.py` counts lines from `FLAGS.annotation_path` but opens
`cfg.TEST.ANNOT_PATH` for the actual loop.

**Recovery**

- Edit `core.config.cfg.TEST.ANNOT_PATH` in the target checkout to match the
  intended file, or patch `evaluate.py` to iterate over `FLAGS.annotation_path`.
- Validate the annotation-line format with the training-data sub-skill before
  running evaluation.
- Keep a backup of existing `mAP/predicted` and `mAP/ground-truth` outputs if
  they matter; `evaluate.py` deletes and recreates them.

## mAP tool fails after `evaluate.py`

**Symptoms**

- Missing files under `mAP/predicted` or `mAP/ground-truth`.
- Class names do not match or contain spaces.
- `mAP/main.py` produces empty or misleading metrics.

**Recovery**

1. Confirm `evaluate.py` processed at least one annotation line.
2. Run the mAP extra cleanup step for class names with spaces when using the
   repository's mAP workflow.
3. Confirm the class IDs in annotations map to names in the class file.
4. Run a tiny subset first before full COCO evaluation.

## Benchmark numbers are misleading

**Symptoms**

- GPU host but TensorFlow logs CPU fallback.
- TF-TRT benchmark uses a non-TRT SavedModel.
- Results differ wildly across runs.

**Recovery**

- Print TensorFlow GPU devices in the benchmark environment before timing.
- Name the artifact, precision, input size, and backend in any report.
- Ignore the first warmup iteration and avoid running other heavy GPU jobs on
  the same device.
- If comparing to README tables, match hardware generation and TensorRT/TensorFlow
  versions; the README numbers are historical, not universal guarantees.
