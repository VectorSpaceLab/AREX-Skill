# Data Preparation and Training Workflows

Commands assume a target checkout root as the current working directory.

## COCO preparation

The README's COCO evaluation flow has three phases: download/extract COCO,
convert COCO JSON to an intermediate pickle, then write this repository's
annotation text format.

```bash
# Optional, large network/data action: download COCO validation data.
cd scripts
bash get_coco_dataset_2017.sh

# Convert COCO annotations JSON to pickle.
python coco_convert.py \
  --input ./coco/annotations/instances_val2017.json \
  --output val2017.pkl

# Convert pickle plus images into data/dataset/val2017.txt.
python coco_annotation.py \
  --coco_data ./val2017.pkl \
  --classes ../data/classes/coco.names \
  --coco_path ./coco \
  --image_path images/val2017 \
  --anno_path_val ../data/dataset/val2017.txt
```

Notes:

- `get_coco_dataset_2017.sh` downloads and unzips COCO files; run it only after
  user approval for network and disk usage.
- `coco_convert.py` writes a pickle containing parsed image/object metadata.
- `coco_annotation.py` maps a few COCO category names to VOC-style spellings
  before class lookup: `couch -> sofa`, `airplane -> aeroplane`, `tv ->
  tvmonitor`, `motorcycle -> motorbike`.
- Validate the produced annotation file with the bundled validator before
  training or evaluation.

## VOC preparation

`voc_annotation.py` converts VOC XML files into the same converted annotation
line format:

```bash
python scripts/voc_annotation.py \
  --data_path /path/to/VOC \
  --train_annotation ./data/dataset/voc_train.txt \
  --test_annotation ./data/dataset/voc_test.txt
```

Expected VOC layout under `--data_path` follows the source script assumptions:

```text
train/VOCdevkit/VOC2007/
train/VOCdevkit/VOC2012/
test/VOCdevkit/VOC2007/
```

The source class list is fixed to the 20 VOC names. For other datasets, create a
custom class file and conversion script rather than forcing names into the VOC
list.

## Training configuration

Training is controlled mostly by `core.config.cfg` plus flags in `train.py`:

```bash
python train.py --model yolov4 --weights ./data/yolov4.weights
```

Verified `train.py` flags:

| Flag | Default | Meaning |
|---|---|---|
| `--model` | `yolov4` | `yolov4` or `yolov3`. |
| `--weights` | `./scripts/yolov4.weights` | Pretrained Darknet or TensorFlow weight path. |
| `--tiny` | false | Tiny model training path. |

Source behavior:

- `Dataset(FLAGS, is_training=True)` reads `cfg.TRAIN.ANNOT_PATH`.
- `Dataset(FLAGS, is_training=False)` reads `cfg.TEST.ANNOT_PATH`.
- First-stage epochs freeze backbone/head layers from `utils.load_freeze_layer`.
- Second-stage epochs unfreeze those layers.
- The source spelling is `cfg.TRAIN.FISRT_STAGE_EPOCHS`; editing
  `FIRST_STAGE_EPOCHS` will have no effect.
- Checkpoints are saved to `./checkpoints/yolov4` at the end of every epoch,
  regardless of model family naming.

## Scratch versus transfer learning

The README says to set `FISRT_STAGE_EPOCHS=0` for scratch training and run
`python train.py`; however `train.py` has a default `--weights` path and checks
`if FLAGS.weights == None`. Passing `--weights None` is a string, not Python
`None`, so target-checkout users may need to patch the flag default or code path
for true scratch training.

For transfer learning, supply a valid Darknet `.weights` file:

```bash
python train.py --model yolov4 --weights ./data/yolov4.weights
```

## Training validation checklist

- Annotation lines pass the bundled validator.
- Image files in the annotations are accessible from the training machine.
- `cfg.YOLO.CLASSES` matches class IDs and desired output classes.
- Anchors match model family and any custom anchor tuning.
- `cfg.TRAIN.INPUT_SIZE` is divisible by the relevant strides.
- Batch size fits memory; lower it before blaming model code.
- The output checkpoint path will not overwrite an important run.
- Full training is approved by the user as a long-running, compute-heavy action.
