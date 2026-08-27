# ImageAI Custom Training Data Formats

This reference describes the on-disk layouts consumed by ImageAI 3.x custom
trainers. Paths below are relative to the dataset root that you pass to
`setDataDirectory(...)`.

## Classification dataset schema

`ClassificationModelTrainer` loads data with TorchVision `ImageFolder` from two
fixed split directories: `train` and `test`.

```text
<dataset>/
  train/
    <class_name_1>/
      image_001.jpg
      image_002.png
    <class_name_2>/
      image_101.jpg
  test/
    <class_name_1>/
      image_201.jpg
    <class_name_2>/
      image_301.jpg
```

Rules:

- The split directory names must be exactly `train` and `test`.
- Each direct child directory under `train` is a class name. The `test` split
  should contain the same class directory names.
- Put images directly inside each class directory. Nested subdirectories are not
  a portable contract for the current trainer.
- Empty class directories fail at data loading or produce unusable training.
- Supported image extensions follow TorchVision/Pillow conventions, including
  `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`, `.webp`, `.ppm`, and `.pgm`.
- Class index order is the sorted `ImageFolder` class order. The trainer writes
  `<dataset_name>_model_classes.json` containing stringified indexes mapped to
  class names.
- For practical accuracy, use many images per class and reserve representative
  images for `test`; a tiny dataset is useful only for smoke checks.

Validation command:

```bash
python scripts/validate_imageai_dataset.py --task classification --dataset-dir <dataset> --strict
```

## Detection dataset schema

`DetectionModelTrainer` uses ImageAI 3.x YOLO text annotations, not Pascal VOC
XML. The dataset root can have any name but must contain these fixed split and
leaf directory names:

```text
<dataset>/
  train/
    images/
      img_001.jpg
      img_002.png
    annotations/
      img_001.txt
      img_002.txt
  validation/
    images/
      img_101.jpg
    annotations/
      img_101.txt
```

Rules:

- The split names must be exactly `train` and `validation`.
- Each split must contain `images` and `annotations` directories.
- Every supported image should have a matching `.txt` annotation with the same
  file stem. Example: `images/case-17.jpg` must match
  `annotations/case-17.txt`.
- Extra annotation files without matching images are mistakes because the
  current loader discovers images and then derives annotation paths from image
  stems.
- Duplicate stems in the same image directory, such as `cat.jpg` and `cat.png`,
  are ambiguous; avoid them.
- The loader accepts readable image files via OpenCV. Use common formats such as
  `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`, or `.webp`.

Validation command:

```bash
python scripts/validate_imageai_dataset.py --task detection --dataset-dir <dataset> --strict
```

## YOLO annotation row format

Each non-empty row in a detection annotation file must have five whitespace
separated values:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Where:

- `class_id` is a zero-based integer.
- `x_center`, `y_center`, `width`, and `height` are normalized floats in
  `[0, 1]` relative to the original image width and height.
- `width` and `height` must be greater than zero.
- In strict validation, the derived box extents must stay inside the normalized
  image frame.

Example for two boxes:

```text
0 0.513333 0.438889 0.220000 0.166667
1 0.301667 0.612500 0.130000 0.245000
```

Use the same class-id order when calling:

```python
trainer.setTrainConfig(object_names_array=["class_for_id_0", "class_for_id_1"])
```

A `classes.txt` file is not required by ImageAI itself, but the bundled
converter writes it and the validator uses it to check class-id ranges. Keep one
label per line in zero-based id order.

## Pascal VOC input expected by the bundled converter

The converter expects Pascal VOC XML files in the same split structure as the
ImageAI detection dataset, except that annotations are XML before conversion:

```text
<voc-dataset>/
  train/
    images/
      img_001.jpg
    annotations/
      img_001.xml
  validation/
    images/
      img_101.jpg
    annotations/
      img_101.xml
```

Every image stem must match one XML stem. The converter validates:

- required `train` and `validation` splits;
- required `images` and `annotations` leaves;
- missing or extra image/XML pairs;
- XML parseability;
- `<size><width>...` and `<height>...` values;
- each `<object><name>...` label;
- each `<object><bndbox>` with `xmin`, `ymin`, `xmax`, and `ymax`;
- positive box size and boxes inside the XML image size.

Conversion command:

```bash
python scripts/pascal_voc_to_yolo.py --dataset-dir <voc-dataset> --output-dir <voc-dataset-yolo>
```

The output contains ImageAI-ready `train` and `validation` folders plus
`classes.txt` at the dataset root and inside each output annotations directory.
