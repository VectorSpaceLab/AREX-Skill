# Datasets and augmentation

This reference is self-contained guidance for SSD.PyTorch training data preparation. It describes what the training data loader expects; it does not download data.

## Shared data conventions

- Images are read with OpenCV, so raw images enter transforms in BGR channel order.
- Mean subtraction uses `MEANS = (104, 117, 123)`, also in BGR order.
- Training uses SSD300 settings with `min_dim = 300`.
- Annotation targets are lists of rows shaped `[xmin, ymin, xmax, ymax, label_index]` where coordinates are normalized to `[0, 1]` before augmentation.
- The model configs include background in `num_classes`:
  - VOC config: 20 foreground labels + background = `num_classes: 21`.
  - COCO config in this repository: `num_classes: 201`; the bundled COCO label map itself maps 80 COCO foreground categories to contiguous ids.

## VOC layout

`VOCDetection` expects `root` to be the VOCdevkit directory containing per-year folders:

```text
VOCDEVKIT_ROOT/
  VOC2007/
    Annotations/
      000001.xml
    JPEGImages/
      000001.jpg
    ImageSets/
      Main/
        trainval.txt
        test.txt
  VOC2012/
    Annotations/
    JPEGImages/
    ImageSets/
      Main/
        trainval.txt
```

Default training uses both `VOC2007/trainval` and `VOC2012/trainval`. Common VOC2007 evaluation/test data uses `VOC2007/test`, but evaluation routing belongs to the evaluation-demos sub-skill.

### VOC dataset and transform signatures

- `VOCDetection(root, image_sets=[('2007', 'trainval'), ('2012', 'trainval')], transform=None, target_transform=VOCAnnotationTransform(), dataset_name='VOC0712')`
- `VOCAnnotationTransform(class_to_ind=None, keep_difficult=False)`

### VOC annotation behavior

- XML files are parsed from `Annotations/<image_id>.xml`.
- Image files are read from `JPEGImages/<image_id>.jpg`.
- Split files under `ImageSets/Main/*.txt` provide one image id per line, without extension.
- Object boxes are read from `bndbox/xmin,ymin,xmax,ymax`.
- Coordinates are converted from 1-based VOC pixels by subtracting 1, then normalized by width or height.
- Objects with `<difficult>1</difficult>` are skipped unless `keep_difficult=True` is used.
- VOC class order is: aeroplane, bicycle, bird, boat, bottle, bus, car, cat, chair, cow, diningtable, dog, horse, motorbike, person, pottedplant, sheep, sofa, train, tvmonitor.

## COCO layout

`COCODetection` expects `root` to be a COCO directory with images, annotations, a label map, and either a local COCO PythonAPI or an environment where `pycocotools` is importable:

```text
COCO_ROOT/
  images/
    trainval35k/
      *.jpg
    val2014/
      *.jpg
  annotations/
    instances_trainval35k.json
    instances_val2014.json
  PythonAPI/                 # optional when pycocotools is already installed
  coco_labels.txt
```

Default COCO training uses `image_set='trainval35k'`, so the required training pair is:

- `images/trainval35k/`
- `annotations/instances_trainval35k.json`

### COCO dataset and transform signatures

- `COCODetection(root, image_set='trainval35k', transform=None, target_transform=COCOAnnotationTransform(), dataset_name='MS COCO')`
- `COCOAnnotationTransform()`

### COCO annotation behavior

- The loader appends `root/PythonAPI` to `sys.path`, then imports `pycocotools.coco.COCO`.
- It opens `annotations/instances_<image_set>.json`.
- It reads images from `images/<image_set>/<file_name>`.
- COCO boxes are converted from `[x, y, width, height]` to `[xmin, ymin, xmax, ymax]`, normalized by image width/height, and assigned a zero-based contiguous label index.
- The COCO label-map file format is one mapping per line: `raw_category_id,contiguous_id,class_name`.
- The label map has 80 foreground categories. Raw COCO ids are not fully contiguous, so do not replace the map with `1..80` unless the raw category ids in the annotation JSON also match.

### COCO import-time label-map caveat

The default `target_transform=COCOAnnotationTransform()` is evaluated while the COCO dataset module is imported. Because the package-level data module imports COCO eagerly, `from data import *` can fail before command-line arguments are parsed if the default home-derived COCO label-map file is absent. When training COCO or even importing the package-level `data` module, ensure the expected `coco_labels.txt` exists at the default COCO label-map location, or patch the default target-transform construction in a local working copy.

## BaseTransform behavior

`BaseTransform(size, mean)` is a deterministic resize/mean-subtraction transform:

1. Resize the image to `(size, size)` with OpenCV.
2. Convert to `float32`.
3. Subtract the BGR mean.
4. Return `(image, boxes, labels)` without modifying boxes or labels.

Use this for deterministic preprocessing contexts such as inference or evaluation planning, not as the main training augmentation path.

## SSDAugmentation behavior

`SSDAugmentation(size=300, mean=(104, 117, 123))` composes the SSD training augmentation chain:

1. Convert image integers to `float32`.
2. Convert normalized boxes to absolute pixel coordinates.
3. Apply photometric distortion: brightness, contrast, HSV saturation/hue, and channel lighting noise.
4. Optionally expand the image canvas using the mean color.
5. Randomly crop while respecting sampled IoU constraints and retaining boxes whose centers remain in the crop.
6. Randomly mirror horizontally.
7. Convert boxes back to normalized percent coordinates.
8. Resize to `300 x 300` by default.
9. Subtract the BGR mean.

Dataset `pull_item` then swaps channels from BGR to RGB before returning a `torch` tensor shaped `[C, H, W]`. Keep this BGR-to-RGB step in mind when debugging visualized tensors or writing custom preprocessing.

## detection_collate behavior

The custom collate function is required because each image may have a different number of objects.

Input batch item shape:

```text
(image_tensor, target_rows)
```

Output batch shape:

```text
images:  Tensor[N, C, H, W]
targets: List[FloatTensor[num_objects_i, 5]]
```

Do not replace it with the default PyTorch collate for detection training; default collation tries to stack all targets into a rectangular tensor and fails when images have different object counts.

## Empty or malformed annotation risk

Training augmentation assumes `target` can be converted to a 2-D array with at least columns `0:4` and `4`. Empty annotations, split ids pointing to missing XML/JSON entries, or all-VOC-difficult objects being skipped can produce empty target arrays and later indexing failures. Filter such samples, keep difficult VOC objects only when appropriate, or add explicit empty-target handling in a local experiment before launching a long run.

## Dataset script side effects, reference-only

The repository includes shell scripts for VOC2007, VOC2012, and COCO2014 setup. Treat them only as evidence for expected layouts and side effects:

- They perform network downloads.
- They create directories under a default user data location when no argument is given.
- VOC scripts download tar files, extract them, then delete the tar files.
- The COCO script downloads image and annotation zip files, extracts them, creates `trainval35k`, copies many images, downloads additional trainval35k annotations, and deletes zip files.
- They are not bundled in this sub-skill and must not be executed as part of skill validation.

Use `scripts/validate_dataset_layout.py` for a no-download skeleton check instead.
