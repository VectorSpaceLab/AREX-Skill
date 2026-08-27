# Troubleshooting

## Import fails: `No module named 'models'`

**Cause**: the repository is source-only and the checkout root is not on Python's import path.

**Fixes**:

- Run code from the repository root.
- Add the repository root to `PYTHONPATH`.
- Use the bundled helper scripts with `--repo-root <superglue-repo-root>` so they add the path explicitly.

## Checkpoint files are missing

**Symptoms**: model construction fails while loading `superpoint_v1.pth`, `superglue_indoor.pth`, or `superglue_outdoor.pth`.

**Fixes**:

- Use a source distribution or checkout that includes `models/weights/`.
- Confirm all three expected files exist.
- Do not rename the files unless you also modify the source code that loads them.
- Run `scripts/check_superglue_environment.py --repo-root <superglue-repo-root>` to list missing files.

## PyTorch checkpoint loading warnings or failures

Old `.pth` files may produce warnings or behavior differences on much newer PyTorch releases. If loading fails:

1. Confirm the file exists and is not truncated.
2. Try a stable PyTorch release compatible with the local Python and hardware.
3. Avoid editing checkpoint tensors unless the task explicitly requires model surgery.
4. For a quick isolated check, run the programmatic API smoke helper on CPU.

## CUDA unavailable or unexpectedly unused

The scripts use CUDA only when `torch.cuda.is_available()` is true and `--force_cpu` is not set.

**Fixes**:

- Remove `--force_cpu` if you want acceleration.
- Check the PyTorch build and driver stack.
- For portable validation, use CPU and keep smoke runs small.
- Do not treat CUDA as required for correctness; it mainly changes speed and memory headroom for this release.

## OpenCV cannot read images

**Symptoms**: `Problem reading image pair`, `Error reading image`, or first-frame failure.

**Fixes**:

- Verify paths relative to the selected `--input_dir` or `--input` directory.
- Confirm file extensions match the directory glob.
- Check image permissions and corruption.
- For pair manifests, run the bundled validator with `--input-dir`.

## GUI/window issues

**Symptoms**: no OpenCV window, keyboard controls do not respond, or preview crashes.

**Fixes**:

- Use `--no_display` on remote/headless machines.
- Prefer output images and smoke wrappers for validation.
- Use a GUI-enabled OpenCV build for interactive demo work.
- Keep the OpenCV window focused when using keyboard controls.

## Empty or weak matches

Common causes:

- image resized too small;
- threshold values too strict;
- wrong indoor/outdoor weights;
- poor anchor frame in the live demo;
- low-texture, blurred, or extreme viewpoint images.

Recovery:

- Increase the resize target while staying within memory limits.
- Lower `keypoint_threshold` to detect more points.
- Lower `match_threshold` to accept more tentative matches.
- Switch `--superglue indoor`/`outdoor` based on the scene.
- Use `--show_keypoints` to distinguish detector failure from matcher filtering.

## `--eval` fails or metrics are nonsensical

`--eval` requires a 38-token row per pair: two image names, two rotations, two flattened `3x3` intrinsics matrices, and one flattened `4x4` relative pose matrix.

If the failure is `AttributeError: module 'numpy' has no attribute 'trapz'`, the unmodified release is running with a NumPy 2.x build that removed the alias used by `models.utils.pose_auc`. Use `numpy<2` for compatibility or patch the source to call `np.trapezoid`.

Use the pair-matching validator:

```bash
python sub-skills/pair-matching-evaluation/scripts/validate_pair_file.py \
  --pair-file <pairs.txt> \
  --input-dir <images_dir> \
  --require-gt
```

If a manifest has only image paths or only rotation fields, remove `--eval` or generate the missing ground-truth fields.

## Slow runs or memory pressure

- Use `--max_length 1` and small resize values for smoke tests.
- Reduce `--max_keypoints` for dense scenes.
- Prefer CUDA for large images and many pairs.
- Avoid full benchmark manifests until one-pair validation is clean.

## Reproducibility differences

The README reports that released code can differ slightly from paper numbers because of post-release simplifications and library differences. OpenCV resizing and RANSAC randomization can change visualizations and pose metrics. Treat exact README tables as approximate unless you control the full dataset and dependency stack.

## License and release-scope limitations

The code and weights are released for noncommercial research use. The repository does not provide training code, SIFT SuperGlue, or homography SuperGlue. If a task asks for those unavailable artifacts, state the release limitation and avoid inventing unsupported workflows.
