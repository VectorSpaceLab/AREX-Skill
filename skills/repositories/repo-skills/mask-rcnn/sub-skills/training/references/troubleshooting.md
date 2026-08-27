# Training Troubleshooting

## `ValueError` or HDF5 shape mismatch when loading weights

**Likely cause:** The checkpoint was trained with a different number of classes, backbone, or layer naming scheme.

**Recovery:** Use `by_name=True` and exclude the final class/mask heads when transferring from COCO to a custom dataset with a different `NUM_CLASSES`. If the checkpoint still mismatches, verify that the config matches the weights source and that the file is actually a Mask_RCNN `.h5` checkpoint.

## `Could not find model directory` from `find_last()`

**Likely cause:** No experiment subdirectory exists under `model_dir`, or the directory name does not begin with the config `NAME`.

**Recovery:** Train once to create the directory, or point `model_dir` at the parent logs directory used for the current config name.

## Training is extremely slow

**Likely cause:** Mask R-CNN is heavy; CPU-only runs are not practical for long training. Large images and large batches increase cost quickly.

**Recovery:**

- Lower `IMAGES_PER_GPU`.
- Start with `layers="heads"`.
- Use a smaller image size for smoke tests.
- Confirm GPU/CUDA compatibility before claiming practical training support.

## Out-of-memory errors

**Likely cause:** Batch size or image dimensions are too large for the available GPU memory.

**Recovery:** Reduce `IMAGES_PER_GPU` first, then reduce `IMAGE_MIN_DIM`/`IMAGE_MAX_DIM` or use a smaller backbone. For very small datasets, training heads only is a sensible first pass.

## BatchNorm behaves poorly

**Likely cause:** Small batches and frozen or moving batch statistics can be unstable.

**Recovery:** Leave `TRAIN_BN = False` for the usual small-batch workflow unless you have strong evidence that updating BN helps on your data.

## Augmentation breaks masks

**Symptoms:** Image and mask shape mismatch after augmentation, or masks no longer align with objects.

**Recovery:** Use mask-safe imgaug augmenters only, and test the augmentation on a tiny fixture first. The `load_image_gt()` path asserts that shapes do not change unexpectedly.

## Custom dataset appears to train but loss never improves

**Likely causes:**

- `NUM_CLASSES` is wrong.
- Masks are empty or mislabeled.
- `prepare()` was skipped.
- Class ids in `load_mask()` do not match classes added via `add_class()`.

**Recovery:** Validate the dataset layout and inspect a few masks/boxes before training. Use the data-preparation helper scripts and a tiny fixture to catch these mistakes early.

## Multi-GPU path is unstable

**Likely cause:** `mrcnn.parallel_model.ParallelModel` is legacy TF1/Keras graph code and depends on an exact runtime stack.

**Recovery:** Verify the backend stack on the target host before relying on multi-GPU training. Do not claim multi-GPU support from CPU imports alone.
