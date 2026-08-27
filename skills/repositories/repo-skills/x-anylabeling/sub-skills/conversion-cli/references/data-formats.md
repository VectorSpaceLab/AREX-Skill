# Conversion Data Formats

This reference describes the file layouts and schema details that X-AnyLabeling conversion code expects. Use it to prepare small, deterministic conversion inputs or to inspect failed outputs without relying on external examples.

## XLABEL Native JSON

XLABEL is X-AnyLabeling's native per-image JSON format. Conversion tasks generally read or write one `.json` file per image stem.

Minimal file:

```json
{
  "version": "4.0.2",
  "flags": {},
  "checked": false,
  "shapes": [],
  "imagePath": "image.png",
  "imageData": null,
  "imageHeight": 10,
  "imageWidth": 10
}
```

Common shape fields:

| Field | Type | Conversion use |
|---|---|---|
| `label` | string | Class name, text content category, pose box class, or keypoint name. |
| `shape_type` | string | Conversion-relevant values include `rectangle`, `polygon`, `rotation`, `quadrilateral`, and `point`. |
| `points` | list of `[x, y]` | Pixel coordinates in image space. Rectangles are normally four points in clockwise order; some legacy files may contain two diagonal points and are expanded by exporters. |
| `group_id` | integer/string/null | Track id for MOT/MOTS and instance association for pose. Pose export requires integer-like non-null group ids for every rectangle and point. |
| `description` | string/null | Text transcription for PaddleOCR export. |
| `difficult` | bool | Used as ignore/difficult/visibility depending on output format. For pose points, `true` is exported as visibility `1` (occluded), `false` as `2` (visible). |
| `kie_linking` | list | Key-information-extraction links for PaddleOCR KIE export. |
| `flags`, `attributes` | mapping | Preserved by XLABEL but usually ignored by format exporters. |

For manual XLABEL editing semantics, route to `../annotation-ui/SKILL.md`; this sub-skill focuses on conversion behavior.

## Classes File

A classes file is a UTF-8 text file with one class name per line. The first line has id `0`.

```text
person
car
cat
```

Required by:

- YOLO detect/segment/OBB import and export.
- COCO detect/segment import and export.
- MOT import and MOT/MOTS export.
- ODVG export.

For `xlabel2vlmr1`, the CLI parser does not expose `--classes` as a formal requirement; when no class filter is loaded, all rectangle labels found in each image are used as prompts.

## Pose YAML

Pose conversion uses a YAML file rather than `classes.txt`.

```yaml
has_visible: true
classes:
  person:
    - nose
    - left_eye
    - right_eye
```

Rules:

- Root must be a mapping.
- `classes` must be a non-empty mapping from object class names to ordered keypoint names.
- `has_visible` defaults to `true` when omitted.
- For XLABEL pose export, each instance needs one `rectangle` shape labeled with the object class and zero or more `point` shapes labeled with keypoint names. All shapes for the same instance must share the same integer-like `group_id`.
- If a rectangle label is not one of the pose classes, export raises a pose class error. If group ids are missing or invalid, export raises a pose group error.

## YOLO

### Detection

One `.txt` file per image stem. Each line:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Coordinates are normalized to `[0, 1]` relative to image width and height. `yolo2xlabel --mode detect` creates XLABEL `rectangle` shapes.

### Segmentation

Each line:

```text
<class_id> <x1> <y1> <x2> <y2> ...
```

Coordinates are normalized polygon vertices. `yolo2xlabel --mode segment` creates XLABEL `polygon` shapes. Polygons with fewer than three points are ignored on export.

### OBB

Each line:

```text
<class_id> <x1> <y1> <x2> <y2> <x3> <y3> <x4> <y4>
```

Coordinates are normalized quadrilateral corners. `yolo2xlabel --mode obb` creates XLABEL `rotation` shapes. `xlabel2yolo --mode obb` exports only rotation shapes with exactly four points. With the default API `obb_boundary_policy="skip"`, any rotation shape with a point outside the image bounds is skipped and may leave an empty output file.

### Pose

Each line:

```text
<class_id> <x_center> <y_center> <width> <height> <kpt_x> <kpt_y> <visible> ...
```

When `has_visible: false`, keypoints use pairs rather than triples. Import creates one rectangle plus point shapes sharing the line index as `group_id`.

## VOC XML

VOC import reads `.xml` files from a label directory. Required XML metadata:

```xml
<annotation>
  <filename>image.jpg</filename>
  <size><width>100</width><height>50</height></size>
  <object>
    <name>person</name>
    <bndbox><xmin>1</xmin><ymin>2</ymin><xmax>30</xmax><ymax>40</ymax></bndbox>
  </object>
</annotation>
```

- Detection mode imports `bndbox` objects as rectangles.
- Segmentation mode imports `polygon` objects when present, otherwise `bndbox` objects as rectangles.
- Missing `<size>` is fatal.
- Object-level missing or incomplete geometry is skipped with a warning, not a fatal error.
- Export writes one XML file per image. Segmentation mode writes polygon data for polygon shapes and bounding boxes for both rectangle and polygon shapes.

## COCO JSON

COCO import/export uses one JSON file with `images`, `annotations`, and `categories`.

