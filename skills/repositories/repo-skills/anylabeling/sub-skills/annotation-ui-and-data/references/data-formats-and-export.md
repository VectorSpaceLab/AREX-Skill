# Data formats and export

This reference describes AnyLabeling's saved JSON structure and the behavior of the built-in export utilities.

## Label JSON structure

A normal saved label file is UTF-8 JSON with these primary top-level keys:

```json
{
  "version": "<application version>",
  "flags": {},
  "shapes": [],
  "imagePath": "relative/or/absolute/image/path",
  "imageData": null,
  "imageHeight": 480,
  "imageWidth": 640
}
```

### Top-level fields

| Field | Required for normal operation | Notes |
| --- | --- | --- |
| `version` | Recommended | Missing version logs a warning, but loading can continue. Saved files always include it. |
| `flags` | Yes for saved files | Image-level boolean flags. Missing or null is treated like `{}` when loading. |
| `shapes` | Yes | List of annotation shape objects. Missing or malformed shapes make the label invalid. |
| `imagePath` | Yes | Path to the image. If relative, it is resolved from the label file directory. |
| `imageData` | Yes | Base64 image bytes or `null`. When null, `imagePath` must resolve to a readable image. |
| `imageHeight` | Needed for export | Saved from the loaded image. Load checks against actual image bytes and logs dimension mismatches. |
| `imageWidth` | Needed for export | Same as `imageHeight`. YOLO export divides by this value, so zero/missing width is fatal for exportable shapes. |

Unknown top-level keys are preserved as `other_data` when a label is loaded and saved again. AnyLabeling also ensures a top-level `text` key exists in `other_data` after load, and the UI uses `image_text` in `other_data` for the image-level text editor.

### Shape fields

Each shape normally has:

```json
{
  "label": "object-name",
  "text": "optional per-object text",
  "points": [[10.0, 20.0], [50.0, 80.0]],
  "group_id": null,
  "shape_type": "rectangle",
  "flags": {}
}
```

| Field | Behavior |
| --- | --- |
| `label` | Required string. Empty labels are not useful and are skipped by normal save flow. |
| `text` | Optional string; defaults to empty string on load. |
| `points` | Required list of numeric `[x, y]` pairs in image pixel coordinates. |
| `group_id` | Optional; `null` or an integer-compatible id. Used only for grouping/visualization, not for exports. |
| `shape_type` | Defaults to `polygon` if missing; must be one of `polygon`, `rectangle`, `point`, `line`, `circle`, `linestrip` in runtime shape objects. |
| `flags` | Optional per-shape flags; defaults to `{}` on load. |

Unknown per-shape keys are preserved under shape `other_data` in memory and written back when saving. This is useful for custom metadata, but downstream exporters ignore it.

### Expected point counts

| Shape type | Expected points | Export support |
| --- | ---: | --- |
| `polygon` | 3 or more | Exported to YOLO, Pascal VOC, COCO, and CreateML. |
| `rectangle` | 2 | Exported to YOLO, Pascal VOC, COCO, and CreateML. UI-created rectangles are normalized to top-left/bottom-right. |
| `point` | 1 | Saved and displayed; skipped by built-in dataset exporters. |
| `line` | 2 | Saved and displayed; skipped by built-in dataset exporters. |
| `circle` | 2 | Saved and displayed; skipped by built-in dataset exporters. |
| `linestrip` | 2 or more | Saved and displayed; skipped by built-in dataset exporters. |

Manual or third-party JSON may contain reversed rectangle points. Pascal VOC, COCO, CreateML, and YOLO detection use min/max or absolute sizes where needed; YOLO segmentation converts the two raw rectangle points into four corners without first sorting them. Normalize rectangle points before segmentation export if deterministic polygon winding matters.

## Core exporter API signatures

The built-in format utility exposes these static methods:

```python
LabelFile.save(
    self,
    filename=None,
    shapes=None,
    image_path=None,
    image_height=None,
    image_width=None,
    image_data=None,
    other_data=None,
    flags=None,
)

FormatExporter.export_to_yolo(
    shapes,
    image_height,
    image_width,
    label_map=None,
    output_path=None,
    export_mode="detection",
)

FormatExporter.export_to_pascal_voc(
    shapes,
    image_path,
    image_height,
    image_width,
    output_path=None,
)

FormatExporter.export_to_coco(
    shapes,
    image_paths,
    image_heights,
    image_widths,
    output_path=None,
)

FormatExporter.export_to_createml(
    shapes,
    image_paths,
    image_heights,
    image_widths,
    output_path=None,
)
```

