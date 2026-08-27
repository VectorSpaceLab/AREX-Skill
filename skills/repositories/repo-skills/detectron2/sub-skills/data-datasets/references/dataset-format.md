# Dataset Registration and Format

Detectron2 data loading starts from lightweight dataset records. A dataset function returns records; a mapper turns each record into model input.

## Catalog APIs

```python
from detectron2.data import DatasetCatalog, MetadataCatalog

DatasetCatalog.register("my_train", load_my_records)
records = DatasetCatalog.get("my_train")
registered_names = DatasetCatalog.list()

MetadataCatalog.get("my_train").set(thing_classes=["cat", "dog"])
metadata = MetadataCatalog.get("my_train")
```

Important behavior:

- `DatasetCatalog.register(name, func)` requires `func` to be callable and rejects duplicate names in the same process.
- `DatasetCatalog.get(name)` calls the registered function each time; it raises a `KeyError` listing available names if `name` is unregistered.
- Dataset functions must be deterministic: return the same records in the same order every time. Do not shuffle, sample, mutate global state, or depend on directory iteration without sorting.
- Registration and metadata live only for the current Python process.
- `MetadataCatalog.get(name)` creates or returns a singleton metadata object for a dataset name.
- Metadata keys are immutable once set to a different value: setting the same key on the same dataset to a different value raises an assertion.

## Standard Dataset Dicts

Use the standard format whenever builtin mappers, evaluators, or visualizers should work. Each top-level record represents one image.

| Task | Required top-level keys | Notes |
| --- | --- | --- |
| Common image record | `file_name`, `height`, `width`, `image_id` | `file_name` points to the image readable by Detectron2. `image_id` is needed by many evaluators. |
| Instance detection/segmentation | `annotations` | Each annotation needs `bbox`, `bbox_mode`, and `category_id`; segmentation/keypoints are optional by model task. |
| Keypoint detection | `annotations` with `keypoints` | Keypoints are `[x1, y1, v1, ...]`; coordinates use real-valued image coordinates. |
| Semantic segmentation | `sem_seg_file_name` | The file should be a label image with integer class ids. |
| Panoptic segmentation | `pan_seg_file_name`, `segments_info` | Each segment entry maps panoptic ids to contiguous `category_id` values. |
| Precomputed proposals | `proposal_boxes`, `proposal_objectness_logits`, `proposal_bbox_mode` | Only for workflows that enable proposal loading. |

Common top-level field details:

- `file_name`: image path. Prefer absolute or application-resolved paths when registering in an application, but do not bake machine-specific paths into reusable code snippets.
- `height`, `width`: integers matching the image. Detectron2 raises a size mismatch when loaded image shape differs.
- `image_id`: string or integer unique within the dataset.
- `annotations`: a list; use an empty list for labeled images with no objects. Training filters empty images by default unless `DATALOADER.FILTER_EMPTY_ANNOTATIONS` is changed.

## Instance Annotation Fields

| Key | Required | Shape / values | Notes |
| --- | --- | --- | --- |
| `bbox` | Yes | 4 numbers for axis-aligned boxes, 5 for rotated boxes | Must match `bbox_mode`. |
| `bbox_mode` | Yes | `BoxMode.XYXY_ABS`, `BoxMode.XYWH_ABS`, or compatible integer value | Relative modes are not supported by `BoxMode.convert`. |
| `category_id` | Yes | Integer in `[0, num_classes - 1]` | Detectron2 standard format uses contiguous zero-based category ids, not raw COCO ids. |
| `segmentation` | For masks | Polygon list or COCO RLE dict | Polygons need even length and at least 3 points; RLE needs `size` and `counts`. |
| `keypoints` | For keypoints | Flat list length divisible by 3 | Pair with `keypoint_names` and `keypoint_flip_map` metadata for horizontal flips. |
| `iscrowd` | Optional | `0` or `1` | Missing means non-crowd in most builtin code. |

Supported box-mode values from Detectron2 include:

- `BoxMode.XYXY_ABS` / integer `0`: `[x0, y0, x1, y1]` absolute coordinates.
- `BoxMode.XYWH_ABS` / integer `1`: `[x0, y0, width, height]` absolute coordinates.
- `BoxMode.XYWHA_ABS` / integer `4`: rotated `[xc, yc, width, height, angle_degrees]`.

