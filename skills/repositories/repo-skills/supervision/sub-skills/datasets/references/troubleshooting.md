# Dataset troubleshooting

Use this reference when a dataset load, merge, split, or export fails or produces
surprising class ids, masks, or files.

## Import and install issues

- Dataset APIs are in the base install: `pip install supervision`.
- Python must be >=3.10 for this generated skill.
- Metrics are not required for loading or converting datasets. If the task moves
  to mAP, confusion matrices, precision/recall, or benchmark loops, install
  `supervision[metrics]` and route to [metrics](../../metrics/SKILL.md).
- Supervision does not require native OpenCV. Image read/write operations may use
  the documented fallback backend when `cv2` is unavailable. Backend diagnostics
  belong to [media-utils](../../media-utils/SKILL.md).

## Dataset API is fluid

The dataset API is marked fluid in the documentation. Pin `supervision` in
conversion scripts and re-run a small load/export/reload smoke test after version
changes. The generated skill targets `supervision` 0.31.0.dev0.

Symptoms of version drift include changed method signatures, different category
indexing in generated COCO files, changed mask approximations, or deprecation
warnings for in-memory image dictionaries.

## Constructor validation errors

`DetectionDataset(classes, images, annotations)` requires the image keys and
annotation keys to match exactly.

Common failures:

- `ValueError: The keys of the images and annotations dictionaries must match.`
  Use the same path strings in `images` and `annotations`.
- `non-integer class_id`: convert class ids to an integer NumPy dtype before
  constructing the dataset.
- `outside the valid range`: ensure every `class_id` is between `0` and
  `len(classes) - 1`.

Repair pattern:

```python
from dataclasses import replace

fixed_annotations = {}
for image_path, detections in annotations.items():
    if detections.class_id is None:
        fixed_annotations[image_path] = detections
    else:
        fixed_annotations[image_path] = replace(
            detections,
            class_id=detections.class_id.astype(int),
        )

dataset = sv.DetectionDataset(
    classes=classes,
    images=list(fixed_annotations),
    annotations=fixed_annotations,
)
```

Do not patch `detections.data["class_name"]` directly to hide invalid class ids;
the dataset constructor derives that metadata from `classes` and `class_id`.

## Missing or unsafe annotation paths

### YOLO and Pascal VOC missing annotation files

For YOLO and Pascal VOC, an image without a matching label/XML file loads as
`Detections.empty()`. This is valid for background images. If every image becomes
empty unexpectedly, check that image stems and annotation stems match and that
the correct `annotations_directory_path` was passed.

### COCO unsafe `images[].file_name`

`from_coco()` validates each COCO `images[].file_name` beneath
`images_directory_path`. It rejects:

- empty, `.`, or values that resolve to the image directory itself;
- `..` traversal and absolute paths outside the image directory;
- entries resolving to a directory;
- duplicate canonical image paths such as `image.jpg` and `nested/../image.jpg`.

Use legitimate relative paths under the image directory, such as
`train/image_001.jpg`, or rewrite unsafe names before loading.

### LabelMe `imagePath`

`from_labelme()` uses only the basename from each JSON `imagePath` and joins it
to `images_directory_path`. It rejects empty, `.`, `..`, and duplicate basenames.
If two annotation files point to `subdir_a/img.jpg` and `subdir_b/img.jpg`, they
collide because both resolve to `images_directory_path/img.jpg`.

### CreateML `image`

`from_createml()` resolves each entry's `image` beneath `images_directory_path`.
Traversal, absolute outside paths, directory targets, unresolvable paths, and
duplicate canonical paths raise `ValueError`.

## COCO category indexing surprises

Internal `Detections.class_id` is zero-based. COCO files use on-disk
`category_id` values. In current exports:

- `as_coco()` writes `categories[].id` starting at `1`.
- `as_coco()` writes each annotation `category_id = internal_class_id + 1`.
- `from_coco()` remaps arbitrary COCO category ids back to zero-based internal
  ids using sorted categories.
- Legacy zero-indexed COCO files still load, but new exports should be
  one-indexed.

If a model trained on a COCO-style dataset expects original COCO ids rather than
sequential internal ids, build an explicit mapping and apply it at the model
boundary. Keep dataset conversion internal ids tied to `dataset.classes`.

## Class remapping during merge

`DetectionDataset.merge([...])` sorts the union of all class names. That can move
class indices even if a source dataset had a different class order.

Example: merging `classes=["dog", "person"]` with `classes=["cat"]` yields
`["cat", "dog", "person"]`. Source `dog` class id `0` becomes merged class id
`1`. The merged dataset repopulates `detections.data["class_name"]` accordingly.

If labels are wrong after a merge:

1. Print `source.classes` for every input dataset.
2. Print `merged.classes`.
3. Check `detections.class_id` and `detections.data["class_name"]` on a few
   images after merge.
4. Do not concatenate annotation dicts manually; use `DetectionDataset.merge()`
   so class ids are remapped.

Merge also refuses duplicate image paths and refuses to mix lazy path-backed and
in-memory dict-backed datasets.

## Duplicate images and export collisions

Many exporters write images or annotations into flat directories using only the
basename or stem. Supervision checks for collisions and raises before overwrites.

Collision examples:

- `dir_a/img.jpg` and `dir_b/img.jpg` collide when exporting images.
- `dir_a/img.jpg` and `dir_b/img.png` collide for annotation formats keyed by
  stem, such as YOLO `.txt`, Pascal VOC `.xml`, or LabelMe `.json`.
- COCO and CreateML exports store only image basenames in their annotation files,
  so duplicate basenames would collapse records.

