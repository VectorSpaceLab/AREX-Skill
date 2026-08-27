# RF-DETR dataset formats

RF-DETR training accepts Roboflow-style COCO, Roboflow/Ultralytics YOLO, and native COCO trees. The high-level API default is `dataset_file="roboflow"`, which auto-detects Roboflow COCO from `train/_annotations.coco.json` or YOLO from `data.yaml`/`data.yml` plus `train/images/`. Use `dataset_file="coco"` for native COCO 2017 and `dataset_file="yolo"` to force YOLO parsing.

Before a long run, use the bundled no-training validator:

```bash
python scripts/validate_dataset_layout.py data/my_dataset --task auto
python scripts/validate_dataset_layout.py data/my_pose_dataset --format yolo --task keypoint --infer-keypoint-schema
```

## Split and detection rules

| Family | Required train layout | Validation | Test behavior |
| --- | --- | --- | --- |
| Roboflow COCO | `train/_annotations.coco.json` and image files under `train/` | `valid/_annotations.coco.json` | Optional `test/_annotations.coco.json` |
| YOLO | `data.yaml` or `data.yml`, `train/images/`, `train/labels/` | `valid/` or `val/`, each with `images/` and `labels/` | Optional `test/images/` and `test/labels/` |
| Native COCO | `train2017/` + `annotations/instances_train2017.json` | `val2017/` + `annotations/instances_val2017.json` | Local scoring uses labelled validation; COCO test-dev is unlabelled |
| Native COCO keypoints | `train2017/` + `annotations/person_keypoints_train2017.json` | `val2017/` + `annotations/person_keypoints_val2017.json` | Same local-scoring caution |

YOLO split paths declared in YAML are resolved first when usable and safely inside the dataset root. Otherwise RF-DETR falls back to conventional `train/valid/test` and also accepts `val/`. A missing YOLO test split can fall back to validation during evaluation; a declared but broken test split is an error.

## COCO detection and segmentation

A split JSON is an object with `images`, `annotations`, and `categories` lists.

| COCO item | Required fields / constraints |
| --- | --- |
| `images[]` | `id`, `file_name`, `width`, `height`; `file_name` resolves relative to the split image directory. |
| `categories[]` | `id`, `name`; custom/Roboflow COCO categories are sorted/remapped to contiguous label slots. |
| `annotations[]` | `id`, `image_id`, `category_id`, COCO pixel `bbox` as `[x, y, width, height]`, `area`, and usually `iscrowd`. |
| Segmentation objects | Add `segmentation` as polygons (`[[x1,y1,...]]`) or valid COCO RLE. |
| Keypoint objects | Add `num_keypoints` and flat `keypoints` `x,y,visibility` triples. |

For segmentation, use a sized segmentation model (`RFDETRSegSmall`, etc.) and `SegmentationTrainConfig`. Detection-only rows cannot provide meaningful mask AP.

Roboflow/custom COCO training remaps sparse category IDs to contiguous label slots. Unannotated hierarchy/grouping categories can be removed so class names, labels, and model output slots agree. Empty images are valid: keep the image row and omit object annotations.

## COCO keypoint preview

Use Roboflow-style `train/` and `valid/` JSON splits, or native COCO person-keypoint annotations. A keypoint annotation has normal box fields plus `num_keypoints` and a flat `keypoints` array of `x, y, visibility` triples. Keypoint-bearing categories should declare `keypoints` names and may declare `skeleton`.

`infer_coco_keypoint_schema(annotation_path, keypoint_oks_sigma=0.1)` returns:

- `class_names`, sorted by category id.
- `num_keypoints_per_class`, including `0` for detection-only classes.
- `keypoint_oks_sigmas`, repeated to the largest keypoint count.
- `keypoint_flip_pairs`, inferred only when left/right names are unambiguous and consistent.

Detection-only COCO files fail keypoint schema inference instead of silently training without keypoints. Mixed keypoint counts are represented per class and padded later by the dataset path.

## YOLO detection and segmentation

```text
dataset/
  data.yaml
  train/images/*.jpg       train/labels/*.txt
  valid/images/*.jpg       valid/labels/*.txt   # or val/
  test/images/*.jpg        test/labels/*.txt    # optional
```

`names` is a list or a contiguous integer-key mapping (`0..N-1`). `nc` is informational but should agree with the names count. YAML `train`, `val`/`valid`, and `test` paths are optional when conventional directories exist.

Detection rows are normalized:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Segmentation rows put normalized polygon coordinates after the class id:

```text
<class_id> <x1> <y1> <x2> <y2> <x3> <y3> ...
```

Images without a matching label file are treated as background images. Empty label files are valid. Class IDs must be integers in `0..N-1`; malformed rows, odd polygon coordinate counts, non-finite numbers, and out-of-range IDs fail clearly.

## YOLO pose / keypoints

YOLO pose uses the same directory layout. The YAML must contain valid `kpt_shape: [K, 2]` or `[K, 3]`. Optional `kpt_names` names joints and `flip_idx` is a length-`K` permutation used to infer RF-DETR's flat `keypoint_flip_pairs`.

Rows are:

```text
<class_id> <x_center> <y_center> <width> <height> <px1> <py1> <v1> ... <pxK> <pyK> <vK>
```

For dimension 2, omit visibility. RF-DETR treats negative coordinates as absent before clamping and synthesizes visibility: nonzero points become visible and `(0,0)` points absent. For dimension 3, visibility must be in `[0,2]`; coordinates are normalized and clamped. A five-field row is detection-only and is rejected in pose mode.

Use `RFDETRKeypointPreview` with `KeypointTrainConfig`. RF-DETR can infer YOLO pose schema during `model.train()` when `data.yaml` declares `kpt_shape`, or explicitly via `infer_yolo_keypoint_schema(data_file, keypoint_oks_sigma=0.1)`. Keypoint training does not support Kornia GPU augmentation; choose CPU/Albumentations. When no reliable flip pairs exist, RF-DETR removes horizontal flips rather than corrupting joint order.

## Native COCO and explicit format

Native COCO uses `train2017`, `val2017`, and `annotations/instances_*`. Native COCO keypoints use `annotations/person_keypoints_*`. Native COCO detection keeps its pretrained sparse-ID convention; custom/Roboflow COCO uses contiguous remap.

The validator is a filesystem/schema preflight. After installing `rfdetr[train]`, still load one transformed batch or run a tiny `fast_dev_run`/short smoke when you need runtime certainty.
