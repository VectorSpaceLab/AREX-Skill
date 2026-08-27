# DataPipeline Data Formats

`Augmentor.DataPipeline(images, labels=None)` is the in-memory API for original-plus-mask groups. It does not read images from disk and does not write augmented images to disk. Inputs are arrays supplied during construction; outputs are arrays returned by `sample()` or yielded by `generator()`.

## Input structure

Use a list of groups. Each group is a list or tuple of arrays that must be transformed together.

```python
images = [
    [image0_rgb, image0_mask],
    [image1_rgb, image1_mask],
]
labels = [0, 1]

p = Augmentor.DataPipeline(images, labels)
```

For multiple masks, add more arrays to the group:

```python
images = [
    [image0_rgb, image0_instance_mask, image0_boundary_mask],
    [image1_rgb, image1_instance_mask, image1_boundary_mask],
]
labels = ["tumor", "normal"]
p = Augmentor.DataPipeline(images, labels)
```

Important constraints:

- Each top-level element is one sample group.
- Each sample group must itself be a list/tuple of arrays. A bare list of image arrays with no mask grouping is a known unsupported/skipped behavior in the package tests.
- Arrays are converted through `PIL.Image.fromarray()`, so use Pillow-compatible dtypes and shapes.
- Groups may mix channel counts, for example an RGB original `(H, W, 3)` and a monochrome mask `(H, W)`.
- Use matching spatial sizes inside a group unless you have verified that the selected operation supports the mismatch. Most mask-safe workflows should start with equal height and width.
- If labels are supplied, use a sequence with the same length as the number of groups.

## Adding operations

`DataPipeline` inherits the same operation-adding methods as `Pipeline`:

```python
p.rotate(probability=1, max_left_rotation=5, max_right_rotation=5)
p.zoom_random(probability=0.5, percentage_area=0.8)
```

Every selected operation receives the full group and returns the transformed group. This is what keeps the original and all masks aligned.

Mask note: color/intensity operations can modify mask pixel values. Prefer geometric operations for categorical segmentation masks.

## `sample(n)` return shape

With labels:

```python
batch, y = p.sample(4)
```

- `batch` is a Python list of length `4`.
- Each `batch[i]` is a list of arrays with the same group length as the selected input sample, for example `[augmented_image, augmented_mask]`.
- `y` is a list of length `4` containing the label selected with each sampled group.

Without labels:

```python
batch = p.sample(4)
```

- `batch` is a list of length `4`.
- Each `batch[i]` is still a grouped list of arrays.

The method samples input groups randomly with replacement, so labels in the returned batch reflect whichever groups were chosen.

## `generator(batch_size=1)` return shape

`generator()` yields forever. A `batch_size` below `1` is treated as `1`.

With labels:

```python
gen = p.generator(batch_size=8)
batch, y = next(gen)
```

Without labels:

```python
gen = p.generator(batch_size=8)
batch = next(gen)
```

The nested batch structure is the same as `sample()`: list of sampled groups, with each group containing one original and its masks after identical operations.

## Minimal validation helper

Before using `DataPipeline`, validate nested shapes explicitly:

```python
def validate_groups(groups, labels=None):
    assert groups, "need at least one image/mask group"
    if labels is not None:
        assert len(labels) == len(groups), "labels must match group count"
    for idx, group in enumerate(groups):
        assert isinstance(group, (list, tuple)), f"group {idx} is not a list/tuple"
        assert len(group) >= 2, f"group {idx} has no mask companion"
        h, w = group[0].shape[:2]
        for arr in group[1:]:
            assert arr.shape[:2] == (h, w), f"group {idx} has mismatched mask dimensions"
```

Run the bundled [array smoke helper](../scripts/augmentor_mask_array_smoke.py) for a tiny known-good original+mask pattern.
