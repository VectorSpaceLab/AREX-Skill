# COCO data formats and DINO targets

## Standard instance layout

For an instance-detection run, pass an existing read-only `COCODIR` as
`--coco_path`:

```text
COCODIR/
├── train2017/                         # JPEG files referenced by train JSON
├── val2017/                           # JPEG files referenced by val JSON
├── test2017/                          # only for test-dev image-info mode
└── annotations/
    ├── instances_train2017.json
    ├── instances_val2017.json
    └── image_info_test-dev2017.json   # only for test-dev mode
```

The loader in `datasets/coco.py` maps `train` and `train_reg` to the first
training pair, `val` and `eval_debug` to the validation pair, and `test` to
`test2017` plus the image-info JSON. A validation run may check only the split
it will consume; absence of an unrequested split is not a failure.

## Instance annotation schema

The annotation JSON is a COCO object with at least:

```json
{
  "images": [
    {"id": 42, "file_name": "0000000042.jpg", "width": 640, "height": 480}
  ],
  "annotations": [
    {
      "id": 7, "image_id": 42, "category_id": 1,
      "bbox": [x, y, width, height],
      "area": 1200.0, "iscrowd": 0
    }
  ],
  "categories": [
    {"id": 1, "name": "class-a"}
  ]
}
```

For DINO detection, `images`, `annotations`, and `categories` are required;
`images[*].id`, `file_name`, `width`, and `height` must be scalar values with
positive dimensions and unique IDs. Each annotation needs a unique `id`, an
existing `image_id`, an existing `category_id`, a four-number `bbox`, and
nonnegative `area`; `iscrowd` is optional and defaults to zero in the loader.
The validator also rejects negative coordinates, nonpositive width/height,
nonfinite numbers, duplicate image/annotation/category IDs, and annotation
references to missing images or categories. It warns, rather than rejects, a
bbox extending beyond the image because `ConvertCocoPolysToMask` clamps boxes
to image bounds. It permits an image with no annotations.

The repository's loader filters `iscrowd != 0` annotations before converting
boxes and classes. If all annotations in an image are crowd annotations, the
resulting target can have zero objects; this is valid but should be understood
when diagnosing empty batches. `segmentation` is required only when masks are
requested. Polygon segmentations are decoded with `pycocotools.mask`; RLE
segmentations must be accepted by the installed COCO API if masks are enabled.
The loader clips out-of-bounds boxes, whereas the bundled validator reports
negative origins or non-positive boxes as strict input errors; record any
intentional source-data exception explicitly rather than relying on clipping.

## Target produced by `CocoDetection`

Before transforms, `ConvertCocoPolysToMask` emits a target dictionary:

| Field | Shape/type | Meaning |
|---|---|---|
| `boxes` | float tensor `[K, 4]` | initially clipped absolute `x0,y0,x1,y1`; after normalization becomes `cx,cy,w,h` in `[0,1]` relative to the transformed image |
| `labels` | int64 tensor `[K]` | original COCO `category_id` values |
| `image_id` | int tensor `[1]` | COCO image ID |
| `area` | tensor `[K]` | annotation areas retained for nonempty boxes |
| `iscrowd` | tensor `[K]` | crowd flags for retained annotations |
| `orig_size` | int tensor `[2]` | original `[height, width]` |
| `size` | int tensor `[2]` | current `[height, width]`, updated by resize/crop/pad |
| `masks` | uint8 tensor `[K,H,W]` | only with `args.masks`; decoded segmentation masks |
| `keypoints` | float tensor `[K,J,3]` | optional if the first annotation contains keypoints |

`datasets.transforms.Normalize` converts image pixels to a float tensor and
changes boxes from absolute `xyxy` to normalized `cxcywh`. Horizontal flips,
resizes, crops, and mask updates are applied jointly. `orig_size` remains the
pre-augmentation size; evaluation post-processing must use the original size
when converting predictions to absolute coordinates.

Optional model-specific target hooks in `coco.py` can add fields such as
`label_compat`, `label_compat_onehot`, `box_label`, known/unknown box groups,
and perturbed boxes. They are for experimental model names and are not part of
the ordinary DINO detection target contract. Do not invent these fields for a
standard `modelname='dino'` run.

## Category and class-count contract

COCO's 80 categories have IDs 1..90 with gaps. The standard configs use
`num_classes=91`, because this repository's classifier and criterion use a
width indexed by the maximum object ID plus one. The focal target represents
no-object as an all-zero target for unmatched queries; there is no additional
explicit no-object classifier logit in `pred_logits`. For a custom dataset, follow
the repository's `build_dino` comment: if the maximum category ID is `m`, set
`num_classes >= m + 1` (or deliberately remap IDs upstream and document that
choice). Do not set it merely to the number of category names when IDs are
sparse or nonzero-based. Also ensure `dn_labelbook_size >= num_classes + 1`
for the custom-dataset guidance in the README, and verify the exact config
behavior after overrides; the constructor allocates `dn_labelbook_size + 1`
embeddings.

The validator checks category references and ID validity, but it cannot decide
whether a custom ID policy is semantically correct. That remains a config/data
review gate.

## Panoptic layout (optional)

When `dataset_file='coco_panoptic'` and masks are enabled, `datasets/coco_panoptic.py`
expects:

```text
COCO_IMAGES/
├── train2017/ or val2017/
└── ...
COCO_PANOPTIC/
├── panoptic_train2017/ or panoptic_val2017/  # RGB-ID PNGs
└── annotations/
    └── panoptic_train2017.json or panoptic_val2017.json
```

The image root is supplied through `coco_path`; the panoptic root is supplied
through `coco_panoptic_path`. Panoptic JSON `images[*]` and `annotations[*]`
are aligned by sorted image order in this implementation, and each annotation
has `file_name` plus `segments_info`. Each segment record needs at least `id`
and `category_id`; `area` and `iscrowd`, when present, are copied into target
fields. The
corresponding PNG contains the encoded segment IDs. The normal instance JSON
still needs to be validated if the surrounding workflow consumes it.

Panoptic support is optional and has a separate dependency (`panopticapi`).
Do not fail an ordinary bounding-box run because panoptic files are absent.
Use the validator's panoptic option only when this branch is selected.

## Safe validation expectations

[`../scripts/validate_coco_layout.py`](../scripts/validate_coco_layout.py) does
not open or rewrite image pixels, annotations, or symlinks. It parses JSON,
checks references and optional image dimensions, and reports counts and
warnings. Its `--fixture` self-test uses a temporary directory that it owns
and removes. It does not download COCO or call `datasets.data_util` copy/remove
helpers.
