# Datasets And Transforms

MMSegmentation dataset configuration joins three contracts: filesystem layout, dataset class metadata, and transform pipeline outputs. Check all three before blaming training or inference code.

## `BaseSegDataset` Contract

Installed API signature:

```python
BaseSegDataset(
    ann_file='',
    img_suffix='.jpg',
    seg_map_suffix='.png',
    metainfo=None,
    data_root=None,
    data_prefix=dict(img_path='', seg_map_path=''),
    filter_cfg=None,
    indices=None,
    serialize_data=True,
    pipeline=[],
    test_mode=False,
    lazy_init=False,
    max_refetch=1000,
    ignore_index=255,
    reduce_zero_label=False,
    backend_args=None,
)
```

Important behavior:

- `data_root` is joined with relative `data_prefix` and `ann_file` values.
- `data_prefix.img_path` points to images; `data_prefix.seg_map_path` points to segmentation masks.
- Without `ann_file`, images are discovered by `img_suffix`; the paired mask path is the relative image path with `img_suffix` replaced by `seg_map_suffix`.
- With `ann_file`, each non-empty line is treated as a sample id or relative stem; the dataset appends `img_suffix` and `seg_map_suffix` under the configured image and mask directories.
- Dataset items include `img_path`, optional `seg_map_path`, `label_map`, `reduce_zero_label`, `seg_fields`, and `sample_idx` before transforms.
- In `test_mode=True`, dataset metainfo must include `classes` for plain `BaseSegDataset`.

## Canonical Layouts

Directory-discovered layout:

```text
data/my_dataset/
  img_dir/train/sample_001.jpg
  img_dir/val/sample_101.jpg
  ann_dir/train/sample_001.png
  ann_dir/val/sample_101.png
```

Config:

```python
dataset=dict(
    type='BaseSegDataset',
    data_root='data/my_dataset',
    data_prefix=dict(img_path='img_dir/train', seg_map_path='ann_dir/train'),
    img_suffix='.jpg',
    seg_map_suffix='.png',
    metainfo=dict(
        classes=('background', 'object'),
        palette=[[0, 0, 0], [255, 255, 255]]),
    pipeline=train_pipeline)
```

Split-file layout:

```text
data/my_dataset/
  images/train/a.jpg
  masks/train/a.png
  splits/train.txt       # contains: a
```

Config:

```python
dataset=dict(
    type='BaseSegDataset',
    data_root='data/my_dataset',
    data_prefix=dict(img_path='images/train', seg_map_path='masks/train'),
    ann_file='splits/train.txt',
    img_suffix='.jpg',
    seg_map_suffix='.png',
    metainfo=dict(classes=('road', 'building'), palette=[[128, 64, 128], [70, 70, 70]]),
    pipeline=train_pipeline)
```

Use the bundled checker before running an expensive job:

```shell
python sub-skills/data-configuration/scripts/check_dataset_layout.py \
  --data-root data/my_dataset \
  --img-path img_dir/train \
  --seg-map-path ann_dir/train \
  --img-suffix .jpg \
  --seg-map-suffix .png \
  --sample-size 5
```

For Cityscapes-style suffixes, include the full suffix:

```shell
python sub-skills/data-configuration/scripts/check_dataset_layout.py \
  --data-root data/cityscapes \
  --img-path leftImg8bit/train \
  --seg-map-path gtFine/train \
  --img-suffix _leftImg8bit.png \
  --seg-map-suffix _gtFine_labelTrainIds.png \
  --recursive
```

## Dataset Classes And Metadata

Built-in dataset classes set `METAINFO` with `classes` and `palette`. Utility functions provide aliases for common datasets:

```python
from mmseg.utils import get_classes, get_palette

classes = get_classes('cityscapes')
palette = get_palette('cityscapes')
```

Supported aliases include names such as `cityscapes`, `ade`, `ade20k`, `voc`, `pascal_voc`, `voc12aug`, `pcontext`, `pascal_context`, `loveda`, `potsdam`, `vaihingen`, `cocostuff`, `isaid`, `stare`, `lip`, `mapillary_v1`, `mapillary_v2`, `bdd100k`, and `hsidrive` variants.

