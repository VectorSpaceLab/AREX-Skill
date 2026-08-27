# Dataset formats for Pytorch-UNet

This reference distills the dataset contracts used by Pytorch-UNet training.

## Directory layout

The default training code expects two flat directories:

```text
data/
  imgs/
    <id>.<image-extension>
  masks/
    <id><mask-suffix>.<mask-extension>
```

Default paths in the training module are `./data/imgs/` for images and `./data/masks/` for masks. The loader is intentionally greedy and flat: do not put subdirectories inside either folder. Hidden files whose names start with `.` are ignored for image IDs, but ordinary extra files can create duplicate or missing ID matches.

## Generic versus Carvana naming

Pytorch-UNet has two dataset classes:

| Class | Constructor | Mask filename rule | Typical use |
| --- | --- | --- | --- |
| `BasicDataset` | `BasicDataset(images_dir, mask_dir, scale=1.0, mask_suffix="")` | image `car.jpg` matches mask `car.*` | Generic segmentation data where image and mask basenames match. |
| `CarvanaDataset` | `CarvanaDataset(images_dir, mask_dir, scale=1)` | image `car.jpg` matches mask `car_mask.*` | Kaggle Carvana data, where masks carry `_mask`. |

The training code tries `CarvanaDataset` first and falls back to `BasicDataset` when Carvana-style loading fails. For a custom dataset, use whichever naming convention you actually have and avoid mixing both in the same mask directory.

## Supported image and mask loaders

The loader accepts ordinary image files through Pillow and also supports NumPy/PyTorch tensor files:

- `.npy` is loaded with `numpy.load` and converted to a Pillow image.
- `.pt` and `.pth` are loaded with `torch.load`, converted to a NumPy array, and then to a Pillow image.
- Other extensions are passed to `PIL.Image.open`.

Images and masks must have identical pixel sizes before scaling. If one image ID has zero matches or multiple matches in either directory, dataset indexing raises an assertion error.

## Scale constraints

`scale` must satisfy `0 < scale <= 1`. The preprocessing step computes `new_width = int(scale * width)` and `new_height = int(scale * height)`, so very small images or tiny scales can fail with the assertion that resized dimensions would have no pixels.

Training defaults to `--scale 0.5`. Use `--scale 1` for full resolution when memory permits, and reduce it when CUDA or CPU memory is limited.

## Tensor shapes and normalization

For images:

- RGB images become channel-first arrays with shape `(3, H, W)`.
- Grayscale images become `(1, H, W)`.
- Pixel values greater than `1` are divided by `255.0`, producing float-like normalized values.

For masks:

- Masks become integer class-index arrays with shape `(H, W)`.
- The loader scans all masks to build `dataset.mask_values`, a sorted list of unique grayscale values or RGB tuples.
- During preprocessing, each discovered pixel value is mapped to its class index.

Training returns batches shaped like:

```python
{
    "image": torch.FloatTensor[N, C, H, W],
    "mask": torch.LongTensor[N, H, W],
}
```

The model's `n_channels` must match image channels, and `n_classes` must be larger than the largest class index in the masks.

## Mask values and checkpoints

At checkpoint time, training saves `dataset.mask_values` inside the model state dictionary under key `mask_values`. This is metadata, not a model parameter. Prediction code uses it later to convert class-index masks back to original mask pixel values.

For binary masks, common palettes are `[0, 1]`, `[0, 255]`, or two RGB tuples. Do not assume `[0, 1]` unless the training masks actually used that palette or the checkpoint lacks metadata and the user confirms a binary convention.

## Data acquisition caution

The original data helper downloads Kaggle Carvana archives and writes into `data/imgs` and `data/masks`. It requires network access, `kaggle`, credentials, `unzip`, and enough disk space. Treat it as a setup recipe requiring user approval, not as a safe default validation step.
