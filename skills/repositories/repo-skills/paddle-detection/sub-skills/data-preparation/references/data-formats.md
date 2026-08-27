# Dataset Formats and Layouts

## Detection and segmentation

**COCO** uses `images/` plus `annotations/*.json`. Each annotation references `image_id` and `category_id`; detection `bbox` is `[x, y, width, height]`. Keep `categories`, `images`, and `annotations` consistent, and ensure every file named by `images.file_name` exists.

**VOC** uses image files plus same-stem XML files and a class list. XML boxes are `xmin,ymin,xmax,ymax`. The target checkout's VOC configs also expect generated image lists or standard VOC directory names.

**WIDER-FACE** and other specialized datasets use their own readers/configs; do not reuse COCO fields without reading the selected dataset config.

## Keypoints

COCO keypoint annotations store `[x, y, visibility]` triples in the configured joint order. Visibility distinguishes unlabeled, labeled-but-not-visible, and visible points. A converted dataset must preserve joint order and coordinate/image path semantics.

## MOT

A MOT sequence generally contains `images/train/<sequence>/img1`, sequence metadata, and matching `labels_with_ids/train/<sequence>/*.txt`. Each label line is:

```text
class identity x_center y_center width height
```

Coordinates are normalized to the image. `identity=-1` means no identity annotation. The source data preparation docs also describe `gt.txt` and `seqinfo.ini`; use `tools/gen_labels_MOT.py` only after confirming that layout.

## Config coupling

Dataset roots and annotation paths are read from the selected YAML config. Before training, check:

1. image root and annotation path resolve from the dataset root;
2. all referenced images exist and decode;
3. category/label names match the config label list;
4. `num_classes` matches the selected reader/head;
5. the metric matches the schema (`COCO`, `VOC`, `MOT`, keypoint, rotated box, or lane);
6. any class remapping is recorded and tested on a tiny sample.
