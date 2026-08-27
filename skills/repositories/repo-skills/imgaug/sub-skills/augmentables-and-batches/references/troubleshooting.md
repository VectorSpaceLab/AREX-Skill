# Augmentables troubleshooting

## Annotation count mismatch

**Symptom:** normalization or augmentation raises an assertion about the number of images and annotation groups.

**Recovery:** ensure every non-empty annotation input has one group per image. For a single image, use a single group rather than an extra batch dimension that changes interpretation.

## Missing or wrong shape metadata

**Symptom:** projection, drawing, or dense-map alignment is wrong.

**Recovery:** construct `...OnImage` objects with the original image shape, including the channel dimension when present. Use `.on(image)` when converting a shape-aware object to a new image.

## Out-of-image boxes or points

**Symptom:** boxes disappear, drawing raises, or polygons become invalid after a crop/warp.

**Recovery:** decide explicitly whether to keep, clip, or remove them. Use `BoundingBoxesOnImage.clip_out_of_image()`, polygon/line clipping, or pipeline helpers such as `ClipCBAsToImagePlanes` and `RemoveCBAsByOutOfImageFraction`.

## Heatmap/segmentation interpolation confusion

**Symptom:** class IDs become fractional or continuous heatmaps show blocky nearest-neighbor artifacts.

**Recovery:** use heatmaps for continuous values and segmentation maps for categorical values. Keep the default heatmap cubic and segmentation nearest-neighbor resize semantics unless the task has a documented alternative.

## Coordinate convention confusion

**Symptom:** landmarks are shifted by half a pixel.

**Recovery:** remember that imgaug coordinates are subpixel-accurate; `(0.5, 0.5)` is the center of the top-left pixel.

## Mixed batch output is hard to interpret

**Symptom:** `images_aug` or annotation output has an unexpected Python list/array/object form.

**Recovery:** use `UnnormalizedBatch.to_normalized_batch()` to inspect normalized columns and let `fill_from_augmented_normalized_batch_()` restore the original style. Preserve `Batch.data` IDs for asynchronous workflows.