Repair by renaming files to unique basenames before creating the dataset, or by
exporting subsets separately and preserving directory structure outside the
flat-format conversion.

## `CLASS_NAME_DATA_FIELD` metadata missing or stale

The constant `CLASS_NAME_DATA_FIELD` has value `"class_name"`. A
`DetectionDataset` constructed with valid `class_id` populates this field in each
annotation. It may be missing when:

- you are working with raw `Detections` not yet wrapped in a dataset;
- `detections.class_id` is `None`;
- code manually mutated `detections.class_id` after dataset construction.

Repair by reconstructing the dataset with the intended `classes`, `images`, and
`annotations` so metadata is regenerated, or derive labels from
`dataset.classes[detections.class_id]` at display time.

## OBB export fails or ignores masks

YOLO OBB mode requires both load/export flags and corner metadata:

- Load OBB datasets with `from_yolo(..., is_obb=True)`.
- Export OBB datasets with `as_yolo(..., is_obb=True)`.
- Each non-empty detection must carry `detections.data["xyxyxyxy"]`, the value of
  `ORIENTED_BOX_COORDINATES`, with shape `(N, 4, 2)` in pixel coordinates.
- `force_masks=True` has no effect in OBB mode; masks are disabled on load and
  ignored on export.
- If `is_obb=False`, existing OBB corner data is ignored and YOLO box format is
  written.

If OBB export raises about missing `xyxyxyxy`, either reload with `is_obb=True`
or synthesize the `(N, 4, 2)` corner array before exporting.

## Mask polygons, RLE, and approximate round-trips

Mask support varies by format:

- YOLO segmentation lines become masks when they contain more than five tokens,
  unless OBB mode is enabled. `force_masks=True` turns YOLO boxes into rectangle
  masks.
- COCO can load polygon and RLE segmentations. If an RLE dict lacks `counts`, the
  loader warns and uses an empty mask for that annotation.
- COCO export writes simple masks as polygons. Masks with holes or multiple
  disconnected regions are inferred as `iscrowd=1` and written as RLE unless
  `detections.data["iscrowd"]` overrides that behavior.
- When COCO masks are not decoded, raw segmentation is stored in
  `detections.data["coco_raw_segmentation"]` so export can preserve it.
- Pascal VOC and YOLO exports approximate masks to polygons. The area filtering
  and simplification parameters can remove tiny components.
- LabelMe exports masks as polygon shapes. Empty or single-pixel masks fall back
  to rectangles to avoid dropping detections, and mask round-trips are
  approximate rather than bit-exact.

When verifying conversion quality, compare mask IoU on a small sample instead of
expecting identical polygon vertex lists.

## VOC, LabelMe, and CreateML shape constraints

### Pascal VOC

- Each object needs `<name>` and `<bndbox>`.
- Missing `<bndbox>` or missing coordinate text raises `ValueError`.
- Polygon coordinates are optional but must contain paired `xN`/`yN` values when
  present.
- VOC coordinates are one-indexed on disk and zero-based internally.
- Background XML files with no objects are valid and load with empty integer
  `class_id`.

### LabelMe

- Only `rectangle` and `polygon` shapes are imported; other shapes are skipped
  with a warning.
- Shapes need `label` and `points`.
- Rectangles need at least two points; polygons need at least three.
- If masks are needed, `imageWidth` and `imageHeight` must be present and
  non-zero.
- Export validates that `class_id` exists and is within `classes`.

### CreateML

- JSON root must be a list.
- Each entry needs `image`.
- Each annotation needs `label` and `coordinates` with `x`, `y`, `width`, and
  `height`.
- CreateML has no explicit category list, so labels absent from all annotations
  do not appear in `dataset.classes`.
- CreateML supports boxes only in this API; keep masks and OBBs in another
  format.

## Progress bars do not appear

Progress bars are opt-in through `show_progress=True` on supported methods.
Defaults suppress tqdm output.

Supported examples:

- `from_yolo(..., show_progress=True)` and `as_yolo(..., show_progress=True)`
- `from_coco(..., show_progress=True)` and `as_coco(..., show_progress=True)`
- `from_pascal_voc(..., show_progress=True)` and
  `as_pascal_voc(..., show_progress=True)`
- `from_createml(..., show_progress=True)` and
  `as_createml(..., show_progress=True)`
- `ClassificationDataset.from_folder_structure(..., show_progress=True)` and
  `as_folder_structure(..., show_progress=True)`

LabelMe load/export methods in this version do not expose `show_progress`.

## Image read errors

If indexing a dataset raises `Could not read image from path`, check:

1. The image path stored in `dataset.image_paths` exists.
2. The file suffix and content are supported by the active image backend.
3. COCO/CreateML resolved paths point to files, not directories.
4. For classification folders, hidden files, nested directories, and unsupported
   suffixes were intentionally ignored by the loader.

OpenCV backend selection, image format details, and low-level file utilities are
covered by [media-utils](../../media-utils/SKILL.md).

## Export raises because `class_id` is missing

YOLO, COCO, Pascal VOC, LabelMe, and CreateML exporters need `Detections.class_id`
to map detections back to labels. If `class_id` is `None`, construct or repair
annotations before export:

```python
import numpy as np
import supervision as sv

fixed = sv.Detections(
    xyxy=detections.xyxy,
    mask=detections.mask,
    confidence=detections.confidence,
    class_id=np.zeros(len(detections), dtype=int),
    tracker_id=detections.tracker_id,
    data=detections.data,
)
```

Only use a default class id when it is semantically correct. Otherwise, revisit
the upstream labeling or model-adapter step in
[detection-and-zones](../../detection-and-zones/SKILL.md).