Use contiguous `category_id` values in dataset dicts even if the raw annotation source uses arbitrary ids. COCO helpers perform this mapping when a `dataset_name` is provided.

## Metadata Keys

Set metadata for facts shared by the whole dataset, not per-record payloads. Frequently used keys:

| Key | Used by | Value |
| --- | --- | --- |
| `thing_classes` | Instance detection/segmentation, visualization, COCO conversion | List of class names indexed by contiguous `category_id`. |
| `thing_colors` | Visualization | List of RGB tuples in `[0, 255]`. |
| `stuff_classes` | Semantic/panoptic segmentation | List of stuff class names. |
| `stuff_colors` | Semantic/panoptic visualization | List of RGB tuples. |
| `ignore_label` | Semantic/panoptic tasks | Integer label to ignore. |
| `keypoint_names` | Keypoint tasks | List of keypoint names. |
| `keypoint_flip_map` | Keypoint augmentation | List of `(left_name, right_name)` pairs. |
| `keypoint_connection_rules` | Keypoint visualization | Line connections and colors. |
| `thing_dataset_id_to_contiguous_id` | COCO-style loading/evaluation | Raw dataset id to zero-based id mapping. |
| `json_file` | COCO evaluation | COCO annotation JSON path for the registered split. |
| `image_root` | COCO helpers and diagnostics | Image directory for the registered split. |
| `evaluator_type` | Builtin trainer conventions | Often `"coco"`; custom training code can provide evaluators directly instead. |

When combining multiple datasets in one loader, keep task metadata such as `thing_classes`, `keypoint_names`, and `keypoint_flip_map` consistent across names.

## COCO Helpers

Use these helpers for COCO instance, segmentation, or keypoint JSONs:

```python
from detectron2.data.datasets import register_coco_instances

register_coco_instances(
    "my_train",
    {"thing_classes": ["cat", "dog"]},
    "annotations/instances_train.json",
    "images/train",
)
```

Behavior to know:

- `register_coco_instances(name, metadata, json_file, image_root)` registers a lazy loader and sets `json_file`, `image_root`, `evaluator_type="coco"`, plus supplied metadata.
- `load_coco_json(json_file, image_root, dataset_name=name)` returns Detectron2-standard records and sets `thing_classes` plus `thing_dataset_id_to_contiguous_id` metadata.
- `load_coco_json(..., extra_annotation_keys=[...])` preserves custom per-annotation keys for a custom mapper.
- COCO boxes load as `BoxMode.XYWH_ABS`; category ids are remapped to contiguous ids when `dataset_name` is provided.
- Invalid empty COCO bboxes, duplicate annotation ids, unknown category ids, unsupported `ignore`, or invalid segmentation polygons fail during loading or are warned/filtered.

## Dataset Roots

Builtin dataset registrations use `DETECTRON2_DATASETS` as the root. If it is unset, Detectron2 treats `./datasets` under the current process working directory as the default builtin root. Typical builtin layout:

```text
$DETECTRON2_DATASETS/
  coco/
  lvis/
  cityscapes/
  VOC2007/
  VOC2012/
```

For custom datasets, prefer registering explicit JSON/image roots in your application code. If you mirror builtin conventions, document how the runtime sets `DETECTRON2_DATASETS` before importing configs that reference builtin names.

## Custom Dataset Dicts

Custom keys are allowed when the standard format is insufficient. Keep records lightweight: store ids, filenames, and compact annotations, not image arrays or large tensors. Then write a mapper that consumes the custom keys and returns exactly what the model expects.

Example pattern:

```python
def load_records():
    return [{
        "file_name": "images/0001.jpg",
        "height": 480,
        "width": 640,
        "image_id": "0001",
        "annotations": [{"bbox": [10, 20, 100, 120], "bbox_mode": 0, "category_id": 0}],
        "depth_file_name": "depth/0001.png",
    }]

DatasetCatalog.register("rgbd_train", load_records)
MetadataCatalog.get("rgbd_train").set(thing_classes=["object"], depth_unit="meters")
```

Route custom keys to a custom mapper; do not expect `DatasetMapper` to automatically transform unknown task-specific fields.