`export_to_yolo` returns `(result_text, label_map)`. Pascal VOC returns XML text. COCO returns a dictionary. CreateML returns a list of dictionaries. Each method writes to `output_path` only when an output path is supplied.

## YOLO export behavior

YOLO supports `export_mode="detection"` and `export_mode="segmentation"`.

- Class ids are produced from a `label_map`. If none is passed, labels are sorted alphabetically to produce deterministic ids.
- Only `rectangle` and `polygon` shapes are exported; other shape types are silently skipped by the core exporter.
- Detection mode writes one line per exported shape: `class x_center y_center width height`, normalized by `imageWidth`/`imageHeight`.
- Detection rectangles use the two rectangle points and absolute size. Detection polygons are converted to axis-aligned bounding boxes from min/max point coordinates.
- Segmentation mode writes `class x1 y1 x2 y2 ...`, normalized by image dimensions.
- Segmentation polygons preserve point order. Segmentation rectangles are converted to four corners from the raw two points.
- Missing or zero image dimensions cause invalid output or division errors for exportable shapes.

The background `ExportWorker` writes `classes.txt` at the output root, then per-image label text files under `labels/` or split-specific `train/labels`, `val/labels`, and `test/labels`. It also copies corresponding images into `images/` when it can find them.

## Pascal VOC export behavior

Pascal VOC export writes one XML file per JSON label.

- Only rectangles and polygons become `<object>` entries.
- Both rectangles and polygons are converted to axis-aligned bounding boxes.
- Image metadata uses the basename, path, width, height, and a fixed depth of `3`.
- The background worker requires a corresponding image file. It first tries `imagePath` relative to the JSON file, then sibling image files with the same stem and `.jpg`, `.jpeg`, `.png`, or `.bmp`.
- Dataset split mode writes XML and copied images into split directories.

## COCO export behavior

COCO export is dataset-wide rather than one file per image.

- Inputs are lists: shapes per image, image paths, heights, and widths.
- Categories are built from all labels seen in input shapes, sorted alphabetically. Unsupported shape labels can therefore appear as categories even when their shapes are skipped from annotations.
- Only rectangles and polygons become annotations.
- Rectangles become bounding boxes and four-point segmentations.
- Polygons become flattened segmentations and bounding boxes.
- The worker writes `annotations.json` in the output root or each split directory and copies corresponding images.
- Images whose corresponding image file cannot be found are skipped by the worker.

## CreateML export behavior

CreateML export is also dataset-wide.

- Output is a list of image records, each with `image` and `annotations`.
- Only rectangles and polygons become annotations.
- Polygons are reduced to bounding box coordinates; polygon vertex segmentation is not preserved.
- The worker writes `annotations.json` and copies images.

## Export dialog and background worker

The UI export dialog provides:

- Format selection: YOLO, COCO, Pascal VOC, or CreateML.
- YOLO mode selection: detection or segmentation.
- Source folder: current folder or selected folder.
- Recursive JSON search, enabled by default in the dialog.
- Output folder selection.
- Optional random UUID4 names.
- Optional train/val/test split with ratios that must add to 100%.

Important limitations:

- Split shuffling uses runtime randomness; use a separate deterministic script if reproducible splits are required.
- Random names intentionally use UUID4 and are not reproducible.
- The worker loads raw JSON directly and does not run the full `LabelFile` image decode/dimension correction path.
- YOLO can still write labels when an image file is missing, but image copy is skipped. Pascal VOC, COCO, and CreateML skip records when the image cannot be found.
- Unsupported shape types are skipped without a per-shape UI warning.
- Recursive Pascal VOC output can involve nested relative paths; ensure output subdirectories can be created before running a large export.

## Bundled smoke helpers

Use [../scripts/validate_label_json.py](../scripts/validate_label_json.py) before export when labels may come from another tool.

Use [../scripts/export_annotation_smoke.py](../scripts/export_annotation_smoke.py) for small fixtures or debugging. It mirrors the core export math without importing AnyLabeling, reports skipped unsupported shapes, and does not copy images or create train/val/test splits. By default it performs a dry run; pass an output directory when files should be written.
