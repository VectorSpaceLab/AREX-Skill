# Data Preparation Troubleshooting

## Common failures

- **`DataGenerator` says no dataset is loaded**
  - Cause: the parser was never called, or the source lists were empty.
  - Fix: parse a CSV / XML / JSON source first, or point the generator at an HDF5 cache.

- **CSV parsing drops rows or reads the wrong box coordinates**
  - Cause: `input_format` does not match the CSV column order.
  - Fix: map the six required fields exactly and confirm that the class ID column is the one you expect.

- **VOC XML parsing misses objects**
  - Cause: the classes list, image-set files, or annotation directory do not match the split.
  - Fix: make sure `background` is the first class and that every split has a matching images directory, image-set file, and annotations directory.

- **COCO JSON parsing or export looks wrong**
  - Cause: category IDs are not consecutive in COCO and need remapping.
  - Fix: build the category maps with `get_coco_category_maps()` before export or evaluation.

- **`h5py` / XML / JSON / image parsing imports fail**
  - Cause: the optional parser dependencies are missing.
  - Fix: install the verified baseline packages from `references/compatibility.md`.

- **Boxes disappear after a transform**
  - Cause: the crop / box filter / image validator settings are too strict.
  - Fix: start with `Resize` or a gentler chain, then relax the overlap thresholds.

- **Empty batches appear unexpectedly**
  - Cause: all boxes were filtered out, or `keep_images_without_gt=False` removed images with no remaining ground truth.
  - Fix: inspect the labels after the transform chain and decide whether empty images should be preserved.

- **Prediction coordinates do not map back to the source image**
  - Cause: the inverse transforms were dropped.
  - Fix: keep `inverse_transform` outputs from the generator and pass them to `apply_inverse_transforms()` later.

## Fast recovery path

1. Re-run `scripts/check_env.py`.
2. Run `sub-skills/data-preparation/scripts/smoke.py`.
3. Reduce the problem to one tiny synthetic image and one bounding box.
4. Re-introduce the full dataset only after the parser and generator are stable.
