# Data-preparation troubleshooting

## Common failures

### No images found

**Symptom**: the loader or helper reports that an input directory is empty.

**Likely cause**: the folder path is wrong, or the files are not in a supported image format.

**Fix**:
- Recheck the directory you passed to `--fold_A`, `--fold_B`, or `--dataroot`.
- Confirm the filenames end with a supported extension.
- Make sure you are pointing at the image folder itself, not a parent directory.

### Paired names do not line up

**Symptom**: the pair helper skips images or writes fewer AB files than expected.

**Likely cause**: the two folders have different filenames or split structures.

**Fix**:
- Compare the A and B filenames before running the helper.
- If you are using `--use_AB`, ensure the A-side names include `_A.` and the B-side names include `_B.`.
- Confirm the split directory names are identical on both sides.

### Wrong layout for the selected dataset mode

**Symptom**: training or inference starts but the loader returns the wrong fields or crashes.

**Likely cause**: `aligned` and `single` expect different directory shapes.

**Fix**:
- Use `aligned` only for horizontally concatenated AB images.
- Use `single` only for one folder of standalone images.
- Do not rely on the repository's `unaligned` stub as a supported path.

### External download helper is inconvenient or unsafe for the run

**Symptom**: you want sample data but do not want the helper to perform a network download.

**Likely cause**: `util.get_data` is designed to fetch remote archives.

**Fix**:
- Treat that helper as reference-only guidance.
- Prefer local fixtures or already-downloaded data for reproducible runs.

### OpenCV not available

**Symptom**: `import cv2` fails in the pair helper.

**Fix**:
- Install `opencv-python-headless` in the inspection or runtime environment.
- Re-run the helper after the import succeeds.

## What to do next

- For training, jump to the training sub-skill after the data layout is correct.
- For inference, jump to the inference sub-skill after the single-image folder is ready.
- For a quick environment sanity check, use the root `check_deblurgan_env.py` helper.
