# Evaluation Workflows

## Provenance note

The bundled evaluator script adapts the metric behavior, text formats, and source-compatible flag names from the repository's Apache-2.0 evaluator. It intentionally changes runtime safety details: it accepts explicit input/output paths, does not depend on the original checkout layout, disables optional plots/animation by default, and refuses to delete a non-empty output directory unless `--overwrite` is supplied.

## Preflight checklist

Before running AP/mAP:

1. Confirm annotation and detection files are already in evaluator text format. If not, route to `conversion`.
2. Confirm the ground-truth and detection-result folders contain matching `.txt` basenames. If the sets need inspection or repair, route to `data-validation`.
3. Decide whether any classes must be ignored. Ignored classes are removed before AP/mAP denominators are built.
4. Decide whether any classes need non-default IoU thresholds.
5. Choose a new output directory, or explicitly approve `--overwrite` for a disposable old directory.
6. Leave plots and animation disabled unless the user asks for them and the optional dependency is available.

## Minimal metric run

From the evaluation sub-skill directory, run:

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir path/to/ground-truth \
  --detection-results-dir path/to/detection-results \
  --output-dir path/to/map-output \
  --quiet
```

Expected signals:

- Exit status `0`.
- Console line like `mAP = 78.48%`.
- `output.txt` and `summary.json` appear in the output directory.

If the output directory already exists and is not empty, either choose a fresh directory or rerun with `--overwrite` after confirming the previous outputs can be deleted.

## Interpreting `output.txt`

`output.txt` has four major sections:

1. `# AP and precision/recall per class`
   - Each evaluated class gets an AP line and rounded precision/recall arrays.
   - AP is a percentage; higher is better.
2. `# mAP of all classes`
   - The arithmetic mean of evaluated-class AP values.
   - Ignored classes and difficult-only classes are not part of the denominator.
3. `# Number of ground-truth objects per class`
   - Non-difficult GT object counts used as recall denominators.
4. `# Number of detected objects per class`
   - Detection counts with true-positive and false-positive totals used by the metric.
   - If detections matched difficult objects, an `ignored:<N>` field may appear because those detections are neither TP nor FP for AP.
   - A class that appears only in detections can appear here with `tp:0` and all detections as false positives.

`summary.json` repeats the same information in machine-readable form and includes the default IoU, per-class IoU overrides, ignored classes, AP values, TP/FP counts, and precision/recall arrays.

## Ignore classes

Use `--ignore` when a class should be removed from both the ground-truth denominator and detection summaries:

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir path/to/ground-truth \
  --detection-results-dir path/to/detection-results \
  --output-dir path/to/map-output-ignore \
  --ignore aeroplane tvmonitor \
  --quiet
```

Important consequences:

- Ignored classes do not receive AP values.
- Ignored classes do not contribute to mAP.
- You cannot set a class-specific IoU for a class that is ignored in the same run.
- If all non-difficult classes are ignored, the run fails because no evaluable class remains.

## Per-class IoU thresholds

The default IoU threshold is `0.5`, matching the VOC-style evaluator. Override one or more classes with `--set-class-iou`:

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir path/to/ground-truth \
  --detection-results-dir path/to/detection-results \
  --output-dir path/to/map-output-iou \
  --set-class-iou person 0.7 car 0.6 \
  --quiet
```

Use this when benchmark rules require stricter or looser matching for selected classes. Validation happens after ignored classes are removed, so the class must still be present in non-difficult ground truth.

## Optional plots

Plots are optional and require `matplotlib`. They are not part of the minimum evaluation environment.

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir path/to/ground-truth \
  --detection-results-dir path/to/detection-results \
  --output-dir path/to/map-output-plots \
  --plot
```

When enabled, plots are saved as PNG files in the output directory. The wrapper uses a non-interactive backend and does not call a GUI display.

If `matplotlib` is absent, rerun without `--plot` for metric-only evaluation or install the optional dependency in the active environment.

## Optional animation / annotated frames

Animation is optional and requires `opencv-python` plus an image folder whose basenames match the GT/DR file ids.

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir path/to/ground-truth \
  --detection-results-dir path/to/detection-results \
  --images-dir path/to/images-optional \
  --output-dir path/to/map-output-animation \
  --animation
```

The bundled wrapper writes saved annotated frames instead of opening a GUI window:

- `images/detections_one_by_one/<class>_detection<N>.jpg`
- `images/<image_name>.jpg` cumulative annotated images

If `opencv-python` is absent, or images are missing/multiple for a basename, rerun without `--animation` or fix the optional image setup.

