# Composition API Reference

Albumentations 2.0.8 composes transforms with `albumentations.Compose` and related composition blocks. Use `import albumentations as A` in examples.

## Constructor Signatures

- `A.Compose(transforms, bbox_params=None, keypoint_params=None, additional_targets=None, p=1.0, is_check_shapes=True, strict=False, mask_interpolation=None, seed=None, save_applied_params=False)`
- `A.ReplayCompose(transforms, bbox_params=None, keypoint_params=None, additional_targets=None, p=1.0, is_check_shapes=True, save_key="replay")`
- `A.OneOf(transforms, p=0.5)`
- `A.SomeOf(transforms, n=1, replace=False, p=1)`
- `A.RandomOrder(transforms, n=1, replace=False, p=1)`
- `A.Sequential(transforms, p=0.5)`
- `A.OneOrOther(first=None, second=None, transforms=None, p=0.5)`
- `A.SelectiveChannelTransform(transforms, channels=(0, 1, 2), p=1.0)`

`transforms` should be a sequence. Passing a single transform is accepted by wrapping it into a list, but Albumentations emits a warning because a sequence is expected.

## Compose Options

| Option | Use | Notes |
| --- | --- | --- |
| `transforms` | Ordered transforms or nested composition blocks. | Top-level `Compose` runs transforms sequentially when `p` passes. |
| `p` | Probability that the whole compose block runs. | If `p=0` and `save_applied_params=True`, the result contains an empty `applied_transforms` list. |
| `strict=True` | Development-time validation. | Validates input keys against available keys and raises if any transform has invalid constructor arguments. |
| `is_check_shapes=True` | Shape consistency guard. | Checks H/W for image, mask, masks, images, and related targets; checks D/H/W for volume-style targets. |
| `additional_targets` | Apply target semantics to custom keys. | Example: `{"depth": "mask"}` treats `depth` like a mask, preserving geometry and mask interpolation behavior. |
| `bbox_params`, `keypoint_params` | Enable bbox/keypoint processors. | See `../targets-and-formats/` for format details and label-field contracts. |
| `mask_interpolation` | Override mask interpolation in nested transforms. | If not `None`, it is recursively propagated to transforms and nested compose blocks that expose `mask_interpolation`. |
| `seed` | Reproducible internal random state. | Independent from `np.random.seed()` and `random.seed()`. Two equivalent `Compose` instances with the same seed produce identical sequences. |
| `save_applied_params` | Inspect applied transform names and parameters. | Adds `applied_transforms` only on the top-level `Compose` when requested. |

Call pipelines with named data only:

```python
result = pipeline(image=image, mask=mask)
```

Positional calls raise a key error instructing the caller to use named arguments.

## Composition Blocks

### `OneOf`

`OneOf` selects one transform when the block probability passes. Child transform probabilities are normalized and used as selection weights; the selected child is called with `force_apply=True`.

```python
choice = A.OneOf([
    A.HorizontalFlip(p=1),
    A.VerticalFlip(p=2),
], p=0.75)
```

### `SomeOf`

`SomeOf` uniformly selects exactly `n` transform indices when its own `p` passes. If `replace=False` and `n` exceeds the pool size, `n` is capped to the number of transforms with a warning. Selected transforms still honor their individual `p` values and run in sorted index order.

```python
block = A.SomeOf([
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.8),
    A.RandomRotate90(p=1),
], n=2, replace=False, p=1)
```

### `RandomOrder`

`RandomOrder` has the same selection contract as `SomeOf`, but does not sort selected indices, so application order is random.

```python
block = A.RandomOrder([A.Blur(p=1), A.CLAHE(p=1), A.ToGray(p=1)], n=2, p=1)
```

### `Sequential`

`Sequential` runs all child transforms in order when its own `p` passes. Use it inside a `Compose`, `OneOf`, or `OneOrOther` block when one branch needs multiple ordered steps; it is not a replacement for the top-level `Compose` because processors and strict top-level validation belong on `Compose`.

```python
pipeline = A.Compose([
    A.OneOf([
        A.Sequential([A.HorizontalFlip(p=1), A.Rotate(limit=10, p=1)], p=1),
        A.Sequential([A.VerticalFlip(p=1), A.Blur(p=1)], p=1),
    ], p=1),
])
```

### `OneOrOther`

`OneOrOther` applies the first transform when its random draw is below `p`; otherwise it applies the last transform. Provide `first` and `second`, or provide `transforms`. If neither complete pair nor `transforms` is supplied, it raises `ValueError`. A `transforms` sequence whose length is not 2 emits a warning.

```python
block = A.OneOrOther(
    first=A.HorizontalFlip(p=1),
    second=A.VerticalFlip(p=1),
    p=0.5,
)
```

### `SelectiveChannelTransform`

`SelectiveChannelTransform` extracts selected channels from `data["image"]`, applies its child transforms to that sub-image, then writes transformed channels back into a contiguous copy of the original image.

```python
rgb_only = A.SelectiveChannelTransform(
    [A.RandomBrightnessContrast(p=1)],
    channels=[0, 1, 2],
    p=1,
)
```

Use it for channel-specific image transforms, not for masks, bboxes, or keypoints.

## Shape And Key Validation

With `is_check_shapes=True`, `Compose` checks that image/mask-like targets have consistent height and width. Volume-like targets also need consistent depth, height, and width. Disable shape checks only when the transform list is intentionally safe for differently-sized targets:

