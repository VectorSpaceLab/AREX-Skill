# Dataset Output Formats

Read this before checking files produced by `base_model.label(...)` or before passing an Autodistill-generated dataset to a target model plugin.

## Detection Dataset Layout

`DetectionBaseModel.label(...)` exports through `supervision.DetectionDataset.as_yolo(...)` and then calls `autodistill.helpers.split_data(...)`. Expect this shape after a successful run:

```text
<output_folder>/
  data.yaml
  train/
    images/
      *.jpg
    labels/
      *.txt
      confidence-*.txt   # only when record_confidence=True
  valid/
    images/
      *.jpg
    labels/
      *.txt
      confidence-*.txt   # only when record_confidence=True
```

During export, intermediate `images/` and `annotations/` directories may be created and then moved into the split folders.

`data.yaml` is rewritten with:

```yaml
train: <absolute-path-to-output>/train/images
val: <absolute-path-to-output>/valid/images
nc: <number-of-classes>
names:
  - <class-name>
```

Future agents should treat the generated `data.yaml` paths as tied to the user's output directory. If moving the dataset, regenerate or edit `data.yaml` paths accordingly.

## Detection Label Files

YOLO label files are written by `supervision`. A normal detection line has normalized center/width/height coordinates and class id. When `record_confidence=True`, Autodistill also writes one confidence value per detection in `confidence-<image-stem>.txt`.

Use these checks:

- Every image that should contain detections has a matching label file under `train/labels` or `valid/labels`.
- `data.yaml` `names` order matches `ontology.classes()`.
- If `record_confidence=True`, every label file has a matching `confidence-*` file and the base model returned confidence scores.

## Split Behavior and Side Effects

`split_data(base_dir, split_ratio=0.8, record_confidence=False)` shuffles image stems, sends the first 80% to train, and the rest to valid. With very small datasets this can produce an empty train or valid set; use at least two images in smoke tests.

Before splitting, `split_data` normalizes image extensions under the intermediate `images/` directory:

- filenames containing duplicate dots are normalized by replacing `..` with `.`;
- `.png` files are converted to `.jpg` and removed;
- `.jpeg` files are converted to `.jpg` and removed.

This mutates the output dataset directory, not the original input folder.

## Classification Dataset Layout

`ClassificationBaseModel.label(...)` writes folder structures after splitting a `supervision.ClassificationDataset`:

```text
<output_folder>/
  train/
    <class-name>/
      images...
  test/
    <class-name>/
      images...
  valid/
    <class-name>/
      images...
```

Classification splits are 70% train, 15% test, 15% valid via two `dataset.split(...)` calls. Verify concrete plugin behavior before relying on class-probability thresholds or target-training arguments.

## Large Dataset Constraint

Autodistill 0.1.29 stores image paths and detection/classification maps in memory during labeling. For very large folders, label in smaller batches, use explicit output directories per batch, and validate each `data.yaml` before combining or training.
