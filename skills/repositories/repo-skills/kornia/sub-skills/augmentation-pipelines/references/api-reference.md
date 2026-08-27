# Augmentation Pipeline API Reference

This reference covers the Kornia 0.9.0rc1 augmentation APIs most often needed
for random/deterministic pipelines. Imports are from `kornia.augmentation` unless
noted otherwise.

## Package facts

- Python: >=3.11.
- Required runtime: PyTorch, numpy, packaging, and `kornia-rs`.
- Optional integrations such as ONNX helpers, transformers, diffusers, and ivy
  may be absent in a minimal runtime.
- Image inputs should be PyTorch tensors, usually `B,C,H,W`, floating point, and
  scaled to `[0, 1]`.

## DataKey import

`DataKey` is defined in `kornia.constants`, not exported from the top-level
augmentation namespace.

```python
from kornia.constants import DataKey
```

Accepted string data-key names in `AugmentationSequential` are:

- `"input"` or `"image"` for image tensors; these are aliases.
- `"mask"` for segmentation masks.
- `"bbox"` for boxes represented by four corner vertices.
- `"bbox_xyxy"` for `x1,y1,x2,y2` boxes.
- `"bbox_xywh"` for `x,y,width,height` boxes.
- `"keypoints"` for keypoint coordinates.
- `"class"` or `"label"` for class targets; these are aliases.

## Containers

### AugmentationSequential

Use `AugmentationSequential` for synchronized image/mask/box/keypoint/class
augmentation.

```python
K.AugmentationSequential(
    *args,
    data_keys=(DataKey.IMAGE,),
    same_on_batch=None,
    keepdim=None,
    random_apply=False,
    random_apply_weights=None,
    transformation_matrix_mode="silent",
    extra_args=None,
)
```

Operational details:

- `data_keys` may be strings, integer enum values, or `DataKey` values. Use
  strings in examples for clarity.
- The first key must be the image/input key when the pipeline needs to sample
  params from an image tensor.
- Positional input order must exactly match `data_keys`.
- Dictionary input is supported when the module is constructed with
  `data_keys=None`; dictionary keys are classified by their prefixes, such as
  `"image"`, `"mask"`, `"bbox_xyxy"`, or `"keypoints"`.
- `same_on_batch=None` and `keepdim=None` preserve each child module's own
  setting. Passing `True` or `False` overrides child modules.
- `random_apply=False` applies all children in original order. `True` applies
  all children in a random order. An integer applies exactly that many randomly
  selected children. A tuple selects a random count within the tuple bounds.
- `random_apply_weights` weights the child selection used by `random_apply`.
- `transformation_matrix_mode="silent"` computes a chained matrix and treats
  non-rigid modules as identity for matrix accounting. `"rigid"` raises when a
  non-rigid module prevents a valid rigid matrix. `"skip"` disables chained
  matrix collection.
- Default mask handling uses nearest interpolation semantics.

### ImageSequential

Use `ImageSequential` when all inputs are image tensors and no mask/box/keypoint
propagation is required.

```python
K.ImageSequential(
    *args,
    same_on_batch=None,
    keepdim=None,
    random_apply=False,
    random_apply_weights=None,
    if_unsupported_ops="raise",
    disable_item_features=True,
    disable_sequential_features=False,
)
```

Operational details:

- It behaves like a Kornia-aware `nn.Sequential` for images.
- It can be nested inside `AugmentationSequential`, but multi-target semantics
  still belong to the outer `AugmentationSequential`.
- Choose this for image-only preprocessing or color/geometric chains.

### PatchSequential

Use `PatchSequential` to apply transforms on a patch grid.

```python
K.PatchSequential(
    *args,
    grid_size=(4, 4),
    padding="same",
    same_on_batch=None,
    keepdim=None,
    patchwise_apply=True,
    random_apply=False,
    random_apply_weights=None,
)
```

Operational details:

