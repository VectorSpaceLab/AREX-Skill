# Troubleshooting

## `--eval` complains about row length

**Symptom**

- `All pairs should have ground truth info for evaluation`
- `File "..." needs 38 valid entries per row`

**Fix**

- Validate the manifest with `scripts/validate_pair_file.py --require-gt`.
- Remove `--eval` if the pair file is match-only.
- Make sure every row has the full 38-token evaluation schema.

## Images cannot be read

**Symptom**

- `Problem reading image pair: ...`
- Missing or empty `.npz` outputs because the script exited early

**Fix**

- Check `--input_dir`.
- Confirm the manifest paths are correct and relative to that directory.
- Verify the images actually exist and the process can read them.
- If the manifest uses absolute paths, make sure they point to valid files.

## Cache load failures

**Symptom**

- `Cannot load matches .npz file: ...`
- `Cannot load eval .npz file: ...`

**Fix**

- Delete the corrupt file and rerun.
- If you changed resize, weights, thresholds, or inputs, do not reuse the old cache.
- Use a fresh output directory when the settings change.

## Visualization flag assertions

**Symptom**

- `Must use --viz with --opencv_display`
- `Cannot use --opencv_display without --fast_viz`
- `Must use --viz with --fast_viz`
- `Cannot use pdf extension with --fast_viz`

**Fix**

- Turn on `--viz` before previewing or using `--fast_viz`.
- Use `--viz_extension png` with `--fast_viz`.
- Keep `--opencv_display` only for OpenCV preview mode.

## Empty or weak matches

**Likely causes**

- Wrong weight profile: indoor weights on outdoor scenes, or vice versa
- Resize too small or too large
- Keypoint or match thresholds too strict
- Insufficient texture or motion blur

**Fixes**

- Use the indoor recipe for ScanNet-like pairs and the outdoor recipe for wide-baseline scenes.
- Increase the resize if you are losing too much detail.
- Lower `--keypoint_threshold` or `--match_threshold` if matches are overly sparse.
- Enable `--resize_float` for large outdoor imagery.
- Avoid running far below `160x120`, and avoid very large images above roughly `2000x1500`.

## Slow CPU runs

**Fixes**

- Use the smoke wrapper with `--device cpu --max-length 1` for sanity checks.
- Shrink the resize for debugging.
- Prefer CUDA when it is available and you are not forcing CPU.

## Pose metrics look wrong, fail, or crash at summary time

**Likely causes**

- The manifest intrinsics or pose matrix are malformed
- EXIF rotations are incorrect
- The pair file is being used with the wrong image directory
- The unmodified release is running with NumPy 2.x and hits `AttributeError: module 'numpy' has no attribute 'trapz'` in `pose_auc`

**Fixes**

- Re-run the validator with `--require-gt` and `--input-dir`.
- Confirm the `K0`, `K1`, and `T_0to1` matrices have the right lengths and numeric values.
- Check the rotation integers are in `0..3`.
- If the traceback names `np.trapz`, install `numpy<2` or patch `pose_auc` to use `np.trapezoid` before rerunning evaluation.

## Output files seem to overwrite each other

**Cause**

- Output names are built from the image stems only.

**Fix**

- Use unique image basenames in one run, or separate output directories per dataset split.

## GUI or keyboard preview issues

**Notes**

- This is only relevant when using `--opencv_display`.
- Batch workflows do not need any GUI preview.
- If preview responsiveness is poor, use Matplotlib output or skip the preview entirely.

## Full benchmark caveat

The bundled sample manifests are just smoke-test slices.
For the full ScanNet, YFCC, or Phototourism benchmarks, download the external datasets and use manifests that match the expected folder layout and EXIF corrections.
