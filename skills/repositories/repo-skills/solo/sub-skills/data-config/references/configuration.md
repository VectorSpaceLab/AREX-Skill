# Data configuration and pipeline wiring

The legacy config is executable Python loaded through MMCV's `Config.fromfile`.
Treat the effective values as a contract: dataset type, class order, paths,
annotation fields, pipeline, and split-specific mode must agree.

## Minimal effective dataset block

Use this as a pattern, replacing values with the local validated manifest. It
is intentionally self-contained and does not depend on another checkout:

```python
dataset_type = 'CocoDataset'
data_root = 'datasets/example/'
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53],
    std=[58.395, 57.12, 57.375],
    to_rgb=True)

train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(type='Resize', img_scale=(1333, 800), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels', 'gt_masks']),
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='MultiScaleFlipAug', img_scale=(1333, 800), flip=False,
         transforms=[
             dict(type='Resize', keep_ratio=True),
             dict(type='RandomFlip'),
             dict(type='Normalize', **img_norm_cfg),
             dict(type='Pad', size_divisor=32),
             dict(type='ImageToTensor', keys=['img']),
             dict(type='Collect', keys=['img']),
         ])
]

data = dict(
    imgs_per_gpu=1,
    workers_per_gpu=2,
    train=dict(type=dataset_type,
               ann_file=data_root + 'annotations/train.json',
               img_prefix=data_root + 'images/',
               pipeline=train_pipeline),
    val=dict(type=dataset_type,
             ann_file=data_root + 'annotations/val.json',
             img_prefix=data_root + 'images/',
             pipeline=test_pipeline),
    test=dict(type=dataset_type,
              ann_file=data_root + 'annotations/val.json',
              img_prefix=data_root + 'images/',
              pipeline=test_pipeline))
```

For boxes-only detection, set `with_mask=False` or omit it and remove masks
from `Collect.keys`. For semantic segmentation, use a `seg_prefix`, make the
reader return `seg_map`, and set `with_seg=True`; do not substitute
`gt_semantic_seg` for instance masks.

## Effective path rules

The legacy `CustomDataset` constructor joins relative files to `data_root`:

| Field | Meaning | Common failure |
|---|---|---|
| `data_root` | base for relative dataset files | a root is repeated because a path was already absolute |
| `ann_file` | JSON, split list, or custom serialized records | train and val accidentally share the same split |
| `img_prefix` | directory joined to each record filename | prefix points at `images/train` while JSON says `train/...` |
| `seg_prefix` | directory for semantic maps | set only for `with_seg=True` |
| `proposal_file` | optional precomputed proposal file | list lengths do not match concatenated datasets |

Keep filenames in manifests relative to the declared image prefix. If an image
record already contains a subdirectory, do not append that subdirectory again
in `img_prefix`. A list-valued `ann_file` invokes concatenation. List-valued
`img_prefix`, `seg_prefix`, and `proposal_file` are selected by index when they
are lists; verify equal lengths and matching order.

## Dataset wrappers and split semantics

`RepeatDataset` wraps one dataset and repeats its samples a configured number
of times; it does not repair a path, class, or annotation error. `ConcatDataset`
combines datasets and takes the class tuple from the first dataset. Use these
only when class order and target semantics are identical.

Training calls filtering for non-test datasets. The default reader drops
images below a 32-pixel minimum dimension; COCO can also drop images without
annotations when `filter_empty_gt` remains enabled. VOC/WIDER ignore difficult
or too-small boxes according to their reader settings. Therefore a validator
can report valid files while the native dataset still has zero usable training
samples; compare the post-filter count in a tiny native build.

## Pipeline field flow

The pipeline is an ordered `Compose` of dictionaries or callables. The useful
field contract is:

