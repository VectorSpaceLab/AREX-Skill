# Post-processing and serialization

Import these utilities from `PytorchWildlife.utils` (or
`PytorchWildlife.utils.post_process`). They write files and images; create an
output directory explicitly and never assume that a result path is portable.
For result entries, the common shape is a dictionary with `img_id`, a
`supervision.Detections` object under `detections`, and model-produced
`labels`. Detection objects expose `xyxy`, `class_id`, and `confidence` arrays.
Some TimeLapse functions additionally require `normalized_coords`.

## Images and crops

- `save_detection_images(results, output_dir, input_dir=None, overwrite=False)`
  reads each source image as RGB, draws supervision boxes and labels, and
  writes annotated images. With `input_dir`, it preserves the relative path
  below that directory; without it, it uses the basename. `results` may be a
  list or one result dictionary. `overwrite` controls the supervision image
  sink.
- `save_detection_images_dots(..., show_labels=True)` uses dot annotations
  centered on each detection and optionally labels them. It supports a result
  containing an in-memory `img` when `img_id` is absent; when `input_dir` is
  supplied, every entry still needs `img_id` to derive a relative output path.
- `save_crop_images(results, output_dir, input_dir=None, overwrite=False)`
  crops every detection and names files as
  `<category>_<index>_<original-basename>`. With `input_dir`, the crop keeps
  the source image's parent directory. Coordinates are passed to
  `supervision.crop_image`; validate source paths and boxes before batch use.

These functions create directories and can overwrite through the image sink.
They do not delete source images. Avoid using an output directory inside the
input tree because a later recursive input scan could process generated
files.

## Detection JSON and dots

`save_detection_json(det_results, output_path, categories=None,
exclude_category_ids=[], exclude_file_path=None)` writes:

```json
{
  "annotations": [
    {"img_id": "relative/or/original.jpg", "bbox": [[x1,y1,x2,y2]],
     "category": [0], "confidence": [0.93]}
  ],
  "categories": ["animal", "person"]
}
```

Each input result produces one annotation, including an empty detection list.
Boxes are converted to integer `xyxy`; categories and confidences remain
parallel arrays. Categories are filtered before all three arrays are written.
`exclude_file_path` removes one exact `<prefix><native separator>` prefix from
`img_id`; it is not a general path normalizer. For portable output, provide a
known input root and inspect the resulting ids.

`save_detection_json_as_dots` has the same top-level and filtering behavior,
but writes `dot: [[center_x, center_y], ...]` instead of `bbox`. It is the
appropriate representation for dot detectors such as HerdNet. Dot centers
are computed from the integer box coordinates.

## TimeLapse JSON

`save_detection_timelapse_json(..., info={"detector":
"megadetector_v5"})` writes:

```json
{
  "info": {"detector": "..."},
  "detection_categories": {"0": "animal"},
  "images": [
    {"file": "nested/image.jpg", "max_detection_conf": 0.93,
     "detections": [
       {"category": "0", "conf": 0.93,
        "bbox": [0.10, 0.20, 0.30, 0.40], "classifications": []}
     ]}
  ]
}
```

The function requires `normalized_coords` aligned with the filtered
`detections`; each normalized value is `xyxy` in image-relative coordinates
and is emitted as TimeLapse `xywh` (`x1, y1, x2-x1, y2-y1`). Empty detections
produce `max_detection_conf: ""` and an empty list. Category ids become
strings. Keep `info`, category mapping, and normalized-coordinate convention
stable across a dataset.

`save_detection_classification_json(det_results, clf_results, output_path,
det_categories=None, clf_categories=None, exclude_file_path=None)` writes:

```json
{
  "annotations": [
    {"img_id": "image.jpg", "bbox": [[...]],
     "det_category": [0], "det_confidence": [0.93],
     "clf_category": [2], "clf_confidence": [0.81]}
  ],
  "det_categories": ["animal"], "clf_categories": ["species"]
}
```

Classifier results are consumed in order and matched while consecutive
`clf_results` entries have the detector image id. Therefore preserve crop
loader order and keep classifier outputs grouped by `img_id`; the serializer
does not independently join arbitrary rows to individual boxes.

`save_detection_classification_timelapse_json` emits the TimeLapse envelope
with `detection_categories` and `classification_categories`. Each detection
has string `category`, float `conf`, normalized `xywh` `bbox`, and a
`classifications` list of `[class_id, confidence]` pairs. In the current
implementation, classifications are selected by image id and appended to
 each detection in that image; use it only when that image-level association
is intended, or create a validated per-box adapter first.

## Separation

`detection_folder_separation(json_file, img_path, destination_path,
confidence_threshold)` reads the detection JSON's `annotations`. An image is
put in `Animal` if any parallel `category`/`confidence` pair has category `0`
and confidence **strictly greater than** the threshold. Category `0` at the
exact threshold is negative. All other images, including empty annotations,
go to `No_animal`. It copies (does not move) each source image and preserves
nested `img_id` directories below the selected folder. The native function
expects every referenced file to exist and does not validate traversal or
length mismatches; use the bundled
[`separate_detection_results.py`](../scripts/separate_detection_results.py)
when JSON is user-supplied or paths are untrusted. The helper validates
parallel arrays, relative paths, source containment, duplicate image ids,
and copy-vs-overwrite behavior.
