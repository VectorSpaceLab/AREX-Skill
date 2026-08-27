# mAP File Formats

## 1) `evaluate.py` input annotations

`cfg.TEST.ANNOT_PATH` must point to a text file where each line has this structure:

```text
image_path xmin,ymin,xmax,ymax,class_id xmin,ymin,xmax,ymax,class_id ...
```

Rules:

- `image_path` is read with OpenCV.
- `class_id` is a zero-based index into `cfg.YOLO.CLASSES`.
- Each box is comma-separated inside the line.
- The line itself is space-separated.
- `evaluate.py` uses the annotation-line number as the output file stem.

## 2) `evaluate.py` output files

`evaluate.py` writes the following text files for mAP scoring:

### Ground-truth

`./mAP/ground-truth/<n>.txt`

```text
class_name xmin ymin xmax ymax
```

### Predicted

`./mAP/predicted/<n>.txt`

```text
class_name score xmin ymin xmax ymax
```

Notes:

- `<n>` is the annotation row index, not the image basename.
- `score` is formatted with `%.4f`.
- `cfg.TEST.WRITE_IMAGE_PATH` stores the drawn images when `cfg.TEST.WRITE_IMAGE` is enabled.
- `evaluate.py` deletes and recreates the prediction, ground-truth, and write-image directories before writing.

## 3) `mAP/main.py` input contract

Run `mAP/main.py` from inside the `mAP/` directory so its relative paths resolve correctly.
It expects:

- `ground-truth/*.txt`
- `predicted/*.txt`
- optional `images/` for animation
- generated `tmp_files/`
- generated `results/`

Ground-truth lines may be either:

```text
class_name left top right bottom
```

or:

```text
class_name left top right bottom difficult
```

Predicted lines must be:

```text
class_name confidence left top right bottom
```

Additional rules:

- Ground-truth and predicted file stems must match.
- Class names are matched by exact string equality.
- Multi-word class names are unsafe unless normalized before evaluation.
- `mAP/main.py` sorts predictions by confidence before AP computation.

## 4) `mAP/main.py` flags

- `-na` / `--no-animation` disables the OpenCV animation path.
- `-np` / `--no-plot` disables Matplotlib plots.
- `-q` / `--quiet` minimizes console output.
- `-i` / `--ignore class_a class_b` skips listed classes.
- `--set-class-iou class_a 0.75 class_b 0.60` overrides the default IoU threshold per class.

The `--set-class-iou` flag must be written as alternating class / IoU pairs, and each IoU value must satisfy `0.0 < value < 1.0`.

## 5) `mAP/extra/` helper formats

| Script | Input format | Output format | Notes |
| --- | --- | --- | --- |
| `convert_gt_xml.py` | VOC XML files in `../ground-truth/` with `object/name` and `bndbox/xmin,ymin,xmax,ymax` | VOC text `class left top right bottom` | Moves processed XML files into `backup/`. |
| `convert_gt_yolo.py` | YOLO ground-truth text `class_id x_center_norm y_center_norm width_norm height_norm`, plus `class_list.txt` and `../images/` | VOC text `class left top right bottom` | Uses image dimensions to de-normalize the boxes. |
| `convert_pred_darkflow_json.py` | Darkflow JSON objects with `label`, `confidence`, `topleft`, and `bottomright` | Predicted text `class confidence left top right bottom` | Moves processed JSON files into `backup/`. |
| `convert_pred_yolo.py` | Darknet `result.txt` output with `Enter Image Path:` separators and per-class detections | Predicted text `class confidence left top right bottom` | Converts width/height boxes into right/bottom coordinates. |
| `convert_keras-yolo3.py` | Keras-YOLO3 annotation rows; GT boxes are `x_min,y_min,x_max,y_max,class_id`; predictions add `score`; `class_list.txt` maps ids to names | Per-image text files under `from_kerasyolo3/version_<timestamp>/` | Supports `--gt` / `--pred`, `-r`, and `-o`. |
| `remove_delimiter_char.py` | GT or predicted files that already use a single delimiter such as `;` | Space-delimited mAP files | Strips spaces from class names while rewriting. |
| `remove_space.py` | `class_list.txt` plus GT / predicted files with spaces in class names | Class names with delimiter replacements | Useful before `mAP/main.py` when class names contain spaces. |
| `rename_class.py` | `class_list.txt` plus GT / predicted files | Renamed class names in place | Interactive unless `-y` is passed. |
| `intersect-gt-and-pred.py` | Mismatched GT and predicted file sets | Intersection only, with backups in `backup_no_matches_found/` | Use before evaluation when file stems diverge. |

Other helper scripts in `mAP/extra/`:

- `find_class.py` finds files that contain a class name.
- `remove_class.py` deletes instances of a class from the text files.
- `class_list.txt` is one class name per line.
