# Data Formats

## ImageNet folder mode

For `DATA.DATASET: imagenet` without `--zip`, the data root should contain:

```text
<data-root>/
  train/
    class_a/*.JPEG
    class_b/*.JPEG
  val/
    class_a/*.JPEG
    class_b/*.JPEG
```

Both `train` and `val` are read by `torchvision.datasets.ImageFolder`, so validation images must already be grouped into class subdirectories.

## Zipped ImageNet mode

When the supervised script receives `--zip`, the loader expects the root to contain:

```text
<data-root>/
  train.zip
  val.zip
  train_map.txt
  val_map.txt
```

Map files use one sample per line with a relative path and integer label separated by whitespace, commonly a tab:

```text
n01440764/n01440764_10026.JPEG 0
ILSVRC2012_val_00000001.JPEG 65
```

`--cache-mode part` shards cached samples across distributed ranks. `--cache-mode full` is heavier and should be chosen only when memory is available.

## ImageNet-22K mode

When `DATA.DATASET: imagenet22K`, the dataset class reads JSON map files. The expected data root contains map files such as:

```text
<data-root>/
  ILSVRC2011fall_whole_map_train.txt
  ILSVRC2011fall_whole_map_val.txt
  fall11_whole/
    n00004475/...
```

The map file content is JSON loaded into a list-like database. Each item should contain a relative image path and a label.

## SimMIM data

SimMIM pretraining uses an ImageFolder-like training directory and transforms each image into `(image, mask)` through `MaskGenerator`. Fine-tuning/evaluation use the standard ImageNet train/val folder layout. The mask settings must satisfy:

- `DATA.IMG_SIZE % DATA.MASK_PATCH_SIZE == 0`
- `DATA.MASK_PATCH_SIZE % model_patch_size == 0`

## Validation

Run:

```bash
python sub-skills/data-and-checkpoints/scripts/validate_imagenet_layout.py --mode folder --data-path <data-root>
python sub-skills/data-and-checkpoints/scripts/validate_imagenet_layout.py --mode zip --data-path <data-root>
python sub-skills/data-and-checkpoints/scripts/validate_imagenet_layout.py --mode imagenet22k-json --data-path <data-root>
```
