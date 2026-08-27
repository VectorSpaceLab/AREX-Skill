# Data Formats and Dataset Configs

## Decide the Dataset Route

| Situation | Recommended route | Notes |
| --- | --- | --- |
| COCO-style boxes or masks | `CocoDataset` plus `CocoMetric` | Best default for detection and instance segmentation. Mask AP evaluation is COCO-format oriented. |
| Pascal VOC XML | VOC dataset/config or convert to COCO | Use `VOCMetric` for VOC-style mAP/recall. |
| Cityscapes instance masks | Convert with Cityscapes tools or use Cityscapes dataset config | Requires `cityscapesscripts` for official conversion/evaluation. |
| Panoptic annotations | `CocoPanopticDataset` | `data_prefix` needs both image and segmentation-map prefixes. |
| Custom JSON/YAML/Pickle middle format | `BaseDetDataset` if no custom loader is needed | Use `metainfo` and `data_list`; route custom loader code to `customization-extension`. |
| Images only, no boxes | Manifest-only COCO JSON via `scripts/images_to_coco.py` | Useful for test-dev style inference/submission, not supervised training metrics. |

## COCO Detection JSON Contract

Required top-level keys:

- `images`: each item has `id`, `file_name`, `height`, and `width`.
- `annotations`: each instance has `id`, `image_id`, `category_id`, `bbox` in `[x, y, width, height]`, `area`, and `iscrowd`; masks add valid `segmentation` polygons or RLE.
- `categories`: each item has `id` and `name`; `supercategory` is commonly included but not essential for MMDetection loading.

Validation checklist:

- Every `annotation.image_id` exists in `images.id`.
- Every `annotation.category_id` exists in `categories.id`.
- `bbox` width and height are positive and fit the image after clipping policy is decided.
- Polygon `segmentation` has at least three points and valid XY ordering when mask evaluation is required.
- Category names and order match `metainfo.classes`; MMDetection maps category ids to contiguous labels by category order/name.

## MMEngine Middle Format

Use the middle format when conversion to COCO/VOC is inconvenient and no custom runtime loader is needed:

```python
{
    'metainfo': {'classes': ('person', 'bicycle')},
    'data_list': [
        {
            'img_path': 'images/000001.jpg',
            'height': 720,
            'width': 1280,
            'instances': [
                {'bbox': [10, 20, 40, 60], 'bbox_label': 0, 'ignore_flag': 0}
            ]
        }
    ]
}
```

Key points:

- Annotation files may be JSON, YAML/YML, pickle/PKL, depending on the dataset implementation.
- `bbox_label` is the contiguous zero-based class index, unlike COCO `category_id` which may be non-contiguous.
- `ignore_flag=1` marks crowd/difficult/ignored boxes.
- If parsing a new raw format requires code, define the format here and route implementation to `customization-extension`.

## Dataset Config Fields

Common fields inside `train_dataloader.dataset`, `val_dataloader.dataset`, and `test_dataloader.dataset`:

| Field | Meaning | Common pitfall |
| --- | --- | --- |
| `type` | Dataset class name such as `CocoDataset` | Unregistered custom type belongs in `customization-extension`. |
| `data_root` | Root joined with relative annotation/image paths | A missing slash or doubled path creates silent file-not-found confusion. |
| `ann_file` | Annotation path, often relative to `data_root` | Evaluator `ann_file` must usually point to the same validation/test annotations. |
| `data_prefix` | Prefix dict such as `dict(img='train2017/')` | Panoptic configs also need `seg`. |
| `metainfo` | `classes` tuple and optional `palette` | Class order affects label ids and displayed names. |
| `filter_cfg` | Training filters such as `filter_empty_gt=True`, `min_size=32` | Validation/test datasets should generally use `test_mode=True` and avoid train filtering. |
| `pipeline` | List of transforms | Transform output keys must match the next transform and model packer. |
| `backend_args` | File backend options | Keep local paths portable; do not bake machine-specific roots into public examples. |

Minimal custom class update:

```python
classes = ('a', 'b', 'c')
metainfo = dict(classes=classes, palette=[(220, 20, 60), (0, 0, 142), (119, 11, 32)])
train_dataloader = dict(dataset=dict(metainfo=metainfo))
val_dataloader = dict(dataset=dict(metainfo=metainfo, test_mode=True))
test_dataloader = val_dataloader
model = dict(roi_head=dict(bbox_head=dict(num_classes=len(classes))))
```

For cascades or models with multiple heads, update every `num_classes`, not just the first visible head.

## Transforms and Pipeline Keys

Typical training pipeline:

```python
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(type='Resize', scale=(1333, 800), keep_ratio=True),
    dict(type='RandomFlip', prob=0.5),
    dict(type='PackDetInputs')
]
```

Typical test pipeline:

```python
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='Resize', scale=(1333, 800), keep_ratio=True),
    dict(type='PackDetInputs', meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor'))
]
```

Checks before training:

- `LoadAnnotations(with_bbox=True)` is present for detection training.
- `with_mask=True` is present for instance segmentation training and mask metrics.
- `PackDetInputs.meta_keys` includes metadata needed by downstream evaluation or debugging.
- Custom transforms preserve required keys such as `img`, `gt_bboxes`, `gt_bboxes_labels`, `gt_masks`, and `img_shape`.
- Use dataset browsing before long training when changing transforms.

## Samplers and Wrappers

Common dataloader patterns:

```python
train_dataloader = dict(
    batch_size=2,
    sampler=dict(type='DefaultSampler', shuffle=True),
    batch_sampler=dict(type='AspectRatioBatchSampler'))
val_dataloader = dict(
    batch_size=1,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(test_mode=True))
```

Dataset wrappers:

- `RepeatDataset`: repeats a dataset to increase epoch length.
- `ClassBalancedDataset`: oversamples rare categories by frequency threshold.
- `ConcatDataset`: joins datasets; keep evaluator/class metainfo consistent.

Use `AspectRatioBatchSampler` for detection batches with varied image sizes to reduce padding waste. Keep validation/test `shuffle=False` for reproducible metric ordering.

## Tiny Validation Workflow

1. Inspect one image path by resolving `data_root + data_prefix['img'] + images[0].file_name`.
2. Load the annotation JSON and assert non-empty `images` and expected `categories`.
3. Compare `tuple(category['name'] for category in categories)` with config `metainfo.classes`.
4. Build or browse the dataset with the config before training.
5. If images have no annotations, treat the JSON as inference/test manifest only; do not expect supervised loss or AP metrics.

## Image-Folder Manifest Helper

Use the bundled helper for image folders and class names. From this sub-skill directory:

```bash
python scripts/images_to_coco.py images/ classes.txt annotations/image_info.json --relative-to images
```

The output contains `images`, `categories`, and an empty `annotations` list. This is suitable for test-style inference or later manual annotation merging, but it cannot train a detector or compute bbox/mask AP by itself.
