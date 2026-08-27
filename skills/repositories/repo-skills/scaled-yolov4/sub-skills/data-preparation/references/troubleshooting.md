# Data-preparation troubleshooting

## `Error loading data from ...`

Usually the split source points to the wrong place or the repo-relative path was resolved from the wrong directory.

Recovery:

- Resolve the YAML or text list from the repository root the same way the run will.
- Confirm the split source exists before you try to build a loader.
- Sample the first few lines of the text list and check that the referenced images exist.

## `No images found in ...`

The loader could not discover any image files in the source directory or list.

Recovery:

- Check file extensions and directory contents.
- Make sure the split list contains actual image paths.
- If you renamed or moved data, regenerate the split files.

## `No labels found`

Training with augmentation cannot proceed without usable labels.

Recovery:

- Check that the `labels/` tree mirrors the `images/` tree.
- Verify that at least some label files are present and non-empty.
- Confirm that the filenames match exactly aside from extension and directory.

## Negative or out-of-range coordinates

The loader asserts that normalized coordinates are in bounds.

Recovery:

- Re-export the annotations in YOLO format.
- Confirm the coordinates are normalized to `[0, 1]`.
- Ensure class ids are zero-based integers.

## Too many or too few columns

The loader expects exactly five values per label row.

Recovery:

- Remove confidence scores, extra metadata, or other columns.
- Convert the annotations to plain YOLO label format before training.

## Cache keeps regenerating

A `.cache` file is only helpful when the underlying data source is stable.

Recovery:

- Fix the source paths or labels.
- Remove the stale cache and rebuild it only after the underlying data is correct.

## Anchor warnings

Poor anchor fit is often a symptom of a data-shape problem or a dataset that differs a lot from the default COCO distribution.

Recovery:

- Inspect the labels first.
- Revisit the dataset layout and class counts.
- Fit new anchors only after the basic validation passes.
