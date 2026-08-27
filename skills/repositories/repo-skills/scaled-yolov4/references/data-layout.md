# Data layout

## Dataset YAMLs

The repository expects dataset YAML files with at least these keys:

- `train`
- `val`
- `test` when you need the test split
- `nc`
- `names`

`data/coco.yaml` is the canonical example in this checkout. It points to text files that list image paths and defines the 80 COCO class names. The bundled `runtime/` mirror also includes a tiny `data/demo.yaml` plus `runtime/demo/images/` and `runtime/demo/labels/` so smoke helpers can validate a self-contained dataset layout without the original checkout.

## Image and label pairing

`utils/datasets.py: LoadImagesAndLabels` expects a YOLO-style image/label pairing:

- Images live under an `images/` tree or are listed in a `.txt` file.
- Labels live under a matching `labels/` tree with the same basename and a `.txt` extension.
- Each label row contains five whitespace-separated columns: `class x_center y_center width height`.
- Coordinates are normalized to `[0, 1]`.
- Class ids are zero-based integers.

## Supported media inputs

For inference, `LoadImages` accepts:

- individual files
- directories
- glob patterns
- text files that list files

Supported image extensions include `.bmp`, `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, and `.dng`. Supported video extensions include `.mov`, `.avi`, `.mp4`, `.mpg`, `.mpeg`, `.m4v`, `.wmv`, and `.mkv`.

## Cache and sampling behavior

`LoadImagesAndLabels` creates a `.cache` file beside the label directory and uses it to store image-shape and label metadata. It also supports:

- `rect` rectangular training
- `cache_images` memory caching
- `image_weights` sampling
- `single_cls` mode
- mosaic and mixup augmentation during training

## Shared data helpers

These helpers matter across training, evaluation, and inference:

- `letterbox` for padded resize
- `random_perspective` for geometric augmentation
- `augment_hsv` for color augmentation
- `load_mosaic` and `replicate` for training augmentation
- `reduce_img_size` for dataset shrinking
- `recursive_dataset2bmp` for image conversion
- `imagelist2folder` for splitting text-based image lists into folders
- `create_folder` for safe directory creation
- `kmean_anchors` for anchor fitting

## Sanity rules

- `names` length should match `nc`.
- Label files must have exactly five columns when loaded as YOLO labels.
- Boxes should not be negative or out of bounds.
- Image size and stride need to agree with the model’s maximum stride.
- `check_file` resolves paths relative to the current working directory, so path normalization matters when a YAML points to relative assets.
