# Data-preparation workflows

This page gives the practical recipes for the repository's supported dataset layouts.

## 1. Unaligned CUT/FastCUT dataset

Use this when the model should load images from two independent domains.

### Layout

```text
root/
  trainA/
  trainB/
  testA/
  testB/
```

### Result

- `data.unaligned_dataset.UnalignedDataset` reads these folders.
- `testA/testB` may fall back to `valA/valB` if the test split is missing.

### Typical use

Prepare the folders, then run the translation workflow.

## 2. Single-image SinCUT dataset

Use this when each domain has one image only.

### Layout

```text
root/
  trainA/one_image_A.jpg
  trainB/one_image_B.jpg
```

### Result

- `data.singleimage_dataset.SingleImageDataset` expects exactly one image in each domain.
- The loader repeats randomized crops and patches from the same source image.

## 3. Cityscapes conversion

Use `scripts/prepare_cityscapes_dataset.py` when you have raw Cityscapes `gtFine_trainvaltest` and `leftImg8bit_trainvaltest` downloads.

### Inputs

- `--gtFine_dir`: path to the unzipped `gtFine_trainvaltest` tree.
- `--leftImg8bit_dir`: path to the unzipped `leftImg8bit_trainvaltest` tree.
- `--output_dir`: destination folder for the prepared dataset.

### Outputs

- `train/` and `test/` side-by-side JPEGs for pix2pix-style loading.
- `trainA/`, `trainB/`, `testA/`, and `testB/` for CUT/CycleGAN-style loading.

### Example

```bash
python scripts/prepare_cityscapes_dataset.py \
  --gtFine_dir /data/cityscapes/gtFine_trainvaltest \
  --leftImg8bit_dir /data/cityscapes/leftImg8bit_trainvaltest \
  --output_dir /data/cityscapes/cut_ready
```

## 4. Pair assembly from A/B trees

Use `scripts/combine_A_and_B.py` when you already have two parallel image trees and want paired side-by-side composites.

### Layout expected by the helper

```text
fold_A/
  split_name/
    image_001.jpg
fold_B/
  split_name/
    image_001.jpg
```

### Result

The helper writes paired images into `fold_AB/split_name/`.

### Example

```bash
python scripts/combine_A_and_B.py \
  --fold_A /data/A \
  --fold_B /data/B \
  --fold_AB /data/AB
```

## 5. Aligned composite export

Use `scripts/make_dataset_aligned.py` when your dataset already has matching files in `trainA/trainB` and `testA/testB` and you want a side-by-side aligned view.

### Expected tree

```text
root/
  trainA/
  trainB/
  testA/
  testB/
```

### Result

The helper writes paired images into `root/train/` and `root/test/`.

### Example

```bash
python scripts/make_dataset_aligned.py --dataset-path /data/aligned_dataset
```

## 6. Cat-face crop helper

Use `scripts/detect_cat_face.py` to crop cat faces from a directory of images. This helper needs an OpenCV Haar cascade XML file; pass `--cascade_path` when the active OpenCV install does not provide a cat-face cascade.

### Inputs

- `--input_dir`: directory containing the source images.
- `--output_dir`: directory for cropped images.
- `--cascade_path`: explicit cat-face cascade XML path, recommended for reproducibility.
- `--use_ext`: choose the extended cat-face cascade name when the active OpenCV install provides one.
- `--border-ratio` and `--output-width`: adjust crop padding and output size.

### Result

Each detected face is written as a resized JPEG crop.

### Example

```bash
python scripts/detect_cat_face.py \
  --input_dir /data/raw_cats \
  --output_dir /data/cat_faces \
  --cascade_path /path/to/haarcascade_frontalcatface.xml
```

## Safety notes

- The bundled helpers never download data.
- They only transform or validate local files and directories.
- Large external datasets and license-gated downloads remain outside the runtime skill.
