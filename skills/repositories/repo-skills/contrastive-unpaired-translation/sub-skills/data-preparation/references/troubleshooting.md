# Troubleshooting

Use this page for dataset-layout and conversion problems.

## Missing images or empty directories

### Symptoms
- A helper reports zero images.
- A dataset loader raises `RuntimeError` or `AssertionError` about missing images.

### Likely causes
- The folder names do not match the expected layout.
- One of the domain directories is empty.

### Recovery
- Recheck the layout in `references/data-formats.md`.
- Make sure the directory names are exactly `trainA`, `trainB`, `testA`, `testB`, `A`, and `B` where required.

## Mismatched A/B pairs

### Symptoms
- `combine_A_and_B.py` or the aligned export helper fails on missing pairs.
- A pair helper produces the wrong images in the same row.

### Likely causes
- The A and B trees contain different filenames or different split names.
- The helper cannot match the source images one-to-one.

### Recovery
- Sort and rename the files so both sides match.
- Re-run the helper on a tiny fixture before processing the full dataset.

## Cityscapes confusion

### Symptoms
- The helper cannot find matching Cityscapes segmentation and photo files.
- The output tree is missing the expected `trainA/trainB` or `testA/testB` folders.

### Likely causes
- The raw `gtFine_trainvaltest` and `leftImg8bit_trainvaltest` trees were not passed to the helper.
- The Cityscapes files were not fully unzipped.

### Recovery
- Re-run `scripts/prepare_cityscapes_dataset.py` with the unzipped source directories.
- Confirm the output tree after a small subset first.

## OpenCV or cascade problems

### Symptoms
- `ImportError` for `cv2`.
- The cat-face crop helper cannot open the Haar cascade file.
- No crops are written even though images exist.

### Likely causes
- OpenCV was not installed.
- The cascade file is missing or the wrong cascade variant was selected.

### Recovery
- Install `opencv-python-headless` in the runtime environment.
- Use `--cascade_path` when you know the exact file path, or `--use_ext` when the extended cascade is the better fit.
- If the helper still finds no faces, lower the threshold parameters on a tiny sample.

## Single-image dataset mistakes

### Symptoms
- SinCUT setup fails before training starts.
- The loader asserts that it expected exactly one image in each domain.

### Likely causes
- The user supplied more than one image in `trainA` or `trainB`.

### Recovery
- Keep one image in each domain for the single-image route.
- If the task needs more than one image per domain, switch back to the unaligned CUT workflow.

## When to stop

Stop and ask for more data when the task requires a large download, a licensed dataset, or a missing system dependency. Those are external prerequisites, not local script bugs.
