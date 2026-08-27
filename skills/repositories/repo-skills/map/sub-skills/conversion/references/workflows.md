# Conversion Workflows

These workflows convert source annotations or detector outputs into the evaluator's required per-image `.txt` files. Run commands from this sub-skill directory or replace `scripts/convert_annotations.py` with the absolute path to the bundled helper.

The helper is intentionally explicit-path and non-mutating: it reads `--input`, `--gt`, or `--dr` sources and writes only under `--output-dir`. It refuses to overwrite existing output files unless `--overwrite` is supplied.

## 0. Choose target output folders

The evaluator expects two sibling data folders when evaluation is run later:

```text
input/
  ground-truth/
    image_1.txt
  detection-results/
    image_1.txt
```

This sub-skill only creates the converted `.txt` files. Put ground-truth conversions in a ground-truth output directory and detection conversions in a detection-results output directory, then use `data-validation` to check that basenames match before routing to `evaluation`.

## 1. Inspect helper commands

```bash
python scripts/convert_annotations.py --help
python scripts/convert_annotations.py voc-xml-gt --help
python scripts/convert_annotations.py yolo-gt --help
python scripts/convert_annotations.py darkflow-json-dr --help
python scripts/convert_annotations.py darknet-result-dr --help
python scripts/convert_annotations.py keras-yolo3 --help
```

The helper uses only Python's standard library for all conversions. For YOLO ground-truth image-size inference it can read common PNG/GIF/JPEG dimensions without extra packages and may also use Pillow/OpenCV if they are installed. If image-size inference is unavailable, provide dimensions explicitly.

## 2. PASCAL VOC XML ground-truth to evaluator text

Use this when each image has a VOC-style XML file with `object/name` and `object/bndbox/{xmin,ymin,xmax,ymax}` fields.

```bash
python scripts/convert_annotations.py voc-xml-gt \
  --input voc_xml_annotations/ \
  --output-dir converted/input/ground-truth
```

Expected result:

```text
converted/input/ground-truth/<image_id>.txt
```

Each output row is:

```text
<class_name> <left> <top> <right> <bottom> [difficult]
```

By default, VOC objects with a truthy `difficult` field are written with the evaluator's optional `difficult` token. Add `--drop-difficult` if the user deliberately wants to omit that token.

## 3. YOLO normalized ground-truth labels to evaluator text

Use this for YOLO label files where each row is:

```text
<class_id> <x_center_norm> <y_center_norm> <width_norm> <height_norm>
```

You must provide a zero-based class list whose line numbers match YOLO class ids.

### Option A: read dimensions from matching images

```bash
python scripts/convert_annotations.py yolo-gt \
  --input yolo_labels/ \
  --class-list class_list.txt \
  --image-dir images/ \
  --output-dir converted/input/ground-truth
```

Image stems must match label stems, for example `images/frame_001.jpg` for `yolo_labels/frame_001.txt`.

### Option B: one known image size for all labels

```bash
python scripts/convert_annotations.py yolo-gt \
  --input yolo_labels/ \
  --class-list class_list.txt \
  --image-size 640 480 \
  --output-dir converted/input/ground-truth
```

### Option C: per-image size map

```bash
python scripts/convert_annotations.py yolo-gt \
  --input yolo_labels/ \
  --class-list class_list.txt \
  --image-size-file image_sizes.txt \
  --output-dir converted/input/ground-truth
```

`image_sizes.txt` rows can be whitespace- or comma-separated:

```text
frame_001 640 480
frame_002.jpg,1280,720
```

The conversion follows the repository converter's coordinate convention: normalized YOLO center-width-height boxes are denormalized to VOC-style `left top right bottom` coordinates using 1-based integer coordinates.

## 4. darkflow JSON detections to evaluator text

Use this when each source JSON file contains a list of detections with `label`, `confidence`, `topleft`, and `bottomright` fields.

```bash
python scripts/convert_annotations.py darkflow-json-dr \
  --input darkflow_json_results/ \
  --output-dir converted/input/detection-results
```

Expected source object:

```json
{
  "label": "person",
  "confidence": 0.92,
  "topleft": {"x": 10, "y": 20},
  "bottomright": {"x": 80, "y": 140}
}
```

Each output row is:

```text
<class_name> <confidence> <left> <top> <right> <bottom>
```

## 5. darknet result text to evaluator detection-results

Use this for detector output captured from a darknet run similar to:

```text
Enter Image Path: data/horses.jpg: Predicted in ... seconds.
horse: 88%    (left_x: 3 top_y: 185 width: 150 height: 167)
```

Command:

```bash
python scripts/convert_annotations.py darknet-result-dr \
  --input result.txt \
  --output-dir converted/input/detection-results \
  --image-ext .jpg
```

The helper creates one output file per `Enter Image Path:` section. Confidence percentages are divided by 100, and `right/bottom` are computed as `left + width` and `top + height`.

If the result file references another extension, pass it with `--image-ext`, for example `--image-ext .png`.

## 6. keras-yolo3 annotations to evaluator text

Use this when annotations are line-oriented and each row starts with an image path followed by one or more comma-separated boxes.

Ground-truth mode:

```bash
python scripts/convert_annotations.py keras-yolo3 \
  --gt train_annotations.txt \
  --class-list class_list.txt \
  --output-dir converted/input/ground-truth
```

Detection-results mode:

```bash
python scripts/convert_annotations.py keras-yolo3 \
  --dr detection_annotations.txt \
  --class-list class_list.txt \
  --output-dir converted/input/detection-results
```

Default output is flattened so an image path like `nested/folder/img001.jpg` becomes `nested__folder__img001.txt`. To preserve a nested tree under the output directory, add `--recursive`:

```bash
python scripts/convert_annotations.py keras-yolo3 \
  --gt train_annotations.txt \
  --class-list class_list.txt \
  --output-dir converted/input/ground-truth \
  --recursive
```

If image paths contain a common dataset prefix that should not appear in the output tree, strip it explicitly:

```bash
python scripts/convert_annotations.py keras-yolo3 \
  --gt train_annotations.txt \
  --class-list class_list.txt \
  --output-dir converted/input/ground-truth \
  --recursive \
  --keras-root dataset/images
```

## 7. After conversion

1. Spot-check a few output files against [data-formats.md](data-formats.md).
2. Use `data-validation` to detect missing, extra, or mismatched basenames between ground-truth and detection-results folders.
3. Route metric computation to `evaluation` only after conversion and validation are complete.