- Detection mode maps COCO `bbox` to XLABEL rectangles.
- Segmentation mode maps polygon `segmentation` lists to XLABEL polygons. RLE segmentation dictionaries are ignored by the importer.
- Pose mode maps COCO `bbox` plus `keypoints` to grouped XLABEL rectangle/point shapes.
- `xlabel2coco --mode detect` writes `coco_detection.json`.
- `xlabel2coco --mode segment` writes `coco_instance_segmentation.json` and may add `_background_` to category handling if absent.
- `xlabel2coco --mode pose` writes `coco_keypoints.json`.

For segmentation export, polygons are grouped as one instance when they share the same label and `group_id`.

## DOTA

DOTA labels are one `.txt` file per image stem. Each line:

```text
x1 y1 x2 y2 x3 y3 x4 y4 class_name difficult
```

Import creates XLABEL `rotation` shapes. Export writes only rotation shapes with four points. If any point is outside `[0, image_width]` or `[0, image_height]`, the shape is skipped and a warning is logged.

## Semantic Mask PNG

Mask import/export uses a mapping JSON and per-image mask files. Supported mapping types:

```json
{"type": "grayscale", "colors": {"road": 1, "cat": 2}}
```

```json
{"type": "rgb", "colors": {"road": [128, 64, 128], "cat": [255, 0, 0]}}
```

Rules:

- `type` must be exactly `grayscale` or `rgb`.
- Grayscale colors are integer pixel values. RGB colors are three-element `[R, G, B]` lists.
- `mask2xlabel` finds mask contours and creates polygon shapes.
- `xlabel2mask` rasterizes polygon shapes. Unknown labels are ignored.
- Empty XLABEL shapes still produce a blank mask of the configured output type.
- The lower-level API also exposes `custom_image_to_empty_mask(image_file, output_file, mapping_table)` to create a blank mask sized from an image when no label JSON exists.

## MOT and MOTS

MOT import reads a text file such as `gt.txt`. Expected fields include:

```text
frame,id,bb_left,bb_top,bb_width,bb_height,valid,class_id,visibility
```

- Import maps `id` to XLABEL `group_id`, class id through `classes.txt`, and boxes to rectangles.
- Frame id is matched against frame filenames by numeric suffix or first numeric text.
- Frames without annotations are skipped with warnings.

MOT export from XLABEL:

- Input is a directory of XLABEL JSON files.
- Rectangle shapes become MOT rows.
- `group_id` is the track id; missing group ids export as `-1`.
- Output includes `seqinfo.ini`, `det.txt`, and `gt.txt`.

MOTS export from XLABEL:

- Polygon shapes become segmentation-tracking rows.
- `group_id` is the track id; missing group ids export as `-1`.
- Output includes `seqinfo.ini` and `custom_gt.txt`.

## PaddleOCR (PPOCR)

PaddleOCR import reads a text file where each line contains an image path and a JSON annotation list separated by a tab.

Recognition/KIE annotation objects commonly include:

```json
{
  "transcription": "hello",
  "points": [[1, 1], [8, 1], [8, 4], [1, 4]],
  "label": "text",
  "id": 0,
  "linking": [],
  "difficult": false
}
```

- Import mode `rec` or `kie` creates XLABEL text-region shapes.
- Four-point regions become `rectangle` when they look rectangular, otherwise `quadrilateral`; longer regions become `polygon`.
- Export mode `rec` uses `description` as transcription, writes `Label.txt`, `rec_gt.txt`, and cropped word images under `crop_img/`.
- Export mode `kie` writes `ppocr_kie.json` and a `class_list.txt` containing labels seen in the converted files.

## ODVG

ODVG import expects JSONL records with image metadata and detection instances. The converter expects the detection instances under `detection.instances`, where each instance has a `bbox`, `label`, and `category`.

```json
{
  "filename": "image.jpg",
  "height": 480,
  "width": 640,
  "detection": {
    "instances": [
      {"bbox": [10, 20, 100, 200], "label": 0, "category": "person"}
    ]
  }
}
```

ODVG export writes:

- `label_map.json`: numeric ids to class names from `classes.txt`.
- `od.json`: JSONL detection records with rectangle shapes whose labels are present in `classes.txt`.

## VLM-R1-OVD

`xlabel2vlmr1` writes JSONL conversation records for open-vocabulary detection. Rectangle shapes become answer boxes.

The importer accepts model answers that can be parsed as JSON-like lists, either directly or inside `<answer>...</answer>`:

```json
[
  {"bbox_2d": [1, 2, 8, 9], "label": "cat"}
]
```

Rules:

- Input boxes become XLABEL rectangles.
- If no boxes can be parsed, the generated XLABEL file contains no shapes.
- On export, images with no rectangle labels are skipped when no class filter is loaded. If a class filter is loaded through API use and no boxes match, the answer is `None`.

## Tiny Fixture Layout

The bundled `scripts/create_conversion_fixture.py` creates this deterministic layout:

```text
<work-dir>/
  classes.txt
  images/tiny.png
  labels/tiny.txt
  xlabel/
```

`labels/tiny.txt` contains one YOLO detection line for class `box` centered in a 10x10 image. The smoke script converts it and asserts that `xlabel/tiny.json` contains one rectangle shape.