- `grid_size` is `(rows, columns)`.
- `padding="same"` keeps the full spatial extent by padding to the patch grid.
- `patchwise_apply=True` samples/applies by patch; set `False` when each image
  should receive the same patch pipeline across all patches.
- Avoid geometric `PatchSequential` inside multi-target pipelines when masks,
  boxes, or keypoints must stay perfectly synchronized; use image-only patch
  augmentation or verify the exact case with a smoke.

### VideoSequential

Use `VideoSequential` for time-aware augmentation over video tensors.

```python
K.VideoSequential(
    *args,
    data_format="BTCHW",
    same_on_frame=True,
    random_apply=False,
    random_apply_weights=None,
)
```

Operational details:

- `data_format="BTCHW"` means batch, time, channels, height, width.
- `same_on_frame=True` applies the same sampled transform across frames in a
  clip, preserving temporal coherence.
- It can be nested in `AugmentationSequential` for video image/mask/box/keypoint
  propagation.

## Representative transform constructors

### RandomAffine

```python
K.RandomAffine(
    degrees,
    translate=None,
    scale=None,
    shear=None,
    resample="BILINEAR",
    same_on_batch=False,
    align_corners=False,
    padding_mode="ZEROS",
    fill_value=None,
    p=0.5,
    keepdim=False,
)
```

Use for random rotation, translation, scale, and shear. For deterministic tests,
use `p=1.0` and fixed or degenerate ranges such as `degrees=0.0` or
`scale=(1.0, 1.0)`.

### RandomPerspective

```python
K.RandomPerspective(
    distortion_scale=0.5,
    resample="BILINEAR",
    same_on_batch=False,
    align_corners=False,
    p=0.5,
    keepdim=False,
    sampling_method="basic",
)
```

Use for random quadrilateral perspective warps. Treat it as geometric: masks,
boxes, and keypoints require `AugmentationSequential` with matching `data_keys`.

### RandomResizedCrop

```python
K.RandomResizedCrop(
    size,
    scale=(0.08, 1.0),
    ratio=(0.75, 1.3333333333333333),
    resample="BILINEAR",
    same_on_batch=False,
    align_corners=True,
    p=1.0,
    keepdim=False,
    cropping_mode="slice",
)
```

Use for random crop plus resize to `size=(height, width)`. Because this changes
spatial size, verify masks/boxes/keypoints and downstream shape expectations.

### ColorJiggle

```python
K.ColorJiggle(
    brightness=0.0,
    contrast=0.0,
    saturation=0.0,
    hue=0.0,
    same_on_batch=False,
    p=1.0,
    keepdim=False,
)
```

Use for image-only color perturbation. It does not spatially transform masks,
boxes, or keypoints. Keep inputs float in `[0, 1]`.

### RandomHorizontalFlip and RandomVerticalFlip

```python
K.RandomHorizontalFlip(p=0.5, p_batch=1.0, same_on_batch=False, keepdim=False)
K.RandomVerticalFlip(p=0.5, p_batch=1.0, same_on_batch=False, keepdim=False)
```

Use `p=1.0` for deterministic flips. They are good smoke-test transforms
because image and mask outputs can be compared with `torch.flip`.

## State, params, matrices, and inverse

- After an eager forward pass, augmentation modules keep sampled params as
  per-call state. In examples, immediate deterministic replay is commonly done
  with `params=aug._params`.
- `aug.transform_matrix` is populated after a forward when matrix collection is
  enabled and applicable. For 2D geometric pipelines, expect shape `(B, 3, 3)`.
  For 3D geometric augmentation, expect shape `(B, 4, 4)`.
- `aug.inverse(*outputs)` applies inverse transforms using cached params when
  available. You can also pass explicit `params=`.
- `inverse` can recover geometric placement but not information destroyed by
  cropping, padding, interpolation, erase/noise, or image-only intensity edits.
- Export capture may skip per-call state such as `._params` and
  `.transform_matrix`. Prefer deterministic single-input preprocessing for
  export and verify exported outputs against eager outputs.
