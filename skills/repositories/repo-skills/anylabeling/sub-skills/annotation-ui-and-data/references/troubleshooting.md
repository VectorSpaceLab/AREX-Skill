# Troubleshooting annotation UI and data issues

## Invalid label JSON

Symptoms:

- Opening a label file shows an error asking whether it is a valid label file.
- Export silently skips a file or raises an export error.
- A downstream conversion produces empty labels.

Check:

```bash
python path/to/validate_label_json.py labels/example.json
```

Typical causes:

- Missing `imageData`, `imagePath`, or `shapes` key.
- `imageData` is `null` but `imagePath` does not resolve to a readable image from the label file directory.
- `shapes` is not a list, or a shape lacks `label` or valid numeric point pairs.
- `shape_type` is misspelled or not one of `polygon`, `rectangle`, `point`, `line`, `circle`, `linestrip`.
- `flags` is not an object at top level or inside a shape.
- `group_id` is not integer-compatible while group display is enabled.

Unknown top-level fields are not automatically invalid. AnyLabeling preserves them as `other_data` and writes them back on save. Unknown per-shape fields are similarly preserved as shape `other_data`. Treat them as warnings unless your downstream pipeline requires an exact schema.

## Missing `imagePath` or `imageData`

AnyLabeling can load image bytes from either:

1. `imageData` as base64 bytes, or
2. `imagePath` resolved relative to the label file directory when `imageData` is `null`.

If both are missing or unusable, label loading fails. If you saved with `store_data: false` or the `--nodata` flag, keep the image files next to the labels or update `imagePath` so it resolves correctly.

For portable fixtures, either embed `imageData` or keep a small image beside the label file and use a simple relative `imagePath` such as `image.jpg`.

## Image dimension mismatch

AnyLabeling checks `imageHeight` and `imageWidth` against actual decoded image bytes during label load. If they differ, it logs an error and uses the actual decoded dimensions in memory.

Exporters use the dimensions present in JSON or passed to the exporter. A stale dimension can therefore cause wrong normalized YOLO values even if the UI displayed the image correctly after correction. Regenerate or fix dimensions before batch export.

Use the validator script to detect mismatches when possible:

```bash
python path/to/validate_label_json.py labels/*.json
```

## Reversed rectangle points

UI-created rectangles are normalized at finalization to top-left then bottom-right. Third-party JSON may contain points in reverse or diagonal order.

Effects:

- Pascal VOC, COCO, CreateML, and YOLO detection compute min/max or absolute sizes and usually remain usable.
- YOLO segmentation converts rectangle points to four corners using the raw point order. Reversed points can produce an unexpected polygon winding or starting corner.

Fix by normalizing each rectangle to:

```json
"points": [[min_x, min_y], [max_x, max_y]]
```

The validator reports reversed rectangles as warnings.

## Unsupported shape types skipped during export

The built-in exporters only export `rectangle` and `polygon` shapes. These are skipped:

- `point`
- `line`
- `circle`
- `linestrip`

This is expected for YOLO, Pascal VOC, COCO, and CreateML. If a fixture contains only unsupported shapes, output labels can be empty while the label JSON is still valid for manual annotation.

Use the smoke exporter to show which shapes will be skipped:

```bash
python path/to/export_annotation_smoke.py labels/example.json --format yolo-segmentation
python path/to/export_annotation_smoke.py labels/example.json --format coco
```

## Exact label validation rejects expected labels

Exact validation checks typed labels against the configured label list. To use it safely:

- Provide `--labels` or `labels:` in config.
- Ensure the configured label list has no duplicates; duplicate config labels are rejected.
- Use the exact spelling expected by the config. Validation is exact, not fuzzy.
- Existing JSON files can contain labels outside the configured list if they were created before validation or by another tool. Validate them separately before export.

Example validation command:

```bash
python path/to/validate_label_json.py labels/*.json --exact-labels --labels person,car,bicycle
```

## Autosave and output confusion

Common cases:

- `--output some_dir` means annotations are saved and loaded from `some_dir`, while images remain where they are.
- `--output one.json` means save to a single JSON file. Do not combine this with auto-save; the application rejects that combination because auto-save expects one label file per image.
- `auto_save: true` is the default. Disable it in config or via the UI if you want explicit Save/Save As behavior.
- `store_data: false` is the default. Saved JSON depends on `imagePath`; moving labels without images can break later loading/export.

## Export produces no records

Check these in order:

1. The input directory actually contains `.json` annotation files.
2. Each JSON has non-empty `shapes`.
3. Shapes are `rectangle` or `polygon`; other types are skipped.
4. `imageHeight` and `imageWidth` are positive for YOLO.
5. For Pascal VOC, COCO, and CreateML worker exports, the corresponding image file exists.
6. If using split export with a tiny dataset, integer truncation can put zero files in one split. Adjust ratios or export without splitting.

## Headless Qt platform plugin errors

When launching AnyLabeling or importing UI modules on a server, Qt may fail with a platform plugin error such as inability to load `xcb`.

For non-interactive smoke imports, set an offscreen platform before starting Python:

```bash
QT_QPA_PLATFORM=offscreen python -c "from anylabeling.views.labeling import label_widget; print('ok')"
```

For actual desktop annotation, use a real display server or remote desktop session. Offscreen mode is for diagnostics, not manual labeling.

## Read-only `imgviz` colormap startup regression

Newer `imgviz`/NumPy combinations can return a read-only colormap array. Startup used to fail with:

```text
ValueError: assignment destination is read-only
```

Current AnyLabeling code copies the colormap before editing it in the label widget. If this error appears:

1. Confirm the installed AnyLabeling code includes the `.copy()` when constructing the label widget colormap.
2. Reinstall or upgrade to a version that includes the fix.
3. If working from a modified tree, avoid changing that line back to direct mutation of `imgviz.label_colormap()`.

## When to use the bundled helpers

- Use [../scripts/validate_label_json.py](../scripts/validate_label_json.py) for schema, label vocabulary, path, dimension, reversed-rectangle, unknown-field, and unsupported-shape diagnostics.
- Use [../scripts/export_annotation_smoke.py](../scripts/export_annotation_smoke.py) to preview YOLO, COCO, Pascal VOC, or CreateML conversion on small examples before opening the GUI export dialog.

The helpers do not import AnyLabeling and do not require a Qt display.
