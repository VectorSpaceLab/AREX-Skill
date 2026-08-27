# FCOS Dataset Layouts and Formats

## Dataset catalog roots

The dataset catalog uses a root named `datasets` and defines COCO, PASCAL VOC, and Cityscapes-style entries.

## COCO-style layout

Expected relative shape:

```text
datasets/
  coco/
    train2014/ or train2017/
    val2014/ or val2017/
    test2017/
    annotations/
      instances_train2014.json
      instances_val2014.json
      instances_minival2014.json
      instances_valminusminival2014.json
```

FCOS evaluation reports COCO-style AP metrics for detection.

## PASCAL VOC layout

VOC entries expect a directory such as:

```text
datasets/voc/VOC2007/
  JPEGImages/
  Annotations/
  VOCdevkit2007/
```

Some COCO-style VOC annotations can be used for COCO-style outputs.

## Cityscapes layout

Cityscapes entries expect:

```text
datasets/cityscapes/
  images/
  annotations/
    instancesonly_filtered_gtFine_train.json
    instancesonly_filtered_gtFine_val.json
    instancesonly_filtered_gtFine_test.json
```

The source converter depends on external Cityscapes scripts and raw Cityscapes downloads. Treat full conversion as a data-preparation task requiring user-provided data and account access.

## Validation helper

```bash
python sub-skills/data-configs/scripts/validate_dataset_layout.py --kind coco --root datasets
python sub-skills/data-configs/scripts/validate_dataset_layout.py --kind voc --root datasets/voc/VOC2007
python sub-skills/data-configs/scripts/validate_dataset_layout.py --kind cityscapes --root datasets/cityscapes
```
