# Data workflows

## Core APIs and helpers

### Loader signatures captured from this checkout

- `LoadImagesAndLabels(path, img_size=640, batch_size=16, augment=False, hyp=None, rect=False, image_weights=False, cache_images=False, single_cls=False, stride=32, pad=0.0)`
- `create_dataloader(path, imgsz, batch_size, stride, opt, hyp=None, augment=False, cache=False, pad=0.0, rect=False, local_rank=-1, world_size=1)`
- `letterbox(img, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True)`
- `random_perspective(img, targets=(), degrees=10, translate=0.1, scale=0.1, shear=10, perspective=0.0, border=(0, 0))`

### Shared data helpers

- `augment_hsv` for color jitter.
- `load_mosaic` and `replicate` for training-time augmentation.
- `reduce_img_size` for shrinking a folder of images.
- `recursive_dataset2bmp` for dataset conversion.
- `imagelist2folder` for turning a text image list into a folder.
- `create_folder` for safe directory creation.
- `kmean_anchors` for fitting anchors from a dataset or dataset YAML.

## Dataset YAML workflow

1. Read the YAML.
2. Confirm `train` and `val` are present.
3. Confirm `nc` and `names` describe the same class universe.
4. Resolve the split sources relative to the repository root or the YAML’s path, whichever the caller intentionally chose.
5. Inspect a small sample from each split before larger-scale work.
6. When you just need a self-contained smoke check, start with the bundled `runtime/data/demo.yaml` and the tiny `runtime/demo/` image/label pair that ships with the skill.

## Label workflow

The repository expects YOLO labels in the familiar five-column format:

- class id
- x center
- y center
- width
- height

All coordinates are normalized.

The loader also expects the label filename to mirror the image filename. When images live under an `images/` tree, labels normally live under a matching `labels/` tree.

## Augmentation workflow

- `letterbox` handles the padded resize used by both training and inference.
- `random_perspective` and `augment_hsv` are the main training-time augmentation steps.
- `load_mosaic` combines four images into one training sample.
- `mixup` is controlled by the hyperparameter file and applied after mosaic loading when enabled.

## Cache workflow

- `LoadImagesAndLabels` writes a `.cache` file beside the label directory.
- Rebuild the cache whenever labels, image paths, or splits change.
- If the cache keeps pointing to broken paths, the data source itself is still wrong and should be fixed first.

## Anchor workflow

`kmean_anchors` can use either a dataset object or a dataset YAML path. It is useful when:

- anchors fit poorly,
- the dataset distribution is very different from COCO,
- or you want to validate that the default anchors are not obviously mismatched.

Do not use anchor fitting as a substitute for fixing label format or path problems.

## Data sanity checklist

- Image paths resolve.
- Label paths mirror image paths.
- Labels have five columns.
- Coordinates stay in bounds.
- `nc` matches `names`.
- Cached metadata reflects the current dataset version.
