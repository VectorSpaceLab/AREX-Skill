# GFPGAN Data Layout and Dataset Reference

## Purpose

Read this when preparing data for `FFHQDegradationDataset`, choosing disk versus LMDB IO, enabling component crops, or diagnosing dataset-return keys and shapes.

## Disk Layout

For `io_backend.type: disk`, `dataroot_gt` should be a folder of high-quality face images. GFPGAN scans image paths from that folder and creates low-quality images on the fly.

Config shape:

```yaml
datasets:
  train:
    type: FFHQDegradationDataset
    dataroot_gt: datasets/ffhq/ffhq_512
    io_backend:
      type: disk
    mean: [0.5, 0.5, 0.5]
    std: [0.5, 0.5, 0.5]
    out_size: 512
```

## LMDB Layout

For `io_backend.type: lmdb`, `dataroot_gt` must end with `.lmdb`. The dataset opens `meta_info.txt` inside that LMDB directory and uses line stems as keys.

Config shape:

```yaml
datasets:
  train:
    type: FFHQDegradationDataset
    dataroot_gt: datasets/ffhq/ffhq_512.lmdb
    io_backend:
      type: lmdb
```

If the path does not end in `.lmdb`, the source dataset raises a `ValueError`.

## Degradation Pipeline

For each high-quality image, the dataset:

1. Applies horizontal flip augmentation if enabled.
2. Optionally reads facial component coordinates.
3. Applies a random blur kernel from `kernel_list` / `kernel_prob` and `blur_sigma`.
4. Downsamples by a random factor from `downsample_range`.
5. Adds Gaussian noise from `noise_range` when enabled.
6. Adds JPEG compression from `jpeg_range` when enabled.
7. Resizes back to original size.
8. Optionally applies color jitter or grayscale transforms.
9. Converts BGR/HWC NumPy arrays to normalized RGB/CHW tensors.

## Returned Keys

Without component crops, `FFHQDegradationDataset.__getitem__` returns:

```text
gt: Tensor shape (3, 512, 512)
lq: Tensor shape (3, 512, 512)
gt_path: source path or LMDB key
```

With `crop_components: true`, it also returns:

```text
loc_left_eye: Tensor shape (4,)
loc_right_eye: Tensor shape (4,)
loc_mouth: Tensor shape (4,)
```

## Landmark `.pth` Schema

The component landmark file loaded by `component_path` should be a PyTorch-saved dictionary keyed by zero-padded item ids such as `00000000`. Each item maps to component triples:

```python
{
    "00000000": {
        "left_eye": [x_center, y_center, half_length],
        "right_eye": [x_center, y_center, half_length],
        "mouth": [x_center, y_center, half_length],
    }
}
```

The dataset converts each triple to `[x1, y1, x2, y2]` boxes, applies `eye_enlarge_ratio` to eye half-lengths, and handles horizontal flip by swapping left/right eyes and mirroring coordinates.

## Using The Bundled Landmark Parser

```bash
python sub-skills/training/scripts/parse_ffhq_landmarks.py \
  --json-path ffhq-dataset-v2.json \
  --save-path FFHQ_eye_mouth_landmarks_512.pth \
  --scale 0.5 \
  --enlarge-ratio 1.4
```

Use `--save-crops-dir` only when you explicitly want visual crop previews. Without that option, the parser does not need image data and only saves the landmark dictionary.

## Data Validation Checklist

- `io_backend.type` matches the actual data path type.
- LMDB paths end in `.lmdb` and contain `meta_info.txt`.
- Disk paths contain readable images.
- `component_path` exists when `crop_components: true`.
- Landmark dictionary keys match dataset item order/names.
- `mean`, `std`, and `out_size` match the model assumptions.
