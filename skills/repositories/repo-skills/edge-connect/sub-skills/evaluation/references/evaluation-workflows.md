# Evaluation workflows

## Pixel-metric workflow

Use the pixel-metric helper when you already have generated outputs and want PSNR, SSIM, and the repo's normalized MAE-style score.
The helper expects two directories:

- `--data-path`: ground-truth images
- `--output-path`: generated predictions

The directories are paired by basename. The helper loads images, converts them to grayscale, and compares matching names only.
It writes a `metrics.npz` file into the prediction directory and prints a concise summary.
It works with both modern `skimage.metrics` and the legacy `skimage.measure.compare_psnr` / `compare_ssim` names that older EdgeConnect environments still expose.
When the prediction and ground-truth images are identical, PSNR can become infinite; the JSON summary normalizes non-finite values to `null` so the output remains machine-readable.

Example:

```bash
python scripts/compute_pixel_metrics.py \
  --data-path <ground-truth-dir> \
  --output-path <prediction-dir>
```

Add `--json` when you want a machine-readable summary on stdout.

### Input expectations

- Use top-level `.jpg`, `.jpeg`, or `.png` files.
- Keep the image names unique across the directory.
- Make sure the prediction directory contains exactly the files you expect to score.
- Keep ground-truth and prediction dimensions aligned; the bundled helper fails on shape mismatch instead of silently resizing.

## FID preflight workflow

FID is more expensive than the pixel metrics and depends on a compatible Inception-backed implementation with cached or downloadable pretrained weights.
This sub-skill does not bundle the original network-sensitive downloader. Instead, it validates the inputs you will hand to any FID implementation.

Use the checker in one of two modes:

```bash
python scripts/check_eval_inputs.py pixel --data-path <ground-truth-dir> --output-path <prediction-dir>
python scripts/check_eval_inputs.py fid --paths <real-images-or-stats> <generated-images-or-stats>
```

For FID, each path may be either:

- an image directory containing top-level `.jpg`, `.jpeg`, or `.png` files, or
- a cached `.npz` file containing `mu` and `sigma` arrays.

The checker confirms the directory layout or cached-statistics layout before you launch a heavier FID run.

### When to stop and reassess

- If the required weights are not cached and network access is not acceptable, stop before attempting FID.
- If the directories are not from the same image domain or the statistics file is missing `mu`/`sigma`, fix the inputs first.
- If you only need quick quality feedback on EdgeConnect outputs, prefer the pixel metrics.

## Output expectations

Pixel metrics produce two artifacts:

- printed summary statistics for the current comparison
- `metrics.npz` saved beside the prediction directory contents

The checker produces only a preflight report and never scores the images itself.