```python
pipeline = A.Compose([A.NoOp()], is_check_shapes=False)
```

With `strict=True`, `Compose` validates input keys. Unknown keys raise `ValueError`, while standard `mask` and `masks` keys are accepted even when transforms primarily expose `image`. To accept custom keys under strict mode, declare them in `additional_targets`:

```python
pipeline = A.Compose(
    [A.HorizontalFlip(p=1)],
    additional_targets={"right_image": "image", "depth": "mask"},
    strict=True,
)
result = pipeline(image=left, right_image=right, depth=depth)
```

When bbox or keypoint data is present, provide `bbox_params` or `keypoint_params` before using those targets. Missing processors raise errors such as `bbox_params must be specified for bbox transformations` or `keypoints_params must be specified for keypoint transformations`. Label-field format and filtering are owned by `../targets-and-formats/`.

## Additional Targets And Mask Interpolation

Use `additional_targets` to map custom data names to existing target types:

```python
pipeline = A.Compose(
    [A.Resize(128, 128, p=1), A.Rotate(limit=15, p=1)],
    additional_targets={"depth": "mask"},
    mask_interpolation=0,  # cv2.INTER_NEAREST
    strict=True,
)
result = pipeline(image=image, mask=mask, depth=depth)
```

Mapping `depth` to `mask` makes geometric transforms apply the same sampled geometry to `image`, `mask`, and `depth`, while using mask interpolation for mask-like targets. If the top-level `mask_interpolation` is set, Albumentations recursively overrides child transform `mask_interpolation` values, including nested `Compose`, `OneOf`, `SomeOf`, and `Sequential` blocks.

Do not reuse an existing additional target name with a different target type. Calling `add_targets({"image2": "mask"})` after `image2` was registered as `image` raises a value error.

## Seed Behavior

`Compose(seed=...)` creates an internal NumPy generator and Python `random.Random` instance and propagates the state to child transforms. It does not use global `np.random.seed()` or global `random.seed()`.

Useful rules:

- Two equivalent `Compose` instances created with the same `seed` produce identical augmentation sequences.
- Repeated calls on the same seeded instance advance its internal state, so each call can differ while the sequence is reproducible.
- `pipeline.set_random_seed(seed)` resets the sequence and propagates the seed to child transforms.
- In PyTorch `DataLoader` worker context, Albumentations combines the base seed with `torch.initial_seed()` modulo `2**32` so workers can get distinct effective seeds.
- `seed=None` creates a fresh internal random state per compose instance.

Example for reproducible comparisons:

```python
p1 = A.Compose([A.HorizontalFlip(p=0.5), A.Rotate(limit=15, p=0.5)], seed=137)
p2 = A.Compose([A.HorizontalFlip(p=0.5), A.Rotate(limit=15, p=0.5)], seed=137)
assert (p1(image=image)["image"] == p2(image=image)["image"]).all()
```

If a user expects `np.random.seed(137)` to control the pipeline, switch to `A.Compose(..., seed=137)` or call `set_random_seed(137)` on the pipeline.

## Applied Parameter Inspection

`save_applied_params=True` adds an `applied_transforms` list to the output of the top-level `Compose`:

```python
pipeline = A.Compose(
    [A.HorizontalFlip(p=1), A.Blur(p=1)],
    save_applied_params=True,
    strict=True,
)
result = pipeline(image=image)
print(result["applied_transforms"])
# [("HorizontalFlip", {...}), ("Blur", {...})]
```

Transforms that do not run because their own `p` fails are not listed. Nested choices list only the transforms that actually applied. For exact replay across inputs, use `ReplayCompose` and route details to `../serialization-and-reproducibility/`.

## Pipeline Operator Edits

All composition classes inherit immutable operator edits from `BaseCompose`:

| Expression | Effect |
| --- | --- |
| `compose + transform` | Appends one `BasicTransform`. |
| `compose + [transform_a, transform_b]` | Appends multiple `BasicTransform` instances. |
| `transform + compose` | Prepends one `BasicTransform`. |
| `[transform_a, transform_b] + compose` | Prepends multiple `BasicTransform` instances. |
| `compose - A.HorizontalFlip` | Removes the first transform whose exact class is `A.HorizontalFlip`. |

Operators return a new compose instance and do not mutate the original. They preserve constructor settings such as `bbox_params`, `keypoint_params`, `additional_targets`, `p`, `strict`, `is_check_shapes`, `mask_interpolation`, `seed`, `save_applied_params`, and subclass options like `SomeOf.n`, `SomeOf.replace`, and `SelectiveChannelTransform.channels`.

Important validation details:

- `+` and left-`+` accept only `BasicTransform` instances or sequences of `BasicTransform` instances. Nested `Compose`, `Sequential`, or other `BaseCompose` operands are rejected by the operator path.
- `-` accepts a transform class, not an instance. Use `compose - A.HorizontalFlip`, not `compose - A.HorizontalFlip()`.
- `-` removes only the first exact class match. If no match exists, it raises `ValueError`.
- For `SomeOf`, adding transforms increases the candidate pool but preserves `n`; it does not increase the number selected.

When you need to add a nested composition block, rebuild the transform list explicitly instead of using `+`:

```python
pipeline = A.Compose([*pipeline.transforms, A.Sequential([A.Blur(p=1), A.CLAHE(p=1)], p=1)])
```
