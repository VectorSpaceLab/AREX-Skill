# Troubleshooting evaluation and submission

## Prediction file is missing `reconstruction`

Symptom: evaluation or validation raises a missing key error for `reconstruction`.

Fix: rewrite predictions with `fastmri.save_reconstructions` or create each HDF5 file with dataset key `reconstruction`. Do not use target keys such as `reconstruction_rss` or `reconstruction_esc` inside prediction files.

## Target and prediction filenames do not match

Symptom: evaluation fails opening `predictions_path / target_filename`, or the validator reports missing predictions.

Fix: keep prediction filenames identical to target/test input filenames during local metric evaluation. Run v2 filename conversion only for the workflow that requires `_v2.h5` suffixes, and do it after local target-matched evaluation unless the targets also use v2 names.

## Challenge uses the wrong target key

Symptom: `--challenge multicoil` fails on singlecoil targets or `--challenge singlecoil` fails on multicoil targets.

Fix: use `multicoil` for target key `reconstruction_rss` and `singlecoil` for target key `reconstruction_esc`. The prediction key remains `reconstruction` for both challenges.

## Acquisition or acceleration filters skip all files

Symptom: filtered evaluation prints unusable statistics or validation reports zero included targets.

Fix: inspect target attributes and remove or correct `--acquisition` / `--acceleration`. The acceleration comparison is exact against target attribute `acceleration`, and acquisition must be one of the supported strings used in the target metadata.

## Prediction shape or crop mismatch

Symptom: center-crop or SSIM fails, or metric results are obviously invalid.

Fix: predictions should be real image stacks shaped like `slices x height x width`. Evaluation crops both target and prediction to the square target width. If predictions are smaller than that crop, regenerate outputs at the expected resolution. For lower-level crop behavior, use [mri-operators](../../mri-operators/SKILL.md).

## FLAIR 203 header/crop caveat

Symptom: zero-filled brain files with `FLAIR_203` in the name request a crop larger than the reconstructed image height.

Fix: the bundled zero-filled script clamps the crop to the available square image height when needed. The original zero-filled README notes that three such files in the test set were ignored for the brain leaderboard, so document any skipped or clamped files in downstream reporting.

## Leaderboard is unavailable

Symptom: the user asks where to upload outputs, but the historical fastmri.org leaderboard is not reachable.

Fix: explain that this checkout's README says leaderboards are unavailable after the fastmri.org domain transfer. Continue preparing local output directories and metrics, but do not promise successful public upload.

## BART compressed sensing cannot start

Symptom: imports or shell commands fail for BART, often involving missing BART Python wrappers or environment variables.

Fix: BART CS is external and reference-only in this skill. The historical workflow requires a separate BART install with `TOOLBOX_PATH` pointing at the cloned BART repository and `PYTHONPATH` including the BART Python wrapper. Do not treat BART as part of the Python `fastmri` package.

## `ModuleNotFoundError: requests`

Symptom: importing `fastmri.data` or modules that transitively import it fails because `requests` is missing.

Fix: install `requests` into the active Python environment. This checkout imports `requests` from `fastmri.data` even though `setup.cfg` does not declare it, so missing `requests` can block evaluation-adjacent imports that touch data utilities.