When using a subset of built-in classes:

```python
dataset=dict(
    type='CityscapesDataset',
    data_root='data/cityscapes',
    data_prefix=dict(img_path='leftImg8bit/train', seg_map_path='gtFine/train'),
    metainfo=dict(classes=('car', 'truck', 'bus')),
    pipeline=train_pipeline)
```

`BaseSegDataset.get_label_map()` maps classes not in the subset to `255` and remaps kept classes to contiguous ids. The subset must be a subset of the dataset class `METAINFO`; otherwise dataset construction raises `ValueError`.

For plain `BaseSegDataset`, provide both `classes` and a matching `palette` when you need deterministic colors. If `palette` is omitted, a random but seed-controlled palette is generated. If `palette` length does not match `classes`, construction raises `ValueError`.

## Label Index Rules

- Segmentation masks should be 2D class-id images, not RGB visualizations, unless a converter has mapped colors to ids.
- Valid class ids normally span `[0, num_classes - 1]`.
- `ignore_index` defaults to `255` and is ignored by loss/evaluation components that honor it.
- `reduce_zero_label=True` changes original label `0` to `255`, subtracts one from remaining labels, then restores underflowed `254` to `255`.
- `LoadAnnotations` applies `reduce_zero_label` before class subset `label_map` remapping.
- Do not use `reduce_zero_label=True` for a binary foreground/background dataset where class 0 is a real background class.
- For datasets with unlabeled border/background encoded as 0 and real classes starting at 1, `reduce_zero_label=True` is usually appropriate.

## Transform Pipeline

Installed transform signatures:

```python
LoadAnnotations(reduce_zero_label=None, backend_args=None, imdecode_backend='pillow')
PackSegInputs(meta_keys=('img_path', 'seg_map_path', 'ori_shape', 'img_shape', 'pad_shape', 'scale_factor', 'flip', 'flip_direction', 'reduce_zero_label'))
```

A common training pipeline:

```python
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations'),
    dict(type='RandomResize', scale=(2048, 1024), ratio_range=(0.5, 2.0), keep_ratio=True),
    dict(type='RandomCrop', crop_size=(512, 1024), cat_max_ratio=0.75),
    dict(type='RandomFlip', prob=0.5),
    dict(type='PhotoMetricDistortion'),
    dict(type='PackSegInputs'),
]
```

Transform fields:

- `LoadImageFromFile` adds `img`, `img_shape`, and `ori_shape`.
- `LoadAnnotations` requires `seg_map_path` and adds `gt_seg_map` plus `seg_fields`.
- `RandomResize` and `Resize` update `img`, `gt_seg_map`, and shape metadata.
- `RandomCrop` updates image, mask, and shape metadata; `cat_max_ratio` can avoid crops dominated by one class.
- `RandomFlip` adds `flip` and `flip_direction` metadata.
- `PhotoMetricDistortion` changes the image only.
- `PackSegInputs` converts the image to `inputs`, wraps labels in `SegDataSample.gt_sem_seg`, and stores selected metadata on the sample.

For validation/test with ground truth, keep `LoadAnnotations` after resize when the ground-truth map should not control resizing. For unlabeled test data, remove `LoadAnnotations` from the test pipeline and ensure the evaluator or inference task does not expect ground-truth masks.

## Custom Datasets And Transforms

For a new dataset class:

1. Subclass `BaseSegDataset`.
2. Register it with the MMSegmentation dataset registry.
3. Define `METAINFO = dict(classes=(...), palette=[...])`.
4. Import the module before the config builds the dataset.
5. Add a dataset base config with `dataset_type`, `data_root`, dataloaders, pipelines, and evaluators.

For a new transform:

1. Subclass `mmcv.transforms.BaseTransform`.
2. Implement `transform(self, results: dict) -> dict`.
3. Register it with the transform registry.
4. Import the module before the config builds the pipeline.
5. Use it in the pipeline as `dict(type='YourTransform', ...)`.

Call `register_all_modules(init_default_scope=True)` when building datasets or transforms from config outside the standard tools so MMSegmentation registries and default scope are initialized.
