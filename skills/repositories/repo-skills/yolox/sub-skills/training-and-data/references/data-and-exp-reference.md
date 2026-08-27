# YOLOX Data And Exp Reference

Use this reference to prepare datasets, review custom `Exp` files, reason about cache behavior, and validate default model/data choices before training or evaluation.

## Verified API facts

```python
get_exp(exp_file=None, exp_name=None)
Exp.merge(self, cfg_list)
Exp.get_data_loader(self, batch_size, is_distributed, no_aug=False, cache_img=None)
TrainTransform(max_labels=50, flip_prob=0.5, hsv_prob=1.0)
ValTransform(swap=(2, 0, 1), legacy=False)
COCODataset(data_dir=None, json_file="instances_train2017.json", name="train2017", img_size=(416, 416), preproc=None, cache=False, cache_type="ram")
VOCDetection(data_dir, image_sets=[("2007", "trainval"), ("2012", "trainval")], img_size=(416, 416), preproc=None, dataset_name="VOC0712", cache=False, cache_type="ram")
CacheDataset(input_dimension, num_imgs=None, data_dir=None, cache_dir_name=None, path_filename=None, cache=False, cache_type="ram")
COCOEvaluator(dataloader, img_size, confthre, nmsthre, num_classes, testdev=False, per_class_AP=True, per_class_AR=True)
VOCEvaluator(dataloader, img_size, confthre, nmsthre, num_classes)
```

## Dataset root resolution

YOLOX resolves built-in data roots through `get_yolox_datadir()`:

1. If `YOLOX_DATADIR` is set, use it.
2. Otherwise use a `datasets` directory associated with the installed YOLOX package.
3. Custom `Exp.data_dir` values bypass the fallback for standard COCO datasets.

Portable command:

```bash
export YOLOX_DATADIR=/datasets-root
python -m yolox.tools.train -n yolox-s -d 1 -b 8
```

## COCO layout

When `data_dir` points to a COCO root:

```text
COCO/
  annotations/
    instances_train2017.json
    instances_val2017.json
    instances_test2017.json
  train2017/
  val2017/
  test2017/
```

`json_file` is resolved under `data_dir/annotations/`; `name` is the image subdirectory. `num_classes` must match the evaluator/model class count.

COCO-style custom Exp:

```python
class Exp(MyExp):
    def __init__(self):
        super().__init__()
        self.data_dir = "datasets/my_coco"
        self.train_ann = "instances_train2017.json"
        self.val_ann = "instances_val2017.json"
        self.num_classes = 12
        self.depth = 0.33
        self.width = 0.50
```

## VOC layout

`VOCDetection` expects a `VOCdevkit` root:

```text
VOCdevkit/
  VOC2007/
    Annotations/
    JPEGImages/
    ImageSets/Main/trainval.txt
    ImageSets/Main/test.txt
  VOC2012/
    Annotations/
    JPEGImages/
    ImageSets/Main/trainval.txt
```

Default VOC classes are the 20 PASCAL VOC classes. A VOC Exp should set `num_classes = 20`, return `VOCDetection` for train/eval datasets, and return `VOCEvaluator`.

## Custom dataset contract

Training datasets should return:

```python
img, target, img_info, img_id = dataset[index]
```

For mosaic/mixup and caching, implement `pull_item(index)`, `load_anno(index)`, and `read_img(index)` where appropriate. Targets should be compatible with YOLOX transforms, eventually producing `[class, xc, yc, w, h]` rows.

## Exp field checklist

| Field | Why it matters |
|---|---|
| `num_classes` | Controls detection head channels and evaluator postprocess. |
| `depth`, `width`, `act` | Must match the checkpoint/model family. |
| `input_size`, `test_size` | Training/eval/inference resize targets. |
| `multiscale_range`, `random_size` | Multi-scale training behavior. |
| `data_dir`, `train_ann`, `val_ann`, `test_ann` | COCO/VOC/custom data location. |
| `mosaic_prob`, `mixup_prob`, `hsv_prob`, `flip_prob` | Augmentation intensity. |
| `max_epoch`, `warmup_epochs`, `no_aug_epochs`, `basic_lr_per_img` | Training schedule. |
| `eval_interval`, `save_history_ckpt`, `output_dir` | Eval/checkpoint cadence and output location. |

## Exp.merge contract

Trailing CLI `opts` are key/value pairs. The key must already exist as an `Exp` attribute. Existing tuple/list values are parsed from comma-separated strings after stripping brackets or parentheses.

Examples:

```bash
python -m yolox.tools.train -f path/to/exp.py -d 1 -b 2 max_epoch 2 print_interval 1 eval_interval 1
python -m yolox.tools.eval -f path/to/exp.py -c best_ckpt.pth --tsize 416 test_conf 0.01 nmsthre 0.65
```

## Default model facts

| Name | Depth | Width | Size | Notes |
|---|---:|---:|---:|---|
| `yolox-s` | 0.33 | 0.50 | 640 | Standard small model. |
| `yolox-m` | 0.67 | 0.75 | 640 | Medium model. |
| `yolox-l` | 1.00 | 1.00 | 640 | Large model. |
| `yolox-x` | 1.33 | 1.25 | 640 | Extra-large model. |
| `yolox-tiny` | 0.33 | 0.375 | 416 | Mixup disabled. |
| `yolox-nano` | 0.33 | 0.25 | 416 | Depthwise, mixup disabled. |
| `yolov3` | 1.00 | 1.00 | 640 | YOLOv3-style FPN path. |

## Caching contract

`--cache` pre-creates `exp.dataset = exp.get_dataset(cache=True, cache_type=args.cache)` before launch. Built-in datasets inherit `CacheDataset`. For custom disk cache, pass `data_dir`, `cache_dir_name`, and `path_filename` to `CacheDataset`, and decorate `read_img` with `cache_read_img`. Delete stale disk caches after changing images, resize logic, or annotation associations.
