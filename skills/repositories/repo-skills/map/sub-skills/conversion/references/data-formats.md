# Conversion Data Formats

This reference describes the input formats supported by the bundled converter and the evaluator text rows it produces.

## Evaluator text output conventions

The evaluator uses one text file per image. The ground-truth and detection-result files for the same image should share the same basename, for example:

```text
ground-truth/frame_001.txt
detection-results/frame_001.txt
```

### Ground-truth row

```text
<class_name> <left> <top> <right> <bottom> [difficult]
```

- `class_name` is a single whitespace-free token.
- `left top right bottom` are bounding-box coordinates.
- `difficult` is optional and tells the evaluator to ignore that ground-truth object for matching penalties.

### Detection-result row

```text
<class_name> <confidence> <left> <top> <right> <bottom>
```

- `confidence` is a numeric score; darknet percentages are converted to `0..1` scores by the helper.
- The evaluator sorts detections by decreasing confidence during metric computation.

The conversion helper does not compute metrics, check GT/DR intersections, or repair files. It only writes rows in these evaluator formats.

## PASCAL VOC XML ground-truth

Supported command: `voc-xml-gt`.

Expected source file shape:

```xml
<annotation>
  <object>
    <name>person</name>
    <difficult>0</difficult>
    <bndbox>
      <xmin>10</xmin>
      <ymin>20</ymin>
      <xmax>80</xmax>
      <ymax>140</ymax>
    </bndbox>
  </object>
</annotation>
```

Output:

```text
person 10 20 80 140
```

If `difficult` is `1`, `true`, `yes`, or `difficult`, the helper appends `difficult` unless `--drop-difficult` is supplied.

## YOLO ground-truth labels

Supported command: `yolo-gt`.

Expected source row:

```text
<class_id> <x_center_norm> <y_center_norm> <width_norm> <height_norm>
```

Example:

```text
0 0.5 0.5 0.25 0.5
```

Requirements:

- `class_id` is a zero-based integer index into `--class-list`.
- `class_list.txt` is newline-delimited, with one class token per line and no blank lines.
- The helper needs image width and height from one of:
  - `--image-dir` with image stems matching label stems,
  - `--image-size WIDTH HEIGHT`, or
  - `--image-size-file` with rows `<image_id> <width> <height>`.

Coordinate convention:

- The repository's converter denormalizes YOLO boxes and adds `+1` to make VOC-style 1-based integer coordinates.
- The bundled helper preserves that behavior.
- The helper does not clip boxes to image boundaries; invalid or out-of-range training labels should be fixed upstream before evaluation.

## darkflow JSON detection results

Supported command: `darkflow-json-dr`.

Expected source file shape:

```json
[
  {
    "label": "person",
    "confidence": 0.92,
    "topleft": {"x": 10, "y": 20},
    "bottomright": {"x": 80, "y": 140}
  }
]
```

Output:

```text
person 0.92 10 20 80 140
```

The output filename is the JSON stem plus `.txt`.

## darknet result text detection results

Supported command: `darknet-result-dr`.

Expected source sections look like:

```text
Enter Image Path: data/horses.jpg: Predicted in 42.07 seconds.
horse: 88%    (left_x: 3 top_y: 185 width: 150 height: 167)
horse: 99%    (left_x: 5 top_y: 198 width: 307 height: 214)
```

Output file:

```text
detection-results/horses.txt
```

Output rows:

```text
horse 0.88 3 185 153 352
horse 0.99 5 198 312 412
```

The helper extracts one image id per `Enter Image Path:` section, converts confidence percentages to fractions, and computes `right = left + width`, `bottom = top + height`.

## keras-yolo3 annotation files

Supported command: `keras-yolo3` with either `--gt` or `--dr`.

### Ground-truth annotation row

```text
<image_path> <x_min>,<y_min>,<x_max>,<y_max>,<class_id> [...]
```

Example:

```text
nested/img001.jpg 10,20,80,140,0 15,25,35,45,1
```

Output rows:

```text
<class_name> <left> <top> <right> <bottom>
```

### Detection-results annotation row

```text
<image_path> <x_min>,<y_min>,<x_max>,<y_max>,<class_id>,<score> [...]
```

Example:

```text
nested/img001.jpg 10,20,80,140,0,0.92
```

Output rows:

```text
<class_name> <confidence> <left> <top> <right> <bottom>
```

### Output layout

- Default flat layout replaces path separators with `__` so `nested/img001.jpg` becomes `nested__img001.txt`.
- `--recursive` preserves nested directories under `--output-dir`.
- `--keras-root` strips a common image-path prefix when recursive output would otherwise include unwanted dataset directories.

## Unsupported or intentionally excluded behavior

- Class names containing spaces are unsupported because the evaluator parses rows by whitespace.
- Conversion does not validate that every GT output has a matching DR output; use `data-validation` for that.
- Conversion does not run AP/mAP; use `evaluation` for metrics.
- Conversion does not move original annotation files into backup folders. The bundled helper leaves source inputs untouched.
