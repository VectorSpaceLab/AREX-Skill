# PyTorch Integration Reference

Albumentations is NumPy-first. In PyTorch-style code, read or decode data to NumPy, run `A.Compose` inside `Dataset.__getitem__`, and put tensor conversion as the final transform. Use `from albumentations.pytorch import ToTensorV2, ToTensor3D` or `A.ToTensorV2` / `A.ToTensor3D` when the optional `torch` dependency is installed.

## Dataset Placement

```python
import albumentations as A
from albumentations.pytorch import ToTensorV2

transform = A.Compose(
    [
        A.RandomResizedCrop(size=(224, 224), p=1.0),
        A.HorizontalFlip(p=0.5),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ],
    strict=True,
)

def __getitem__(index):
    image = load_image_as_rgb_numpy(index)      # H,W,C, usually uint8
    mask = load_mask_as_numpy(index)            # H,W for class labels, or H,W,C for multi-channel masks
    data = transform(image=image, mask=mask)
    return {"image": data["image"], "mask": data["mask"]}
```

Keep PIL images, file paths, tensors, and framework batches outside the Albumentations call unless a transform explicitly supports them. Core transforms expect NumPy target arrays and return a dict keyed by target name.

## `ToTensorV2` Contract

`ToTensorV2(transpose_mask=False, p=1.0)` converts 2D image-style targets to `torch.Tensor` without changing numeric values.

| Input target | Input shape | Output shape | Notes |
| --- | --- | --- | --- |
| `image` | `H,W,C` | `C,H,W` | Multi-channel images become channels-first. |
| `image` | `H,W` | `1,H,W` | Single-channel images get a channel axis. |
| `images` | `N,H,W,C` | `N,C,H,W` | Batched image arrays are transposed as a single tensor. |
| `mask` | `H,W` | `H,W` | Mask shape is preserved. |
| `mask` | `H,W,C` | `H,W,C` by default | Set `transpose_mask=True` for `C,H,W`. |
| `masks` | list of `H,W` arrays | list of tensors | List input stays a list. |
| `masks` | `N,H,W` | `N,H,W` | Stacked masks stay stacked. |
| `masks` | `N,H,W,C` | `N,H,W,C` by default | With `transpose_mask=True`, becomes `N,C,H,W`. |

Validation checks after a fix:

```python
assert sample["image"].ndim == 3
assert sample["image"].shape[0] in {1, 3, 4}
assert sample["image"].dtype.is_floating_point  # when Normalize or ToFloat ran before ToTensorV2
```

If no normalization or float conversion ran first, `uint8` images remain `torch.uint8` after `ToTensorV2`.

## `ToTensor3D` Contract

`ToTensor3D(p=1.0)` is for 3D `volume` and `mask3d` targets.

| Input target | Input shape | Output shape | Notes |
| --- | --- | --- | --- |
| `volume` | `D,H,W,C` | `C,D,H,W` | Multi-channel volumes become channels-first. |
| `volume` | `D,H,W` | `1,D,H,W` | Single-channel volumes get `C=1`. |
| `mask3d` | `D,H,W,C` | `C,D,H,W` | 3D masks are also moved to channels-first. |
| `mask3d` | `D,H,W` | `1,D,H,W` | There is no `transpose_mask` option for 3D masks. |

Use `ToTensor3D` only with `volume=` and `mask3d=` keys. For 2D `image=` and `mask=` keys, use `ToTensorV2`.

## Normalize Before Tensor Conversion

`A.Normalize` should appear before `ToTensorV2` because it operates on NumPy arrays and controls scaling/range. Its default signature is equivalent to ImageNet-style standard normalization with `mean=(0.485, 0.456, 0.406)`, `std=(0.229, 0.224, 0.225)`, `max_pixel_value=255.0`, and `normalization="standard"`.

Common outcomes:

- `A.Normalize(...), ToTensorV2()` returns float tensor values already normalized.
- `ToTensorV2()` alone returns a tensor with the original dtype/range, commonly `torch.uint8` in `[0, 255]`.
- `A.ToFloat(max_value=255), ToTensorV2()` returns float values scaled to `[0, 1]` without mean/std normalization.

Do not normalize integer segmentation masks with image statistics. Masks should usually remain integer class labels, while images are normalized.

## Bboxes, Keypoints, and Labels

`ToTensorV2` targets images and masks. It does not convert bbox or keypoint lists into tensors. For object detection or pose datasets:

```python
transform = A.Compose(
    [A.Resize(512, 512), A.Normalize(), ToTensorV2()],
    bbox_params=A.BboxParams(format="pascal_voc", label_fields=["labels"]),
    keypoint_params=A.KeypointParams(format="xy"),
    strict=True,
)

result = transform(image=image, mask=mask, bboxes=bboxes, labels=labels, keypoints=keypoints)
image_tensor = result["image"]
bboxes_after_aug = result["bboxes"]
labels_after_aug = result["labels"]
```

Convert `bboxes`, `labels`, and `keypoints` to tensors in dataset code after Albumentations if the model API requires tensors. Keep label fields aligned with their corresponding boxes/keypoints.

## DataLoader Worker Reproducibility

Albumentations `Compose(seed=...)` uses its own random state. In a PyTorch `DataLoader` worker, Albumentations detects `torch.utils.data.get_worker_info()` and combines the base Compose seed with `torch.initial_seed()` so workers do not all replay the same random sequence. When a seeded `Compose` is unpickled in worker processes, it resets the worker-aware state.

Recommended pattern:

```python
transform = A.Compose([...], seed=137, strict=True)
loader = DataLoader(dataset, batch_size=8, num_workers=4, shuffle=True)
```

Use `Compose(seed=...)` when repeatable augmentation streams are needed. If additionally using NumPy or Python `random` inside custom dataset code outside Albumentations, seed those through the DataLoader's `worker_init_fn` or a PyTorch `Generator`; Albumentations does not control custom code randomness.

## Repair Checklist for Bad Tensor Shapes

1. Confirm image input is `H,W,C` or `H,W`, not already `C,H,W`.
2. Confirm `ToTensorV2` is last, after all NumPy transforms and `Normalize`/`ToFloat`.
3. Inspect masks separately: default masks stay `H,W` or `H,W,C`; use `transpose_mask=True` only for channel-first masks.
4. For batches, pass stacked `images` as `N,H,W,C`, not `N,C,H,W`.
5. For 3D, pass `volume`/`mask3d` as `D,H,W` or `D,H,W,C`, then expect `C,D,H,W`.
6. Convert bboxes/keypoints/labels after the Albumentations call, not by relying on `ToTensorV2`.
