# Troubleshooting

Start with safe probes that do not construct models or download weights:

```bash
python scripts/check_pytorch_fid_env.py
python scripts/validate_fid_inputs.py INPUT_A INPUT_B --expected-dims 2048
python scripts/inspect_stats_npz.py maybe_stats.npz
```

## Install or import failure

Symptoms:

- `ModuleNotFoundError: No module named 'pytorch_fid'`
- `pytorch-fid: command not found`
- `python -m pytorch_fid` cannot locate the module

Likely causes:

- Package is not installed in the active Python environment.
- Console script directory is not on `PATH`.
- A different Python executable is being used than the one used for install.

Recoveries:

1. Install with `pip install pytorch-fid` in the intended environment.
2. Prefer `python -m pytorch_fid ...` if the console script is missing from
   `PATH`.
3. Run `python scripts/check_pytorch_fid_env.py --json` to inspect import,
   distribution metadata, CLI help, and torch/torchvision versions.

## NumPy / torch ABI warning or failure

Symptoms:

- Warnings about modules compiled against NumPy 1.x being run with NumPy 2.
- Torch import warnings or failures mentioning NumPy ABI.
- FID import probe works on one machine but not another after NumPy upgrade.

Likely cause:

- The installed torch build is not compatible with the installed NumPy major
  version.

Recoveries:

1. Use a NumPy 1.x runtime for affected torch builds, for example `numpy<2`.
2. Re-run `python scripts/check_pytorch_fid_env.py` after changing packages.
3. Avoid changing the FID command itself until the import layer is clean.

## Missing paths or output collisions

Symptoms:

- `RuntimeError: Invalid path: ...`
- `RuntimeError: Existing output file: ...` in `--save-stats` mode

Likely causes:

- One of the two comparison paths does not exist.
- `--save-stats` output path already exists; the package refuses overwrite.
- Command shape for `--save-stats` was confused with comparison mode.

Recoveries:

1. Validate with `python scripts/validate_fid_inputs.py INPUT_A INPUT_B`.
2. For `--save-stats`, pass `DATASET_DIR OUTPUT_STATS.npz` and choose a new
   output filename if the old one should be preserved.
3. Keep comparison mode as `PATH_A PATH_B` without `--save-stats`.

## Empty directories or no supported image files

Symptoms:

- Later DataLoader/model errors after a directory path appeared valid.
- Batch-size warnings followed by failure.
- FID result cannot be produced for a directory with files present.

Likely causes:

- Directory contains no files with supported suffixes.
- Images are nested in subdirectories; package discovery is shallow.
- Suffixes are uppercase or unusual.
- Files have supported suffixes but are corrupt or not readable by Pillow.

Recoveries:

1. Run `python scripts/validate_fid_inputs.py DIR_A DIR_B` and inspect counts.
2. Move or symlink images directly under the input directory.
3. Use supported lowercase suffixes: `bmp`, `jpg`, `jpeg`, `pgm`, `png`, `ppm`,
   `tif`, `tiff`, `webp`.
4. Try opening a failing image with Pillow if corruption is suspected.

## First-run weights download, cache, or network failure

Symptoms:

- First real FID run stalls or fails while loading Inception.
- Error references a GitHub release URL, PyTorch cache, URL loading, or network.
- Safe validation scripts pass, but model construction fails.

Likely cause:

- `InceptionV3(use_fid_inception=True)` loads FID-specific weights through
  PyTorch's `load_state_dict_from_url` when the weights are not cached.

Recoveries:

1. Allow network access for the first model construction, or pre-populate the
   PyTorch cache according to local policy.
2. Retry after confirming cache permissions and available disk space.
3. Do not switch to `use_fid_inception=False` for standard FID; that changes the
   model weights and score comparability.
4. Treat this as an environment/cache issue, not an image input issue, when the
   validation scripts pass.

## CUDA unavailable or CUDA OOM

Symptoms:

- `Torch not compiled with CUDA enabled`
- `CUDA error: out of memory`
- Invalid device string such as unavailable `cuda:1`
- CPU works but `--device cuda:0` fails

Likely causes:

- CPU-only torch build.
- No visible CUDA device.
- Batch size is too large for the GPU memory.
- Requested device index does not exist.

Recoveries:

1. Run `python scripts/check_pytorch_fid_env.py --json` and inspect CUDA fields.
2. Use `--device cpu` when CUDA is unavailable.
3. Use a valid device string such as `cuda:0` only when `torch.cuda.is_available()`
   is true.
4. Reduce `--batch-size` before changing the feature dimension.
5. Lower `--num-workers` if worker startup or host memory pressure appears.

## Dimension or stats shape mismatch

Symptoms:

- Assertion about mean vectors having different lengths.
- Assertion about covariances having different dimensions.
- FID computed with a saved stats file gives nonsensical or non-comparable
  values.

Likely causes:

- `.npz` files were generated with different `--dims` values.
- CLI `--dims` does not match the saved stats dimension.
- `mu` and `sigma` arrays are malformed.

Recoveries:

1. Run `python scripts/inspect_stats_npz.py STATS_A.npz STATS_B.npz`.
2. Re-run validation with `--expected-dims`.
3. Regenerate stats with the intended dimension.
4. Never compare scores across `64`, `192`, `768`, and `2048` settings.

## Singular covariance or complex `sqrtm`

Symptoms:

- Message: `fid calculation produces singular product; adding ... to diagonal`
- `ValueError: Imaginary component ...`
- Unstable values for very small datasets

Likely causes:

- Too few images for a stable covariance estimate.
- Nearly singular covariance matrices.
- Non-finite or malformed stats.

Recoveries:

1. Inspect stats with `python scripts/inspect_stats_npz.py STATS.npz`.
2. Use more images for each side of the comparison.
3. Regenerate stats after removing corrupt images and validating inputs.
4. Treat non-negligible imaginary-component errors as invalid stats or an
   ill-conditioned comparison rather than silently discarding the error.

## Non-comparable FID scores

Symptoms:

- Two reported scores disagree more than expected.
- A score from this package is compared directly to an official TensorFlow FID
  score.
- A lower-dimensional exploratory score is mixed with a standard 2048 score.

Likely causes:

- Different FID implementations or Inception weights.
- Different feature dimensions.
- Different preprocessing, image resizing/cropping, dataset split, or reference
  stats provenance.
- Different package versions or cached weights.

Recoveries:

1. Report package/version, dimension, command/API, reference stats, and input
   preprocessing with every score.
2. Recompute all compared values with the same package, `--dims`, reference
   stats, and image preparation.
3. Do not treat this package's README caveat about TensorFlow comparability as a
   minor formatting issue; it affects leaderboard-style comparisons.

## Unsupported or corrupt image files

Symptoms:

- Pillow `UnidentifiedImageError` or decode errors.
- A directory has images, but supported count is lower than expected.
- WebP/TIFF behavior differs across environments.

Likely causes:

- Unsupported suffix or uppercase/unexpected suffix patterns.
- Corrupt files or non-image files with image suffixes.
- Pillow build lacks support for a specific format variant.

Recoveries:

1. Validate suffix counts with `scripts/validate_fid_inputs.py`.
2. Normalize files to supported formats such as PNG or JPEG when possible.
3. Remove corrupt files or regenerate the dataset.
4. Verify Pillow can open representative files before launching a large FID run.
