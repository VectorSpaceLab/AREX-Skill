# Folder evaluation workflows

Use `scripts/voc_metrics_eval.py` for unattended PASCAL VOC AP/mAP evaluation from text folders. The helper is self-contained, standard-library-only, noninteractive, and plot-free.

## Quick decision table

| User request | Use these flags |
|---|---|
| Default VOC-style AP/mAP from text folders | `--gt-folder`, `--det-folder`, optional `--threshold` |
| Ground truth or detections are `left top right bottom` | Add `--gt-format xyrb` and/or `--det-format xyrb` |
| Detections are YOLO-style relative center/size | Add `--det-coords rel --img-size WIDTH,HEIGHT` |
| Ground truth is YOLO-style relative center/size | Add `--gt-coords rel --img-size WIDTH,HEIGHT` |
| Need machine-readable results | Add `--output-json metrics.json --pretty` |
| Need VOC-like text summary | Add `--output-text results.txt` |
| Need custom in-memory metrics or plotting | Route to `../python-api/SKILL.md` |

## 1. Absolute `xywh` folders

Expected line schemas:

```text
# ground truth
class left top width height

# detection
class confidence left top width height
```

Command:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder <groundtruths> \
  --det-folder <detections> \
  --threshold 0.5 \
  --gt-format xywh \
  --det-format xywh \
  --output-text voc-results.txt \
  --output-json voc-results.json \
  --pretty
```

If no output path is supplied, the helper prints the text summary to stdout.

## 2. Absolute `xyrb` / `XYX2Y2` folders

Expected line schemas:

```text
# ground truth
class left top right bottom

# detection
class confidence left top right bottom
```

Command:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder <groundtruths-xyrb> \
  --det-folder <detections-xyrb> \
  --threshold 0.5 \
  --gt-format xyrb \
  --det-format xyrb \
  --output-json voc-results.json \
  --pretty
```

If only one folder uses right/bottom coordinates, set only that side to `xyrb`; the GT and detection format flags are independent.

## 3. Mixed absolute formats

Example: GT files use `left top right bottom`, detections use `left top width height`:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder <groundtruths-xyrb> \
  --det-folder <detections-xywh> \
  --threshold 0.5 \
  --gt-format xyrb \
  --det-format xywh \
  --output-text voc-results.txt
```

This is useful when annotation exports and detector exports use different box conventions. Validate a small image manually before trusting mAP, because selecting `xywh` when the data is actually `xyrb` can change IoU without producing a syntax error.

## 4. Relative YOLO-like detections

Relative coordinates are center/size, not top-left/size:

```text
class confidence center_x center_y width height
```

Command when only detections are relative:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder <groundtruths> \
  --det-folder <detections-rel> \
  --threshold 0.3 \
  --gt-format xywh \
  --det-format xywh \
  --gt-coords abs \
  --det-coords rel \
  --img-size 200,200 \
  --output-text voc-results.txt
```

Command when both folders are relative center/size values:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder <groundtruths-rel> \
  --det-folder <detections-rel> \
  --gt-coords rel \
  --det-coords rel \
  --img-size 200,200 \
  --threshold 0.5 \
  --output-json voc-results.json
```

The helper rejects relative `xyrb` because the legacy conversion is defined for YOLO-style center/size values only.

## 5. Mapping from the legacy CLI

| Legacy option | Helper option | Notes |
|---|---|---|
| `-gt` / `--gtfolder` | `--gt-folder` | Required; no checkout default is assumed. |
| `-det` / `--detfolder` | `--det-folder` | Required; no checkout default is assumed. |
| `-t` / `--threshold` | `--threshold` | Defaults to `0.5`. |
| `-gtformat` | `--gt-format` | Choices: `xywh`, `xyrb`. |
| `-detformat` | `--det-format` | Choices: `xywh`, `xyrb`. |
| `-gtcoords` | `--gt-coords` | Choices: `abs`, `rel`. |
| `-detcoords` | `--det-coords` | Choices: `abs`, `rel`. |
| `-imgsize` | `--img-size` | Required when either coordinate reference is `rel`. |
| `-np` / `--noplot` | not needed | Helper never plots. |
| `-sp` / `--savepath` | `--output-text`, `--output-json` | Helper never deletes a save directory. |

## 6. Reading text output

Text output shape:

```text
Object Detection Metrics
Self-contained PASCAL VOC every-point AP/mAP helper

IoU threshold: 0.3

Average Precision (AP), Precision and Recall per class:

Class: person
AP: 24.57%
Precision: ['1.00', '0.50', ...]
Recall: ['0.07', '0.07', ...]
Total positives: 15
Total TP: 7
Total FP: 17

mAP: 24.57%
```

- `AP` is per class.
- `mAP` is the arithmetic mean of AP over classes with at least one ground-truth positive.
- `Precision` and `Recall` arrays are accumulated in descending-confidence detection order.
- `Total FP` includes low-IoU detections, detections on images with no same-class ground truth, and duplicate detections of an already matched object.

## 7. Reading JSON output

Top-level fields:

```json
{
  "metric": "PASCAL VOC every-point AP",
  "threshold": 0.5,
  "classes": [
    {
      "class": "person",
      "AP": 0.2457,
      "AP_percent": 24.57,
      "precision": [1.0, 0.5],
      "recall": [0.0667, 0.0667],
      "interpolated_precision": [1.0, 1.0],
      "interpolated_recall": [0.0, 0.0667],
      "total positives": 15,
      "total TP": 7,
      "total FP": 17
    }
  ],
  "mAP": 0.2457,
  "mAP_percent": 24.57,
  "warnings": []
}
```

Keep numeric values as fractions for programmatic decisions and use `*_percent` fields for human reports.

## 8. Validation steps after running

1. Confirm the process exits with status `0`.
2. Review warnings before using the score in a report.
3. Confirm `valid_classes` is the expected number of evaluated classes.
4. For a small sample, manually inspect one true positive and one false positive at the selected threshold.
5. If AP is unexpectedly zero or one, re-check file stems, class spelling, `xywh` versus `xyrb`, relative image size, and threshold.

## 9. Failure recovery

- For invalid line errors, open the reported file and line, then fix field count or numeric values.
- For missing `--img-size`, add the exact image width and height used to normalize relative boxes.
- For surprising IoU/AP, run a tiny two-file sample first, then scale back to the full folder.
- For custom data loading, non-uniform image sizes, 11-point interpolation, or plotting/drawing from code, route to `../python-api/SKILL.md`.
