# Data Keys, Target Shapes, Transform Matrices, and Inverse

Use this reference whenever a Kornia augmentation pipeline handles more than one
input, exposes transform matrices, or needs deterministic replay/inverse.

## Data-key order is an API contract

For positional calls, `data_keys` is not metadata; it is the contract that maps
each positional argument to a target type.

```python
aug = K.AugmentationSequential(
    K.RandomHorizontalFlip(p=1.0),
    data_keys=["input", "mask", "bbox_xyxy", "keypoints", "class"],
)
image_out, mask_out, boxes_out, keypoints_out, labels_out = aug(
    image, mask, boxes_xyxy, keypoints, labels
)
```

Rules:

- Number of positional inputs must equal number of data keys.
- Order must match exactly.
- The first key must be `"input"`/`"image"` when the pipeline samples params
  from an image.
- `"image"` and `"input"` are aliases. Prefer `"input"` for examples because
  many error messages use that term.
- `"class"` and `"label"` are aliases.
- Use `data_keys=None` only for dictionary input where keys are classified by
  prefix.

## Accepted target conventions

### Input/image

- Common shapes: `C,H,W` or `B,C,H,W`; prefer `B,C,H,W`.
- Dtype: floating point.
- Range: `[0, 1]` for image augmentations, especially color transforms.
- Coordinates for associated targets use pixel `(x, y)` order, where `x`
  indexes width and `y` indexes height.

### Mask

- Common shapes: `B,1,H,W` or `B,C,H,W`.
- Masks are internally converted to a floating dtype compatible with the image,
  then converted back after augmentation when possible.
- Default `AugmentationSequential` mask handling uses nearest interpolation
  semantics, which preserves labels better than bilinear interpolation.
- Keep mask spatial size aligned with the input image unless the selected
  augmentation intentionally changes size.

### Boxes

Supported data keys:

- `"bbox"`: explicit corner vertices, usually `B,N,4,2`.
- `"bbox_xyxy"`: `B,N,4` with `[x1, y1, x2, y2]`.
- `"bbox_xywh"`: `B,N,4` with `[x, y, width, height]`.

Rules:

- Use floating point box coordinates for geometric transforms.
- Batch dimension should align with the image batch.
- After crop/resize/perspective transforms, inspect boxes for clipping,
  invalid extents, or task-specific filtering needs.

### Keypoints

- Common shape: `B,N,2`.
- Coordinates are `(x, y)` pixel coordinates.
- Use floating point tensors for precision. Integer inputs may be converted for
  transformation and can lose fractional information.

### Class/label

- Data keys `"class"` and `"label"` are aliases.
- Values are passed through unchanged.
- Use class/label data keys only for targets that should not be spatially or
  photometrically transformed.

## Dictionary input

When constructing `AugmentationSequential` with `data_keys=None`, a single input
dictionary may be passed. Keys are classified by prefix; unknown keys are
preserved without augmentation.

```python
aug = K.AugmentationSequential(
    K.RandomHorizontalFlip(p=1.0),
    data_keys=None,
    keepdim=True,
)
out = aug({
    "image": image,
    "mask": mask,
    "bbox_xyxy": boxes_xyxy,
    "keypoints": keypoints,
    "sample_id": sample_id,  # passed through unchanged
})
```

Rules:

- Do not pass a dictionary to a pipeline that was constructed with explicit
  non-`None` `data_keys`.
- Prefer explicit positional `data_keys` for training loops where the target
  tuple shape is fixed.
- Use dictionary input when the batch object naturally carries named fields or
  optional fields.

## same_on_batch and p

`same_on_batch` controls whether a sampled transform is shared across the batch.
`p` controls whether each transform is applied.

- `same_on_batch=True`: every batch item receives identical sampled parameters.
- `same_on_batch=False`: each batch item samples independently.
- `same_on_batch=None` in a container: leave each child module's own setting.
- `p=1.0`: transform is always applied when selected.
- `p=0.0`: transform is never applied.
- Flip modules also expose `p_batch`; keep the default unless you intentionally
  want whole-batch on/off behavior separate from item-level `p`.

Testing pattern:

```python
aug = K.AugmentationSequential(
    K.RandomHorizontalFlip(p=1.0),
    data_keys=["input", "mask"],
    same_on_batch=True,
    keepdim=True,
)
```

## keepdim

`keepdim` controls whether the output keeps the same dimensionality convention
as the input.

- Use `keepdim=True` for most task code and tests.
- Use `keepdim=None` when you explicitly want child modules to keep their own
  default behavior.
- Be careful with single images (`C,H,W`): a transform may normalize internally
  to batch form unless `keepdim=True` preserves rank.

## random_apply

`random_apply` controls which child modules run.

- `False`: run all children in the original order.
- `True`: run all children in random order.
- `int`: choose exactly that many children.
- `(min_count, max_count)`: choose a random count within the range.
- `random_apply_weights`: optional weights for child selection.

For a clean one-of pipeline, set child transform `p=1.0` and set
`random_apply=1` on the container.

## Transform matrix modes

`AugmentationSequential(..., transformation_matrix_mode=...)` controls the
container-level `.transform_matrix` state.

- `"silent"` (default): collect a chained matrix where applicable; treat modules
  without rigid matrices as identity for matrix accounting.
- `"rigid"`: collect a chained matrix, but raise if a module cannot provide a
  valid rigid/affine matrix.
- `"skip"`: skip container matrix collection.

Expected matrix shapes:

- 2D geometric pipeline: `(B, 3, 3)`.
- 3D geometric pipeline: `(B, 4, 4)`.
- Pure intensity pipeline or skipped matrix mode: matrix may be `None`.

Use `"rigid"` while debugging image/mask/box/keypoint synchronization. Use
`"silent"` in mixed pipelines where intensity modules should not break matrix
collection. Use `"skip"` when matrices are not needed and state collection must
be avoided.

## Deterministic replay

A forward pass stores sampled params on the module in eager mode. Replay the
same augmentation by passing those params back.

```python
image_out, mask_out = aug(image, mask)
params = aug._params
image_replay, mask_replay = aug(image, mask, params=params)
```

Rules:

- Use the params immediately and on compatible inputs.
- Do not treat cached params as a portable file format.
- Passing explicit params is required when no input/image key is present.
- In export capture, per-call state such as cached params may be skipped.

## Inverse

`AugmentationSequential.inverse` applies inverse transforms using cached or
supplied params.

```python
image_out, mask_out = aug(image, mask)
image_back, mask_back = aug.inverse(image_out, mask_out)
```

Rules:

- A previous forward or explicit `params=` is required.
- Inverse uses the same `data_keys` unless you pass an override.
- Rigid geometric transforms are the best candidates for inverse.
- Cropping, resizing, interpolation, padding, erasing, noise, and color edits can
  discard information and therefore cannot be perfectly inverted.
- If exact low-level warp matrices or matrix direction conventions are the main
  task, route to [geometry-vision](../../geometry-vision/SKILL.md).

## Export and compile notes

- Deterministic image-only preprocessing is the safest export target.
- Random augmentation and multi-target propagation should be treated as eager
  training/data-pipeline behavior unless the target export format has a focused
  passing smoke.
- Export capture may omit per-call eager state: `._params` and
  `.transform_matrix` are diagnostic/runtime state, not guaranteed exported
  outputs.
- Optional ONNX-related dependencies may be absent; do not require them for
  basic augmentation work.
