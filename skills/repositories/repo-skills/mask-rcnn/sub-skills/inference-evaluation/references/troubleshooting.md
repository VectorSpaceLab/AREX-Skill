# Inference, Visualization, and Evaluation Troubleshooting

## `len(images) must be equal to BATCH_SIZE`

`detect()` expects exactly `config.BATCH_SIZE` images. For ordinary single-image inference, use an inference config with `GPU_COUNT = 1` and `IMAGES_PER_GPU = 1`.

## `After resizing, all images must have the same size`

All batched inference images must match after resizing. Use a consistent resize mode and avoid mixing unrelated image shapes in the same call.

## No detections or empty masks

Likely causes:

- Incorrect or mismatched `NUM_CLASSES`.
- Wrong checkpoint file.
- Input images not compatible with the training resize assumptions.
- Confidence threshold too high.

**Recovery:** Lower `DETECTION_MIN_CONFIDENCE`, confirm the checkpoint source, and inspect `mold_inputs()` output shapes. For custom datasets, verify the dataset layout and class map in [data-preparation](../../data-preparation/SKILL.md).

## Color splash output is grayscale everywhere

Likely causes: no instances survived thresholding, the mask array is empty, or the instance masks do not align with the image.

**Recovery:**

- Visualize raw detections with `display_instances()` first.
- Check that `masks.shape[-1] > 0`.
- Confirm the mask has the same image height and width as the source image.
- Verify that class ids and weights match the training dataset.

## COCO result conversion errors

**Symptoms:** pycocotools rejects the result file, or AP computation crashes.

**Likely causes:** `bbox` order is wrong, segmentation masks are not compressed/Fortran encoded correctly, or the image ids do not match the dataset.

**Recovery:** Convert boxes to `[x, y, width, height]`, use `np.asfortranarray(mask)` before `maskUtils.encode`, and verify `dataset.get_source_class_id(class_id, "coco")` when using the sample-style COCO converter.

## Nucleus RLE looks reversed or malformed

**Likely cause:** RLE was flattened in row-major order instead of column-major order.

**Recovery:** Use the bundled `scripts/rle_tools.py` and the reference implementation that transposes before flattening. Make sure the output line starts with the image id and uses one-based start positions.

## Evaluation needs `pycocotools` or dataset files that are absent

If the user only needs prediction routing or visualization guidance, keep the task in-memory and do not force a dataset download. If the task explicitly needs COCO evaluation, route back to data-preparation and ensure the dataset plus `pycocotools` are installed.
