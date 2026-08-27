---
name: evaluation
description: "Score EdgeConnect outputs with pixel metrics and validate
  evaluation inputs for FID-style runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation

Use this sub-skill when the task is about scoring EdgeConnect outputs after inference or checking whether evaluation inputs are paired correctly.
It owns the pixel-metric workflow and the preflight checks that make PSNR/SSIM/MAE/FID comparisons trustworthy.

## Covers

- paired ground-truth vs prediction image evaluation
- grayscale pixel metrics on saved outputs
- metric artifact generation such as `metrics.npz`
- FID input preflight for image directories or cached statistics files
- validation of output naming, count alignment, and missing-file problems

## Read first

- `references/evaluation-workflows.md` for command shape and directory expectations.
- `references/metrics-reference.md` for how to interpret PSNR, SSIM, MAE, and FID in this repo.
- `references/troubleshooting.md` when the score command fails or the pairings look wrong.

## Bundled helpers

- `scripts/compute_pixel_metrics.py` computes PSNR/SSIM/MAE for paired image directories and saves `metrics.npz`.
- `scripts/check_eval_inputs.py` validates paired pixel-metric inputs and FID-ready directories or cached `mu`/`sigma` statistics.

## Use for

- comparing generated images against ground truth
- checking that result filenames line up with the expected source names
- verifying that a prediction directory is ready for pixel metrics
- validating FID input directories or precomputed statistic files before you launch a heavier run

## Do not use for

- training or checkpoint creation
- building flists or fixing mask/edge layout problems
- checkpoint-backed inference command generation

## FID note

The source repository's FID helper depends on pretrained Inception weights and network/cache behavior. This sub-skill therefore treats FID as a documented and validated workflow rather than a fully self-contained no-network scorer. Use the bundled input checker first, then run a compatible FID implementation in an environment where the weights are already cached or where downloads are explicitly acceptable.
