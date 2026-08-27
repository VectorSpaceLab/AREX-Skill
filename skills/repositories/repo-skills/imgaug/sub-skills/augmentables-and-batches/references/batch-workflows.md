# Batch workflows

## Read this when

The task uses `Batch`/`UnnormalizedBatch`, mixed augmentable columns, or feeds a loader into background augmentation.

## Batch types

`UnnormalizedBatch` accepts flexible arrays, lists, tuples, coordinate objects, dense maps, and an optional `data` payload. Its `to_normalized_batch()` method converts those inputs to normalized `Batch` columns. After augmentation, `fill_from_augmented_normalized_batch_()` restores output forms compatible with the original unnormalized inputs.

`Batch` stores normalized columns for images, heatmaps, segmentation maps, keypoints, bounding boxes, polygons, line strings, and `data`. It is the natural handoff to `Augmenter.augment_batch()` or `imgaug.multicore.Pool`.

## Verified constructors/methods

- `UnnormalizedBatch(images=None, heatmaps=None, segmentation_maps=None, keypoints=None, bounding_boxes=None, polygons=None, line_strings=None, data=None)`
- `Batch(images=None, heatmaps=None, segmentation_maps=None, keypoints=None, bounding_boxes=None, polygons=None, line_strings=None, data=None)`
- `UnnormalizedBatch.to_normalized_batch()`
- `Batch.to_normalized_batch()`
- `Augmenter.augment_batch(batch, hooks=None)`
- `Augmenter.augment_batches(batches, hooks=None, background=False)`

## Example

```python
import numpy as np
import imgaug as ia
import imgaug.augmenters as iaa
from imgaug.augmentables.batches import UnnormalizedBatch

images = np.zeros((2, 32, 32, 3), dtype=np.uint8)
batches = [UnnormalizedBatch(
    images=images,
    keypoints=[
        [ia.Keypoint(x=4, y=4)],
        [ia.Keypoint(x=8, y=8)],
    ],
    data={"source": "tiny-fixture"},
)]
seq = iaa.Sequential([iaa.Fliplr(1.0)])
for batch in seq.augment_batches(batches):
    assert batch.images_aug is not None
    assert batch.data["source"] == "tiny-fixture"
```

## Batch invariants

- All non-empty augmentable columns in a batch must correspond to the same number of images.
- `data` is not transformed; use it to carry IDs or file metadata through asynchronous processing.
- Normalize before augmentation and restore after augmentation; do not reuse a partially augmented `UnnormalizedBatch` as if it were new input.
- When the task uses background processing, read [`../../multicore-and-diagnostics/SKILL.md`](../../multicore-and-diagnostics/SKILL.md) for queue, worker, and pickling behavior.
