# Masks and Arrays Troubleshooting

## `ground_truth()` prints `0 ground truth image(s) found.`

Check the pairing rules before sampling:

- Filenames must match exactly, including extension and case.
- For class-subfolder pipelines, the ground-truth root must repeat the same class folder names.
- The pipeline must already have scanned originals before `ground_truth()` is called.
- Confirm matches with `get_ground_truth_paths()`; unmatched originals have `None` as the ground-truth path.

## Ground-truth images silently do not attach

Common causes:

- The mask file is in the wrong class subfolder.
- The original and mask dimensions differ.
- The image extension differs even though the stem is the same.
- Only some originals have masks; `get_ground_truth_paths()` will show mixed `path`/`None` pairs.

For segmentation workflows, preflight every pair for equal width and height before running a long `sample()` job.

## Original/mask output count is unexpected

With one ground-truth image per original, disk sampling usually writes one transformed original and one transformed ground-truth image for each generated sample. If the output count looks like originals only, check whether `ground_truth()` found any matches and whether `process_ground_truth_images` became enabled internally.

## `DataPipeline` crashes on input arrays

Use a nested group structure:

```python
images = [[image_array, mask_array]]          # good
images = [image_array0, image_array1]         # unsupported no-mask shape
```

The no-mask form is a known unsupported/skipped behavior in the package tests. For non-mask array generators, use the generator/framework sub-skill rather than `DataPipeline`.

Also confirm that each array can be converted by `PIL.Image.fromarray()`:

- RGB images usually use shape `(H, W, 3)` and dtype `uint8`.
- Monochrome masks usually use shape `(H, W)` and dtype `uint8`.
- Avoid unusual dtypes until you have tested a tiny sample.

## Labels are missing or not returned

`DataPipeline.sample()` and `DataPipeline.generator()` return labels only when `labels` was supplied during construction.

- With labels: `batch, labels = p.sample(n)`.
- Without labels: `batch = p.sample(n)`.

The labels sequence should have the same length as the top-level `images` group list. The returned labels are the labels for the randomly selected groups, so repeated labels are expected when sampling with replacement.

## Shapes change after augmentation

Some operations preserve size; others can change spatial dimensions or crop/resize content. Check the selected operation behavior before assuming a fixed shape. For mask-safe workflows:

- Use tiny samples and inspect `array.shape` for every group member.
- Prefer operations that preserve the original/mask alignment you need.
- If downstream model input must be fixed-size, include an explicit resize/crop strategy and verify the final shape.

## Mask class IDs are corrupted

Color, brightness, contrast, histogram, greyscale, and other intensity operations may alter mask pixel values. For categorical masks, keep the mask pipeline geometric-only unless you intentionally want to transform mask colors. If you need image-only color changes while preserving masks, split the workflow and apply image-only changes outside this grouped mask pipeline.

## Multiple masks per image are misaligned

All masks for one original must be in the same group:

```python
images = [[image, instance_mask, boundary_mask]]
```

Do not create separate top-level groups for masks that belong to the same original. Top-level groups are sampled independently; only arrays inside the same group receive identical random operation parameters.
