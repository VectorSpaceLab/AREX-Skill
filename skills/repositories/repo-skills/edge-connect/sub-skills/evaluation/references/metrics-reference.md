# Metrics reference

## PSNR

Peak signal-to-noise ratio measures how close two images are after converting them to grayscale in the bundled helper.
Higher is better.
The helper uses the image data range of `1.0` because it normalizes the source images to `[0, 1]` before scoring.

## SSIM

Structural similarity measures structural overlap rather than raw pixel error.
Higher is better.
The bundled helper chooses a safe odd window size that fits the image and keeps the comparison on a grayscale pair.
If the images are extremely small, SSIM can still fail because the comparison window becomes too small.

## MAE-style ratio

The source repository's metric script does not compute plain `np.mean(abs(a-b))`.
It computes a normalized absolute-error ratio:

```text
sum(abs(a - b)) / sum(a + b)
```

Lower is better.
The helper keeps that behavior so the generated skill matches the repository's published metric script.
The JSON summary normalizes non-finite values such as infinite PSNR to `null`, while the saved `metrics.npz` keeps the numeric arrays.

## FID

Frechet Inception Distance compares distributions of image features rather than image pairs.
Lower is better.
The score depends on a pretrained Inception feature extractor and is therefore sensitive to cache state, network access, and the chosen implementation.

In this skill, FID is treated as a preflighted workflow: first validate the inputs with `scripts/check_eval_inputs.py fid`, then run whichever compatible FID implementation is already available in your environment.

## Internal training metrics

The training code also uses two internal diagnostics:

- `src.metrics.PSNR`: a tensor-based PSNR helper used in the training and validation loops.
- `src.metrics.EdgeAccuracy`: a precision/recall helper for the edge mask.

These internal metrics are not the same as the external pixel-metric helper and should not be mixed up when you report results.

## Practical reading guide

- Use PSNR/SSIM/MAE when you want per-image or per-dataset quality comparisons against known ground truth.
- Use FID when you care about the distribution of generated images rather than a direct pairwise comparison.
- Use the internal training metrics only when you are inspecting the model's own logging output.
