# SiamMask Data Layouts

## Benchmark Data

### VOT2016/VOT2018/VOT2019

Expected layout under a data root:

```text
data/
  VOT2016/
    list.txt
    <video>/groundtruth.txt
    <video>/*.jpg or <video>/color/*.jpg
  VOT2016.json
  VOT2018/
  VOT2018.json
  VOT2019/
  VOT2019.json
```

The VOT JSON files feed the evaluation toolkit. Existing VOT directories can be converted with `scripts/generate_vot_json.py`.

### DAVIS2016/DAVIS2017

Expected layout:

```text
data/
  DAVIS/
    ImageSets/2016/val.txt
    ImageSets/2017/val.txt
    JPEGImages/480p/<video>/*.jpg
    Annotations/480p/<video>/*.png
  DAVIS2016 -> DAVIS   # optional compatibility symlink
  DAVIS2017 -> DAVIS   # optional compatibility symlink
```

SiamMask loads DAVIS data through the shared `DAVIS` directory and year-specific ImageSets.

### YouTube-VOS Validation

Expected benchmark-style layout:

```text
data/
  ytb_vos/
    valid/meta.json
    valid/JPEGImages/<video>/*.jpg
    valid/Annotations/<video>/*.png
```

## Training Data

Training configs reference crop/index outputs, not raw archives directly.

### COCO

Expected generated layout:

```text
data/coco/
  annotations/instances_train2017.json
  annotations/instances_val2017.json
  train2017/
  val2017/
  crop511/train2017/<image-id>/*.x.jpg
  crop511/train2017/<image-id>/*.m.png
  train2017.json
  val2017.json
  pycocotools/
```

COCO is mask-capable and is used by base/refine training.

### ImageNet DET

Expected generated layout:

```text
data/det/
  ILSVRC2015/Annotations/DET/train/...
  ILSVRC2015/Data/DET/train/...
  crop511/...
  train.json
```

DET contributes detection-style single-frame object crops.

### ImageNet VID

Expected generated layout:

```text
data/vid/
  ILSVRC2015/Annotations/VID/train/...
  ILSVRC2015/Data/VID/train/...
  vid.json
  crop511/...
  train.json
  val.json
```

VID contributes temporal object tracks and validation splits.

### YouTube-VOS Training

Expected generated layout:

```text
data/ytb_vos/
  train/meta.json
  train/JPEGImages/<video>/*.jpg
  train/Annotations/<video>/*.png
  instances_train.json
  instances_val.json
  crop511/train/<video>/*.x.jpg
  crop511/train/<video>/*.m.png
  train.json
```

YouTube-VOS supplies mask-capable training samples for SiamMask base/refine workflows.

## Read-Only Layout Check

Use:

```bash
python scripts/check_dataset_layout.py --data-root <siammask-checkout>/data --dataset training
```

Use `--strict` only when missing optional datasets should fail the surrounding automation.
