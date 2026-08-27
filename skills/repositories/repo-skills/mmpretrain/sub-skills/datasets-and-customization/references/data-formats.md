# Data formats and layout choices

## Quick choice guide

| Need | Best choice | Why |
| --- | --- | --- |
| Folder-per-class image data | `CustomDataset` subfolder format | No annotation file needed; class names come from folder names. |
| Explicit sample lists | `CustomDataset` text annotation format | Each line can name the sample and label directly. |
| Shared, richer metadata | OpenMMLab 2.0 `json` / `yaml` / `yml` / `pkl` / `pickle` | One schema works across tasks and supports extra fields. |
| ImageNet-style class tree | `ImageNet` | Built-in split handling and official category list. |
| Fold-based validation | `KFoldDataset` | Wraps another dataset and splits indices into folds. |

## `BaseDataset`

`BaseDataset` is the common image-dataset base class. It expects each sample to become a dictionary in `load_data_list()`, and the pipeline loads the actual image later.

Important fields:

- `data_root`: shared root used to resolve relative paths.
- `ann_file`: annotation file path; when relative, keep it consistent with `data_root`.
- `data_prefix`: prefix for sample files; the common image case uses `img_path`.
- `classes`: optional class names from a list, tuple, or file with one class name per line.
- `metainfo`: extra metadata such as class names or task names.

Class-name order rules:

- Explicit `classes` wins.
- If `metainfo.categories` exists, `BaseDataset` derives `classes` by sorting categories by `id`.
- If neither is given, a dataset may fall back to its built-in `METAINFO`.

Typical sample dictionaries look like this:

```python
{
    'img_path': 'train/cat_001.jpg',
    'gt_label': 0,
}
```

For multi-label or multi-task data, the same `data_list` entry can carry richer labels:

```python
{
    'img_path': 'train/sample.jpg',
    'gt_label': [0, 2],
}
```

```python
{
    'img_path': 'train/sample.jpg',
    'gt_label': {
        'gender': 1,
        'wear': [0, 1, 0, 1],
    },
}
```

Use `PackInputs` for the standard single-task classification case, or `PackMultiTaskInputs` when one sample carries several task-specific labels.

## `CustomDataset`

`CustomDataset` supports two layouts.

### Subfolder format

Use this when the data already sits in class folders.

Supervised form:

```text
data_prefix/
├── class_x/
│   ├── xxx.png
│   └── xxy.png
└── class_y/
    ├── 123.png
    └── asd932_.png
```

Unsupervised form:

```text
data_prefix/
├── folder_1/
│   ├── xxx.png
│   └── xxy.png
├── 123.png
└── nsdf3.png
```

Notes:

- Set `with_label=True` for supervised use.
- Set `with_label=False` to load only file paths.
- If you omit `ann_file`, the dataset scans the folder tree.
- Folder names are sorted before class ids are assigned, so label order is lexical unless you pass `classes` explicitly.
- The default file filter accepts common image extensions; override `extensions` if your data uses another suffix.

### Text annotation format

Use this when you already have a file list.

Supervised lines:

```text
folder_1/xxx.png 0
folder_1/xxy.png 1
123.png 4
```

Unsupervised lines:

```text
folder_1/xxx.png
folder_1/xxy.png
123.png
```

Rules:

- Labels start at `0`.
- Every label must stay in `[0, num_classes - 1]`.
- Relative image paths are interpreted with respect to `data_prefix`.
- `classes` should be supplied when the annotation file only stores numeric labels.

## OpenMMLab 2.0 annotation files

This schema is used for more structured datasets and can be serialized as `json`, `yaml`, `yml`, `pkl`, or `pickle`.

Required top-level keys:

- `metainfo`: a dictionary with dataset metadata.
- `data_list`: a list of sample dictionaries.

A minimal single-label example:

```json
{
  "metainfo": {
    "categories": [
      {"id": 0, "category_name": "cat"},
      {"id": 1, "category_name": "dog"}
    ]
  },
  "data_list": [
    {"img_path": "train/cat_001.jpg", "gt_label": 0},
    {"img_path": "train/dog_001.jpg", "gt_label": 1}
  ]
}
```

A multi-task example:

```json
{
  "metainfo": {
    "tasks": ["gender", "wear"]
  },
  "data_list": [
    {"img_path": "a.jpg", "gt_label": {"gender": 0}},
    {"img_path": "b.jpg", "gt_label": {"gender": 1, "wear": [0, 1, 0, 1]}}
  ]
}
```

The same schema works in YAML and pickle formats. The content shape is identical; only the serializer changes.

## `ImageNet`

`ImageNet` supports the standard ImageNet directory layout and the text-annotation layout.

Subfolder layout:

```text
data/imagenet/
├── train/
│   ├── n01440764/
│   └── ...
└── val/
    ├── n01440764/
    └── ...
```

Text-annotation layout:

```text
data/imagenet/
├── meta/
│   ├── train.txt
│   ├── val.txt
│   └── test.txt
├── train/
└── val/
```

Rules:

- `split` must be `train`, `val`, or `test`.
- `test` is label-free and behaves like `with_label=False`.
- If `meta/<split>.txt` exists, it can be used instead of folder scanning.
- The built-in class list matches the ImageNet category order.

## Dataset wrappers

Wrappers keep the inner sample schema unchanged while changing how samples are selected.

- `ConcatDataset`: join several datasets end to end.
- `RepeatDataset`: repeat one dataset several times.
- `ClassBalancedDataset`: oversample rare classes.
- `KFoldDataset`: split one dataset into train/validation folds.

`KFoldDataset` wraps any already-valid dataset, preserves its metadata, and selects a fold by index. Use it when you want cross-validation without changing the underlying annotation format.

## Common image pipeline order

A typical image pipeline follows this order:

```text
LoadImageFromFile -> resize/crop/augment -> PackInputs
```

Common choices in each stage:

- Load: `LoadImageFromFile`
- Train-time crop/resize: `RandomResizedCrop`
- Eval-time resize/crop: `ResizeEdge` and `CenterCrop`
- Extra augmentation: `RandAugment`
- Final formatting: `PackInputs`

Example training order:

```python
[dict(type='LoadImageFromFile'),
 dict(type='RandomResizedCrop', scale=224),
 dict(type='RandAugment', policies='timm_increasing', num_policies=2, magnitude_level=6),
 dict(type='PackInputs')]
```

Example evaluation order:

```python
[dict(type='LoadImageFromFile'),
 dict(type='ResizeEdge', scale=256, edge='short'),
 dict(type='CenterCrop', crop_size=224),
 dict(type='PackInputs')]
```

`Albumentations` is also supported as an optional transform stage when the dependency is installed.
