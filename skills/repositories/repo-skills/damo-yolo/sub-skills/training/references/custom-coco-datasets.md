# Custom COCO dataset setup for DAMO-YOLO

DAMO-YOLO's default data path logic supports COCO-format datasets. This reference distills the repository custom dataset tutorial, config path catalog behavior, and `COCODataset` label mapping into self-contained operating guidance.

## COCO layout expected by the package

A minimal custom dataset can be arranged under any user-owned data root. The example below uses a `datasets/` directory only as a convention:

```text
training-workdir/
  datasets/
    my_coco/
      annotations/
        train.json
        val.json
      images/
        train/
          000001.jpg
        val/
          000101.jpg
```

Each annotation JSON must contain at least:

- `images`: entries with `id`, `file_name`, `height`, and `width`.
- `annotations`: entries with `image_id`, `category_id`, `bbox` in COCO `[x, y, width, height]` format, `area`, `iscrowd`, and `id`.
- `categories`: entries with `id` and `name`; `supercategory` is optional for training but common in COCO files.

`file_name` values are resolved relative to the catalog `img_dir`. If `file_name` already contains subdirectories, make sure they exist below `img_dir`.

## Register dataset names

The base config's `get_data(name)` uses `DatasetCatalog.DATA_DIR` and `DatasetCatalog.DATASETS` from `damo.config.paths_catalog`. You can either edit those values in a config-accessible path catalog or override `get_data()` in your custom `Config` subclass.

Important naming rule: dataset names must contain the substring `coco`; otherwise the base `Config.get_data()` raises `Only support coco format dataset now!`.

Example catalog entries:

```python
class DatasetCatalog(object):
    DATA_DIR = 'datasets'
    DATASETS = {
        'my_train_coco': {
            'img_dir': 'my_coco/images/train',
            'ann_file': 'my_coco/annotations/train.json',
        },
        'my_val_coco': {
            'img_dir': 'my_coco/images/val',
            'ann_file': 'my_coco/annotations/val.json',
        },
    }
```

If you do not want to edit `DatasetCatalog`, place this logic in a custom config:

```python
def get_data(self, name):
    mapping = {
        'my_train_coco': ('/abs/path/images/train', '/abs/path/annotations/train.json'),
        'my_val_coco': ('/abs/path/images/val', '/abs/path/annotations/val.json'),
    }
    root, ann_file = mapping[name]
    return {'factory': 'COCODataset', 'args': {'root': root, 'ann_file': ann_file}}
```

## Edit the model config

Training uses a single training dataset name in `self.dataset.train_ann`; keep it as a one-element tuple. Validation may list one or more dataset names.

```python
self.dataset.train_ann = ('my_train_coco',)
self.dataset.val_ann = ('my_val_coco',)

class_names = ['widget', 'defect', 'label']
self.dataset.class_names = class_names

ZeroHead = {
    'name': 'ZeroHead',
    'num_classes': len(class_names),
    'in_channels': [128, 256, 512],
    'stacked_convs': 0,
    'reg_max': 16,
    'act': 'silu',
    'nms_conf_thre': 0.05,
    'nms_iou_thre': 0.7,
    'legacy': False,
}
self.model.head = ZeroHead
```

If fine-tuning from a pretrained detector:

```python
self.train.finetune_path = 'checkpoints/pretrained_damoyolo.pth'
self.train.resume_path = None
```

## Class-name mapping details

`COCODataset` builds two mappings:

```python
contiguous_class2id = {class_name: i for i, class_name in enumerate(class_names)}
ori_id2class = {category_id: category_name from annotation categories}
```

For each annotation, DAMO-YOLO computes:

```python
label = contiguous_class2id[ori_id2class[annotation['category_id']]]
```

Consequences:

- COCO `category_id` values may be non-contiguous, but every category id used by annotations must appear in `categories`.
- Every annotation category `name` must match one entry in `self.dataset.class_names` exactly, including case, spaces, and punctuation.
- The order of `self.dataset.class_names` defines DAMO-YOLO's contiguous class indices. Keep this order stable between training and evaluation.
- `self.model.head['num_classes']` must equal `len(self.dataset.class_names)`.
- A validation JSON that omits categories present in training may still run only if no validation annotations reference missing names, but it is safer for train/val `categories` to list the same class names.

Run the bundled validator before long jobs:

```bash
sub-skills/training/scripts/validate_coco_config.py \
  --config /path/to/my_damoyolo_custom.py \
  --workdir /path/used/by/config-relative-assets \
  --data-root /path/to/training-workdir/datasets \
  --split both \
  --check-images 5
```

Omit `--data-root` when the config already resolves dataset roots correctly.

## Common custom-dataset edit checklist

- [ ] Dataset names in `train_ann` and `val_ann` contain `coco` and map to COCO-style roots/annotations.
- [ ] Annotation JSON has `images`, `annotations`, and `categories`.
- [ ] `class_names` contains exactly the intended names and no duplicates.
- [ ] Annotation category names are a subset of `class_names` and preferably equal to it.
- [ ] `model.head['num_classes'] == len(class_names)`.
- [ ] Fine-tune checkpoint path exists if `train.finetune_path` is set.
- [ ] `train.batch_size` is divisible by the planned GPU count; `test.batch_size` is divisible by eval GPU count.
- [ ] Config-relative TinyNAS structure files and dataset paths resolve from the `--workdir` you plan to use.
