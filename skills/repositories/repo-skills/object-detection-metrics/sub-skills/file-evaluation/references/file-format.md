# File format and matching rules

This sub-skill evaluates object detections from two text-folder inputs: one folder for ground truth and one folder for detections. Images themselves are not required by the evaluator unless relative coordinates need a shared image size.

## Folder layout

Use one `.txt` file per image id:

```text
groundtruths/
  image_001.txt
  image_002.txt
detections/
  image_001.txt
  image_002.txt
```

The file stem is the image id. `groundtruths/image_001.txt` and `detections/image_001.txt` refer to the same image. Missing detection files mean those ground-truth objects may become false negatives. Extra detection files are counted as false positives when their class has ground-truth positives elsewhere.

Blank lines are ignored. Each nonblank line must use whitespace-separated fields. Class labels cannot contain spaces.

## Ground-truth schemas

Absolute `xywh` format:

```text
<class> <left> <top> <width> <height>
```

Example:

```text
person 25 16 38 56
person 129 123 41 62
```

Absolute `xyrb` / `XYX2Y2` format:

```text
<class> <left> <top> <right> <bottom>
```

Example:

```text
person 25 16 63 72
person 129 123 170 185
```

## Detection schemas

Absolute `xywh` format:

```text
<class> <confidence> <left> <top> <width> <height>
```

Example:

```text
person 0.88 5 67 31 48
person 0.70 119 111 40 67
```

Absolute `xyrb` / `XYX2Y2` format:

```text
<class> <confidence> <left> <top> <right> <bottom>
```

Example:

```text
person 0.88 5 67 36 115
person 0.70 119 111 159 178
```

Confidence is used only to sort detections by descending score before AP calculation. It is usually between `0` and `1`, but the legacy evaluator treats it as a numeric ranking value.

## Coordinate format flags

Map schemas to helper flags:

| Data shape | Ground-truth flag | Detection flag |
|---|---|---|
| `left top width height` | `--gt-format xywh` | `--det-format xywh` |
| `left top right bottom` | `--gt-format xyrb` | `--det-format xyrb` |
| GT and detections differ | choose independently | choose independently |

For absolute `xywh`, the source-style conversion is:

```text
x2 = left + width
y2 = top + height
```

Then IoU area uses inclusive VOC pixel area, so width/height in area calculations include `+1` after conversion.

## Absolute versus relative coordinates

Use `--gt-coords abs` and `--det-coords abs` for pixel coordinates.

Use `rel` only for YOLO-like relative `center_x center_y width height` values. A shared image size is required:

```bash
python scripts/voc_metrics_eval.py \
  --gt-folder groundtruths \
  --det-folder detections_rel \
  --det-coords rel \
  --img-size 200,200
```

When coordinates are relative, the four values are interpreted as:

```text
center_x / image_width
center_y / image_height
box_width / image_width
box_height / image_height
```

The conversion mirrors the legacy helper:

```text
x1 = round(((2 * center_x - box_width) * image_width / 2))
y1 = round(((2 * center_y - box_height) * image_height / 2))
x2 = x1 + round(box_width * image_width)
y2 = y1 + round(box_height * image_height)
x1/y1 are clipped to at least 0
x2/y2 are clipped to at most image_width - 1 / image_height - 1
```

Relative coordinates must use `xywh` flags because they are center/size values, not `left top right bottom`. The bundled helper rejects `rel` plus `xyrb` to prevent misleading AP.

## Matching and metric semantics

For each class independently:

1. Ground-truth boxes are grouped by image id.
2. Detections are sorted by descending confidence.
3. Each detection is compared with ground truths of the same class and image id.
4. If the best IoU is greater than or equal to the threshold and that ground truth is not already matched, the detection is a true positive.
5. If IoU is below threshold, the image id has no ground truth for that class, or the best ground truth is already matched by a higher-confidence detection, the detection is a false positive.
6. Precision and recall are accumulated over the confidence-sorted detections.
7. AP uses every-point interpolation; mAP averages AP over classes with at least one ground-truth positive.

## Validation checklist

Before evaluation, check:

- Both folders exist and contain `.txt` files.
- Line field counts match the selected schema: 5 fields for ground truth, 6 for detections.
- Class names are single tokens with no spaces.
- File stems match the intended image ids in both folders.
- `xywh` versus `xyrb` has been selected independently for GT and detections.
- `--img-size WIDTH,HEIGHT` is present whenever `--gt-coords rel` or `--det-coords rel` is used.
- `rel` coordinates are center/size values, not top-left/size values.
