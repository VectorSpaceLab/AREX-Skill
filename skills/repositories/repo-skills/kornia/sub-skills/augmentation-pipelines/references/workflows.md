# Augmentation Pipeline Workflows

These recipes are no-download and assume PyTorch tensors are already created on
the target device. Use `import kornia.augmentation as K`.

## 1. Synchronized image and mask flip

Use `AugmentationSequential` with matching positional input order and
`data_keys` order.

```python
import torch
import kornia.augmentation as K

image = torch.rand(2, 3, 64, 80, device=device, dtype=torch.float32)  # B,C,H,W in [0,1]
mask = (torch.rand(2, 1, 64, 80, device=device) > 0.5).to(torch.float32)

aug = K.AugmentationSequential(
    K.RandomHorizontalFlip(p=1.0),
    data_keys=["input", "mask"],
    same_on_batch=True,
    keepdim=True,
    transformation_matrix_mode="rigid",
)
image_out, mask_out = aug(image, mask)

assert image_out.shape == image.shape
assert mask_out.shape == mask.shape
assert aug.transform_matrix is not None and aug.transform_matrix.shape == (image.shape[0], 3, 3)
```

Checklist:

- Make both image and mask batched tensors.
- Keep the image float in `[0, 1]`; masks may be binary/label tensors but are
  internally processed with nearest interpolation semantics.
- Use `keepdim=True` in tests to avoid rank surprises.

## 2. Reuse sampled random params deterministically

Run once, then pass cached params to replay the same sampled transform on the
same or aligned targets.

```python
aug = K.AugmentationSequential(
    K.RandomAffine(degrees=15.0, translate=(0.05, 0.05), p=1.0),
    K.ColorJiggle(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.02, p=1.0),
    data_keys=["input", "mask"],
    keepdim=True,
)
image_a, mask_a = aug(image, mask)
params = aug._params  # eager per-call state; use immediately, not as a long-term file format
image_b, mask_b = aug(image, mask, params=params)

torch.testing.assert_close(image_a, image_b)
torch.testing.assert_close(mask_a, mask_b)
```

Checklist:

- Replay params only across inputs with compatible batch and spatial shape.
- Do not rely on `._params` after another forward pass unless you intentionally
  want the newest call's params.
- For reproducible tests, also seed PyTorch when using non-degenerate random
  ranges.

## 3. Use one-of or random subchains

Use `random_apply=1` for one-of behavior. Add weights when some transforms
should be sampled more often.

```python
aug = K.AugmentationSequential(
    K.RandomHorizontalFlip(p=1.0),
    K.RandomVerticalFlip(p=1.0),
    K.RandomAffine(degrees=10.0, p=1.0),
    data_keys=["input", "mask"],
    random_apply=1,
    random_apply_weights=[0.4, 0.4, 0.2],
    keepdim=True,
)
image_out, mask_out = aug(image, mask)
```

Checklist:

- `random_apply=False`: all children in original order.
- `random_apply=True`: all children in random order.
- `random_apply=2`: exactly two selected children.
- `random_apply=(1, 3)`: a random count between one and three selected
  children.
- Keep child `p=1.0` when `random_apply` owns the stochastic choice.

## 4. Transform boxes and keypoints with images

Use the correct data-key shape convention for each target.

```python
image = torch.rand(2, 3, 32, 48, device=device)
mask = torch.zeros(2, 1, 32, 48, device=device)
boxes_xyxy = torch.tensor(
    [[[4.0, 5.0, 20.0, 24.0]], [[8.0, 6.0, 30.0, 28.0]]],
    device=device,
)
keypoints = torch.tensor(
    [[[10.0, 12.0], [18.0, 20.0]], [[12.0, 14.0], [24.0, 22.0]]],
    device=device,
)

aug = K.AugmentationSequential(
    K.RandomHorizontalFlip(p=1.0),
    data_keys=["input", "mask", "bbox_xyxy", "keypoints"],
    keepdim=True,
    transformation_matrix_mode="rigid",
)
image_out, mask_out, boxes_out, keypoints_out = aug(image, mask, boxes_xyxy, keypoints)

assert boxes_out.shape == boxes_xyxy.shape
assert keypoints_out.shape == keypoints.shape
```

Checklist:

- Box coordinates and keypoints are in pixel `(x, y)` order.
- `bbox_xyxy` expects `x1,y1,x2,y2`; `bbox_xywh` expects `x,y,width,height`;
  `bbox` expects explicit corner vertices.
- Use float coordinate tensors. Integer keypoints/boxes may be converted for
  geometric computation and can lose precision.

## 5. Preserve class labels while augmenting inputs

Class/label targets are routed through unchanged.

```python
labels = torch.tensor([3, 7], device=device)
aug = K.AugmentationSequential(
    K.RandomResizedCrop(size=(32, 32), scale=(0.8, 1.0), p=1.0),
    data_keys=["input", "class"],
    keepdim=True,
)
image_out, labels_out = aug(image, labels)
assert labels_out is labels or torch.equal(labels_out, labels)
```

Checklist:

- Use `"class"` or `"label"`; both target the same class/label data key.
- Class labels are not spatially transformed.

## 6. Invert a geometric augmentation

Use inverse for approximate geometric recovery or to map targets back to the
input frame.

```python
aug = K.AugmentationSequential(
    K.RandomAffine(degrees=0.0, translate=(0.1, 0.0), p=1.0),
    data_keys=["input", "mask"],
    keepdim=True,
    transformation_matrix_mode="rigid",
)
image_out, mask_out = aug(image, mask)
image_back, mask_back = aug.inverse(image_out, mask_out)
```

Checklist:

- A prior forward pass or explicit `params=` is required before `inverse`.
- Interpolation, crop boundaries, padding, intensity edits, and erased/noisy
  regions are not perfectly invertible.
- Use `transformation_matrix_mode="rigid"` while debugging to fail fast on
  transforms that cannot produce a rigid matrix.

## 7. Image-only preprocessing pipeline

Use `ImageSequential` or single-input `AugmentationSequential` for deterministic
preprocessing suitable for model input code.

```python
tf = K.AugmentationSequential(
    K.Resize((224, 224)),
    K.CenterCrop((224, 224)),
    data_keys=["input"],
    keepdim=True,
)
out = tf(image)
```

Checklist:

- Deterministic transforms are better candidates for export than random
  multi-target training augmentations.
- Route low-level size, crop, and warp semantics to
  [geometry-vision](../../geometry-vision/SKILL.md) only if the task is primarily about warp math.

## 8. Patch-level image augmentation

Use `PatchSequential` for local patch perturbations when target propagation is
not required.

```python
patch_aug = K.PatchSequential(
    K.ColorJiggle(brightness=0.1, contrast=0.1, p=1.0),
    grid_size=(4, 4),
    padding="same",
    patchwise_apply=True,
    keepdim=True,
)
out = patch_aug(image)
```

Checklist:

- `grid_size` is rows then columns.
- Keep patch augmentation image-only unless a dedicated smoke proves your
  multi-target case.

## 9. Video augmentation with temporal coherence

Use `VideoSequential` when the input has a time dimension.

```python
video = torch.rand(2, 4, 3, 32, 48, device=device)  # B,T,C,H,W
video_aug = K.VideoSequential(
    K.RandomHorizontalFlip(p=1.0),
    data_format="BTCHW",
    same_on_frame=True,
)
out = video_aug(video)
assert out.shape == video.shape
```

Checklist:

- `same_on_frame=True` preserves a coherent transform across frames in a clip.
- If video masks, boxes, or keypoints are involved, wrap the video chain in an
  `AugmentationSequential` and run a targeted smoke.
