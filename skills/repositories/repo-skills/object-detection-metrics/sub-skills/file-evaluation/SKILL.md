---
name: file-evaluation
description: "Folder-based PASCAL VOC AP/mAP evaluation from ground-truth and
  detection text files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# file-evaluation

Use this sub-skill when the user wants PASCAL VOC Average Precision (AP) or mean AP (mAP) from folders of ground-truth and detection `.txt` files, including YOLO-style relative detections, mixed `xywh`/`xyrb` coordinate formats, or a noninteractive replacement for the legacy `pascalvoc.py` workflow.

## Route here for

- Compute VOC AP or mAP from `groundtruths/` and `detections/` text folders.
- Evaluate detection text files with an IoU threshold such as `0.3`, `0.5`, or `0.75`.
- Convert relative YOLO-like `center_x center_y width height` boxes to VOC AP/mAP with a fixed image size.
- Avoid the original script's save-path prompt/deletion and plotting behavior.

## Route away

- Direct construction of `BoundingBox`, `BoundingBoxes`, or `Evaluator` objects, custom in-memory metrics, 11-point AP choices, or drawing/plotting API behavior: use `../python-api/SKILL.md`.
- COCO metrics, successor UI/new-tool workflows, video metrics, model training, or detector inference are outside this legacy sub-skill.

## Required inputs

1. A ground-truth folder containing one `.txt` file per image id.
2. A detection folder containing one `.txt` file per image id.
3. The coordinate format for each folder:
   - `xywh`: absolute `left top width height`; for relative coordinates this means YOLO-style `center_x center_y width height`.
   - `xyrb`: absolute `left top right bottom` / `XYX2Y2`.
4. Coordinate reference for each folder: `abs` or `rel`.
5. `WIDTH,HEIGHT` image size if either folder uses `rel` coordinates.
6. IoU threshold for TP/FP matching. Default is `0.5`.

See `references/file-format.md` for exact schemas, matching rules, and relative-coordinate conversion.

## Noninteractive helper

The bundled helper is self-contained and uses only the Python standard library:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder /path/to/groundtruths \
  --det-folder /path/to/detections \
  --threshold 0.5 \
  --gt-format xywh --det-format xywh \
  --gt-coords abs --det-coords abs \
  --output-text voc-results.txt \
  --output-json voc-results.json \
  --pretty
```

For YOLO-like relative detections against absolute ground truth:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder /path/to/groundtruths \
  --det-folder /path/to/detections_rel \
  --threshold 0.3 \
  --gt-format xywh --det-format xywh \
  --gt-coords abs --det-coords rel \
  --img-size 200,200 \
  --output-text voc-results.txt
```

The helper never plots, never prompts, and never deletes an output directory. It prints to stdout when no output file is requested and creates only the explicit `--output-text` and/or `--output-json` files.

## Output contract

Text output contains:

- IoU threshold.
- Any validation warnings, such as unmatched file stems.
- Per-class AP percentage, precision array, recall array, total positives, total TP, and total FP.
- Final `mAP` percentage.

JSON output contains:

- `metric`, `threshold`, `classes`, `valid_classes`, `ignored_classes`, `mAP`, `mAP_percent`, and `warnings`.
- Each item in `classes` includes `class`, `AP`, `AP_percent`, `precision`, `recall`, `interpolated_precision`, `interpolated_recall`, `total positives`, `total TP`, and `total FP`.

## Evaluation semantics

- AP uses VOC every-point interpolation, the default behavior of the legacy toolkit.
- IoU uses inclusive VOC pixel area (`+1` in width and height).
- Detections are sorted by descending confidence within each class.
- A ground-truth box can be matched once. Duplicate detections of the same object become false positives after the first match.
- mAP is the mean of AP values over classes with at least one ground-truth positive; detection-only classes are ignored with a warning.

## Standard workflow

1. Validate folder existence and text-line schema before running.
2. Confirm file stems match image ids across ground-truth and detection folders.
3. Select `--gt-format` and `--det-format`; wrong `xywh` vs `xyrb` selection can silently change IoU/AP.
4. If using `rel`, add `--img-size WIDTH,HEIGHT` and keep format `xywh`.
5. Run the helper with `--output-json` for machine-readable reports or `--output-text` for a VOC-like summary.
6. Interpret AP/mAP using `references/workflows.md`; troubleshoot failures using `references/troubleshooting.md`.

## Evidence distilled

This sub-skill is distilled from the repository's `README.md` PASCAL VOC metrics and CLI guidance, `pascalvoc.py` parser/evaluation behavior, the tiny text fixtures in `groundtruths/`, `detections/`, `groundtruths_rel/`, `detections_rel/`, `samples/sample_2/README.md`, and the sample output shape in `results/results.txt`.
