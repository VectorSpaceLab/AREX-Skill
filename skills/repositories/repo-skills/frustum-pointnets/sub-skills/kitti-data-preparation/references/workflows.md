# Preparation workflows

## Ground-truth train/validation

Use a training index and the `training` split. The source-equivalent operations
are `--gen_train` (perturbed 2D boxes, five augmentations per box) and
`--gen_val` (unperturbed boxes). Add `--car_only` when downstream model
metadata is configured for the single Car class. Confirm label parsing and
free space before launching; the run writes its pickle next to the index/data
code in the original release, so a port should make the output directory
explicit and stage atomically.

## RGB-detection validation

Use `--gen_val_rgb_detection` with a detector file and the training sensor
files. Detector boxes produce unlabeled frustum point sets for later inference;
they do not provide 3D ground truth. The source caches calibration and projected
points per frame, ignores non-whitelisted classes, and rejects boxes under 25
pixels or with fewer than five points. Preserve the detector confidence and
frame id in the output stream.

## Safe staging checklist

- Validate all index and detector rows before conversion.
- Check image/Velodyne/calibration/label counts and free disk space.
- Write to a new staging filename; do not overwrite a prior pickle.
- Record class whitelist, augmentation, thresholds, source revision, and
  Python/pickle protocol.
- Inspect the pickle object count and representative array shapes before
  connecting it to `train/provider.py` or `train/test.py`.
- Treat `--demo` as interactive visualization, not as an automated smoke test.