| Stage | Adds/updates | Required input or invariant |
|---|---|---|
| `LoadImageFromFile` | `img`, `img_shape`, `ori_shape`, `filename` | `img_prefix` + record filename resolves |
| `LoadAnnotations` | bbox/label, mask, or semantic fields | dataset `get_ann_info` provides requested fields |
| `Resize` | image, boxes, masks, seg, scale metadata | all geometry fields are registered |
| `RandomFlip` | image and geometry fields | target fields stay aligned |
| `RandomCrop`/`MinIoURandomCrop` | cropped image and targets | a crop may return `None` when no box remains |
| `Expand` | larger image and translated boxes/masks | do not use without boxes |
| `PhotoMetricDistortion` | image only | load image as a compatible numeric type |
| `Albu` | mapped image/boxes/masks | optional dependency and correct bbox format |
| `Corrupt` | image only | `imagecorruptions` installed; severity valid |
| `Normalize` | image and `img_norm_cfg` | channel order and statistics match model |
| `Pad` | image, masks, semantic map, pad metadata | fixed size or divisor, not both |
| `DefaultFormatBundle` | tensors/DataContainers | all collected fields exist |
| `Collect` | `img_meta` plus requested keys | metadata keys exist and keys match model |

A standard test pipeline uses `MultiScaleFlipAug`. Its inner transforms set
scale/flip, resize and normalize the image, pad it, convert it with
`ImageToTensor`, and collect only inference inputs. Do not put stochastic
training crops or `LoadAnnotations` in that test wrapper unless the model/API
explicitly consumes them.

### Geometry checks

- Boxes use four coordinates internally; masks and semantic maps must undergo
  the same resize/flip/crop operations as the image.
- `Resize` clips registered boxes to the resized image. This prevents some
  downstream crashes but can conceal an upstream bad annotation; validate
  first and report clipped/out-of-range data.
- `RandomCrop` filters boxes that become empty and returns `None` if all ground
  truth disappears. With very small objects or aggressive crops, repeated
  skips can starve a worker.
- `Expand` translates boxes and masks but requires `gt_bboxes`. `MinIoURandomCrop`
  expects image, boxes, and labels and keeps box centers in the crop.
- `Albu` maps `img` to `image`, `gt_bboxes` to `bboxes`, and `gt_masks` to
  `masks` by default. A Pascal VOC bbox format and label fields must be declared
  consistently; `skip_img_without_anno=True` can amplify empty-sample issues.

## Inheritance and overrides

The checked-in configuration examples in this release are complete flat Python
files. Source use of `Config.fromfile` is evidence that the file is executed,
not evidence that every modern MMCV configuration feature is available. There
are no checked-in `_base_` examples and no documented generic `--cfg-options`
merge command in this snapshot.

If a prepared environment's parser demonstrably supports `_base_`, use it only
with a small inheritance smoke test and record the resolved `data.*` values.
Otherwise make a complete derived config. Avoid a partially copied dictionary:
a replacing assignment such as `data = dict(...)` can discard workers or other
splits, and a nested override may not merge in the old parser.

The training entry-point parser exposes runtime overrides such as work
 directory, resume checkpoint, validation flag, GPU count, seed,
determinism, launcher, and optional automatic learning-rate scaling. The test
entry point exposes output/result naming, evaluation types, visualization,
temporary result collection, and launcher options. These are runtime controls,
not a general nested data-config merge. When a data path or pipeline must
change, verify the effective Python config rather than assuming a CLI flag did
so.

A safe override procedure is:

1. Copy the representative complete pattern into a task-owned config.
2. Change `dataset_type`, class-dependent model counts, `data_root`, and every
   split's `ann_file`/`img_prefix` together.
3. Change `LoadAnnotations` and `Collect.keys` together when changing boxes,
   instance masks, or semantic maps.
4. Validate every referenced manifest and image root.
5. Parse/build one dataset in the prepared environment and print class order,
   length, one record's image metadata, and target shapes.
6. Preserve the resolved config and validator report with the experiment.

## Optional transforms and dependencies

Minimum data loading needs the legacy runtime stack and, for COCO, a working
COCO mask API. This source era targets PyTorch 1.1+ and `mmcv==0.2.16` and was
documented for CUDA-enabled execution. The safe validator is independent of
those packages.

- `Albu` requires the optional Albumentations package (the source-era optional
  floor is `>=0.3.2`); its transform names and constructor arguments belong to
  the installed version.
- `Corrupt` requires `imagecorruptions` and converts the image to `uint8`; it
  is an image-only robustness transform, not an annotation repair.
- `InstaBoost` requires `instaboostfast` and consumes instance masks; treat it
  as optional and fail early if masks or the package are absent.

A CPU import or schema test cannot certify custom CUDA kernels, CUDA NMS, or
multi-GPU behavior. Separate native GPU/backend verification is required.
