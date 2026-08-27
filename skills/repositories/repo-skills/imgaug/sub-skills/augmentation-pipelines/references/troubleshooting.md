# Pipeline troubleshooting

## Pipeline changes the image shape

**Symptoms:** downstream model receives unexpected height/width or arrays cannot be stacked.

**Likely causes:** `Crop`, `Pad`, `Resize`, `CropAndPad`, affine `fit_output`, or other size-changing augmenters were used without the intended `keep_size`/resize behavior.

**Recovery:**
- Check whether the task expects exact shape preservation.
- Use `CropAndPad(..., keep_size=True)` when preserving size is desired.
- If output size should change, update downstream shape assumptions and aligned augmentables at the same time.

## Color output looks wrong

**Symptoms:** hue/saturation changes look extreme, channels appear swapped, or a grayscale/single-channel smoke behaves differently from a 3-channel RGB smoke.

**Likely causes:** images came from OpenCV in BGR order, while most imgaug examples assume RGB. Some older imgaug/OpenCV combinations also expose single-channel arithmetic edge cases that do not show up in 3-channel fixtures.

**Recovery:** convert BGR to RGB before imgaug color operations and document the conversion in the workflow. For arithmetic checks, prefer a 3-channel RGB smoke unless the task explicitly needs grayscale.

## Random results are not repeatable

**Symptoms:** each call produces a different transform when the user expected the same result.

**Recovery:**
- Use a single call containing images and all aligned augmentables.
- If separate calls are necessary, create `det = seq.to_deterministic()` and apply `det` to each input group.
- For deeper seed control, use the parameters/random sub-skill.

## Optional `imgcorruptlike` augmenters fail

**Symptoms:** import or runtime errors mention `imagecorruptions`.

**Recovery:** install the optional dependency only if the task needs that family. Otherwise choose an equivalent built-in noise/blur/weather augmenter and record that `imgcorruptlike` was left unverified.

## Dtype or value-range errors

**Symptoms:** errors mention unsupported dtypes, clipping, or values outside expected ranges.

**Recovery:**
- Prefer `uint8` images in `0..255` for common image augmentation.
- Use dtype utilities before and after augmentation when a workflow needs float or integer conversions.
- Be cautious with `uint64`, `int64`, and `float128` in geometric operations; some paths intentionally reject them.

## GUI/display failures

**Symptoms:** `imshow` fails on a server or CI environment.

**Recovery:** avoid GUI display in automated workflows. Use the bundled contact-sheet script to write an image file or inspect arrays numerically.
