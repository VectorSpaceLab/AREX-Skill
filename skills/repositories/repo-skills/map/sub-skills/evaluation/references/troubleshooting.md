# Evaluation Troubleshooting

## Missing input folders or no `.txt` files

Symptom:

```text
Error: Missing ground-truth directory: ...
Error: No .txt files found in detection-results directory: ...
```

Recovery:

- Point `--ground-truth-dir` and `--detection-results-dir` at directories, not individual files.
- If annotations are not in evaluator text format yet, route to `conversion`.
- If files exist with a different extension, convert or rename them before evaluation.

## Ground-truth and detection-result basenames do not match

Symptom:

```text
Error: Ground-truth and detection-results file sets must match by basename; missing detection-results .txt for image ids: ...
```

Recovery:

- Use matching names such as `image_1.txt` in both folders.
- If one side has extra or missing files, route to `data-validation` for intersection reporting or safe repair.
- Do not paper over a missing detection-result file unless the intended benchmark semantics are clear; the source evaluator treats mismatched file sets as an error.

## Wrong ground-truth row format

Expected ground-truth row:

```text
<class_name> <left> <top> <right> <bottom> [difficult]
```

Common causes:

- Class names contain spaces. Replace spaces with a single token such as `traffic_light`.
- The optional difficult marker is misspelled or not the final token.
- Coordinates are missing, non-numeric, or ordered as `xmin ymin width height` instead of `left top right bottom`.
- `right < left` or `bottom < top`.

Recovery:

- Fix the text files or route source annotations to `conversion`.
- Keep only one object per line.
- Use pixel coordinates in the same image coordinate system as the detections.

## Wrong detection-result row format

Expected detection row:

```text
<class_name> <confidence> <left> <top> <right> <bottom>
```

Common causes:

- Missing confidence value.
- Confidence or coordinates are non-numeric.
- Detector output is still in JSON, YOLO normalized, darknet stdout, or another source format.
- Class names contain spaces.

Recovery:

- Route non-evaluator formats to `conversion`.
- Confirm confidence is a score where larger means more confident; detections are sorted in descending score order before matching.

## Optional dependency warnings

Plots:

```text
Error: Optional dependency "matplotlib" is not installed. Omit --plot or install matplotlib.
```

Animation:

```text
Error: Optional dependency "opencv-python" is not installed. Omit --animation or install opencv-python.
```

Recovery:

- For metric-only AP/mAP, rerun without `--plot` and without `--animation`.
- Install optional dependencies only if the user needs visualization artifacts.
- Optional visualization dependencies are not required for the minimum evaluation scope.

## Output directory already exists

Symptom:

```text
Error: Output directory already exists and is not empty. Choose a new --output-dir or pass --overwrite...
```

Recovery:

- Prefer a new output directory for each comparison run.
- Use `--overwrite` only when the old contents are disposable. The wrapper will delete and recreate the output directory.
- If a parent directory does not exist, the wrapper creates it.

## Invalid `--set-class-iou`

Common symptoms:

```text
Error: --set-class-iou requires CLASS IOU pairs...
Error: Unknown or ignored class "..." in --set-class-iou...
Error: IoU for class "..." must be between 0.0 and 1.0...
Error: Duplicate class "..." in --set-class-iou.
```

Recovery:

- Provide complete `CLASS IOU` pairs.
- Use a class name exactly as it appears in non-ignored, non-difficult ground truth.
- Remove classes that are also passed to `--ignore`.
- Use numeric thresholds strictly greater than `0.0` and strictly less than `1.0`.

## Ignored-class behavior surprises

Symptoms:

- A class passed to `--ignore` is absent from AP and mAP.
- `--set-class-iou` fails for an ignored class.
- The run fails because no evaluable ground-truth objects remain.

Recovery:

- Use `--ignore` only for classes that should be completely excluded from evaluation.
- If a class should remain in mAP with a different matching threshold, do not ignore it; use `--set-class-iou` instead.
- If all objects are `difficult` or ignored, add at least one non-difficult GT object or narrow the run to a valid class set.

## Repeated detections and difficult boxes

Expected behavior:

- The highest-confidence detection that matches an unused, non-difficult GT box at the class IoU threshold is TP.
- A later detection matching the same non-difficult GT box is FP.
- A detection matching a difficult GT box at threshold is ignored, not TP and not FP.
- The bundled wrapper records difficult matches as `ignored_detections` in `summary.json` and may show `ignored:<N>` in the detected-object summary.

If these counts look wrong, inspect `summary.json` precision/recall arrays and verify that detector confidences sort in the expected order.

## Animation image errors

Symptoms:

```text
Error: Animation requested but no image file matches id 'image_1'...
Error: Animation requested but multiple image files match id 'image_1'...
```

Recovery:

- Place optional image files in the folder passed to `--images-dir`.
- Ensure each image basename matches one `.txt` id exactly.
- Avoid duplicate extensions for the same id, such as both `image_1.jpg` and `image_1.png`.
- Rerun without `--animation` if images are not needed.
