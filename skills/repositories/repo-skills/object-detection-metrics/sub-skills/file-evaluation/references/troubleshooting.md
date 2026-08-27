# File-evaluation troubleshooting

## `error: ground-truth folder does not exist` or `detection folder does not exist`

Pass actual folders with `--gt-folder` and `--det-folder`. The helper intentionally has no checkout-relative defaults, so it will not silently use sample data from another directory.

## `expected 5 fields` or `expected 6 fields`

Ground-truth lines require exactly five fields:

```text
class left top width height
```

or, with `--gt-format xyrb`:

```text
class left top right bottom
```

Detection lines require exactly six fields:

```text
class confidence left top width height
```

or, with `--det-format xyrb`:

```text
class confidence left top right bottom
```

Class labels cannot contain spaces in this text format. Replace labels such as `traffic light` with a single token such as `traffic_light` consistently in both folders.

## Numeric parse errors

Every coordinate and detection confidence must parse as a finite number. Remove comments from data lines, fix commas used as decimal separators, and avoid tokens such as `nan` or `inf`.

## `no valid classes`

AP/mAP requires at least one ground-truth positive. Common causes:

- The ground-truth folder is empty or contains no nonblank valid lines.
- Only detection files were supplied.
- Class names are misspelled and all boxes are detection-only.
- The wrong folder was passed as `--gt-folder`.

Detection-only classes are excluded from mAP and reported as warnings because recall is undefined without positives.

## File stem mismatch warnings

File stems are image ids. These two files match:

```text
groundtruths/00001.txt
detections/00001.txt
```

These do not match:

```text
groundtruths/00001.txt
detections/image_00001.txt
```

Unmatched ground-truth files produce missed objects if there are no detections. Unmatched detection files can count as false positives when their class has ground-truth positives in other images.

## AP is unexpectedly low or zero

Check in this order:

1. Class labels are identical between GT and detection files.
2. File stems match the intended image ids.
3. `--gt-format` and `--det-format` match the actual coordinate convention.
4. If using relative coordinates, `--img-size` matches the image size used during normalization.
5. The IoU threshold is appropriate; `0.5` is the default, while examples often use `0.3` to demonstrate the metric.
6. Detections are not all below the threshold due to shifted boxes, wrong width/height interpretation, or mixed coordinate spaces.

## Wrong `xywh` versus `xyrb` selection

The helper cannot infer whether the third and fourth coordinate values are width/height or right/bottom. A valid but wrong selection can produce plausible-looking, incorrect AP.

- Use `xywh` for `left top width height`.
- Use `xyrb` for `left top right bottom`.
- Select GT and detection formats independently.
- Test one known box pair manually when converting from another annotation format.

## Relative coordinates fail or produce strange boxes

Relative coordinates require `--img-size WIDTH,HEIGHT`.

The relative schema is YOLO-like center/size:

```text
center_x center_y width height
```

It is not `left top width height`. The helper rejects `rel` plus `xyrb` because the legacy conversion only supports relative center/size values.

If normalized boxes were created from different image sizes, evaluate per-size subsets or convert all boxes to absolute coordinates before using this folder-level helper. For per-image sizes or custom loaders, route to `../python-api/SKILL.md`.

## Duplicate detections are false positives

Only one detection can match each ground-truth object. If five detections overlap the same object at or above the IoU threshold, the highest-confidence one is a true positive and the rest are false positives.

## IoU appears off by one pixel

This legacy VOC implementation uses inclusive pixel areas:

```text
area = (right - left + 1) * (bottom - top + 1)
```

This is expected for reproducing the repository's PASCAL VOC behavior. Do not mix this score with an exclusive-area implementation without documenting the difference.

## Original `pascalvoc.py` prompts or deletes output

The original high-level script asks before clearing a non-empty save path, then deletes and recreates that folder for plots/results. For unattended jobs, use the bundled helper instead. It never prompts, never plots, and never deletes directories; it writes only the explicit output files requested with `--output-text` or `--output-json`.

## Matplotlib, GUI, OpenCV, or display errors

Those errors come from plotting or drawing paths in the original toolkit. The bundled helper avoids them by using only the Python standard library and never creating plots. If the user specifically needs plotting, drawing boxes, or direct source API behavior, route to `../python-api/SKILL.md`.

## COCO metrics or successor UI requested

COCO metrics, the newer UI workflow, additional file formats from the successor project, and video/STT-AP metrics are outside this legacy Object-Detection-Metrics sub-skill. Explain the scope mismatch instead of trying to approximate COCO with VOC AP.

## Safe rerun guidance

- Prefer writing outputs to a fresh report path.
- If reusing an output file path, the helper overwrites that explicit file only; it never deletes a directory.
- Keep raw GT/detection folders unchanged and write converted data to a separate folder when debugging format conversions.
