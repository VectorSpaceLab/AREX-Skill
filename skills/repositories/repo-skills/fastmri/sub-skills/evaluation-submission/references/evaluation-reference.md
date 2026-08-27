# Evaluation reference

This reference captures fastMRI evaluation and submission APIs that matter after a model has produced image-domain reconstructions.

## Prediction file contract

- Prediction directories contain one HDF5 file per fastMRI volume.
- Each prediction filename must match the corresponding target filename for local metric evaluation.
- Each prediction file must contain a dataset named `reconstruction`.
- `fastmri.save_reconstructions(reconstructions, out_dir)` accepts a dictionary mapping output filenames to NumPy arrays and writes each entry to `out_dir / fname` with dataset key `reconstruction`.
- `fastmri.convert_fnames_to_v2(path)` walks `.h5` files in a directory and renames files missing `_v2.h5` to `stem + "_v2.h5"`; it raises `ValueError` when `path` does not exist.

## Challenge target keys

Use the challenge to pick the target reconstruction key:

| Challenge | Target key | Typical output shape |
| --- | --- | --- |
| `multicoil` | `reconstruction_rss` | slices x height x width |
| `singlecoil` | `reconstruction_esc` | slices x height x width |

If the challenge is wrong, evaluation fails with a missing target key or computes against the wrong target family. Use [validate_reconstructions.py](../scripts/validate_reconstructions.py) before evaluation when target files are available.

## CLI behavior

The evaluation module exposes these required and optional CLI arguments:

```bash
python -m fastmri.evaluate \
  --target-path TARGETS \
  --predictions-path PREDICTIONS \
  --challenge {singlecoil,multicoil} \
  [--acceleration ACCELERATION] \
  [--acquisition ACQUISITION]
```

Supported acquisition filters are `CORPD_FBK`, `CORPDFS_FBK`, `AXT1`, `AXT1PRE`, `AXT1POST`, `AXT2`, and `AXFLAIR`. Filtering is applied from target-file attributes; if every target file is skipped, the printed metric statistics are not meaningful.

## Function behavior

Programmatic evaluation calls `fastmri.evaluate.evaluate(args, recons_key)`, where `args` has at least `target_path`, `predictions_path`, `acceleration`, and `acquisition` attributes. The caller must choose `recons_key` as `reconstruction_rss` for `multicoil` or `reconstruction_esc` for `singlecoil`.

Evaluation steps for each target file:

1. Open `target_path / fname` and `predictions_path / fname`.
2. Skip the file if `--acquisition` is set and does not match target attribute `acquisition`.
3. Skip the file if `--acceleration` is set and does not match target attribute `acceleration`.
4. Read target dataset `reconstruction_rss` or `reconstruction_esc`.
5. Read prediction dataset `reconstruction`.
6. Center-crop target to `(target.shape[-1], target.shape[-1])`.
7. Center-crop prediction to the same square shape.
8. Push MSE, NMSE, PSNR, and SSIM into `Metrics`.

## Metrics

`fastmri.evaluate.Metrics` maintains running `runstats.Statistics` for the metric functions in `METRIC_FUNCS`:

- `MSE`: mean squared error, `mean((gt - pred) ** 2)`.
- `NMSE`: squared error norm divided by squared ground-truth norm.
- `PSNR`: `skimage.metrics.peak_signal_noise_ratio`, using `gt.max()` as `data_range` when `maxval` is omitted.
- `SSIM`: mean slice-wise `skimage.metrics.structural_similarity`, requiring 3D target and prediction arrays.

`Metrics.__repr__()` prints sorted metric names as `name = mean +/- 2 * stddev`.

## Shape and crop expectations

Evaluation arrays are expected to be real-valued image stacks with at least the last two spatial dimensions. SSIM specifically expects 3D arrays: `slices x height x width`. Because evaluation crops both target and prediction to a square based on target width, predictions can be larger than the target square but should not be smaller than the requested crop.

For array-level crop mechanics and transform details, use [mri-operators](../../mri-operators/SKILL.md). For target split layout and HDF5 field meanings, use [data-loading](../../data-loading/SKILL.md).
