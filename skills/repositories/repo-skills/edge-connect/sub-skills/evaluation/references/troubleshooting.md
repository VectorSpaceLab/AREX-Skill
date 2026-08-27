# Troubleshooting

## Missing prediction image

**Symptom:** the pixel-metric helper reports a missing file or fewer scored pairs than expected.

**Likely cause:** the prediction directory does not contain a basename that matches the ground-truth image.

**Fix:**

- compare the sorted basenames in both directories,
- rename the outputs if they collided,
- rerun the checker before recomputing the metrics.

## Unexpected extra outputs

**Symptom:** the prediction directory contains extra images that are not part of the ground-truth set.

**Likely cause:** debug outputs or a previous run left additional files in the directory.

**Fix:**

- remove the unrelated files,
- or keep them in a separate output directory before rescoring.

## Shape mismatch

**Symptom:** the pixel-metric helper stops on a width/height mismatch.

**Likely cause:** the generated output and the ground-truth reference do not have the same dimensions.

**Fix:**

- verify that the inference step produced the expected image size,
- or regenerate the outputs from the correct checkpoint/config pair.

## SSIM fails on tiny fixtures

**Symptom:** SSIM raises an error on very small test images.

**Likely cause:** the comparison window cannot fit the image.

**Fix:**

- use a larger fixture,
- or keep the helper's adaptive window by leaving the images at a realistic size.

## FID inputs are incomplete

**Symptom:** the FID preflight checker complains about missing images or missing `mu`/`sigma` statistics.

**Likely cause:** the input directories are empty, the image pair is incomplete, or the cached statistics file is not a valid FID statistics archive.

**Fix:**

- populate the directories with the expected top-level `.jpg`, `.jpeg`, or `.png` files,
- or regenerate the statistics file so it contains `mu` and `sigma` arrays.

## FID is not worth the cost for a quick check

**Symptom:** you only need a fast quality sanity check and are considering FID anyway.

**Likely cause:** FID feels like the most complete score, but it is heavier than necessary for a small debugging loop.

**Fix:**

- use the pixel metrics first,
- reserve FID for a later pass when the inputs and weights are already prepared.

## Runtime dependencies look too new

**Symptom:** the metrics helper imports fail before any scoring happens.

**Likely cause:** the environment is missing the repo's legacy-compatible scientific stack.

**Fix:**

- revisit `references/installation.md` in the root skill,
- verify that the environment can import Pillow, NumPy, and modern `skimage.metrics`,
- then rerun the preflight checker.
