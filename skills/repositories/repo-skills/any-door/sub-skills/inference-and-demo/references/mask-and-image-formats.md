# Mask and Image Formats

AnyDoor’s preprocessing is mask-sensitive. Many user failures come from an
image that looks right but is formatted in a way the preprocessing code does not
expect.

## Expected inputs

- **Reference image**: RGB or RGBA source image of the object to transplant.
- **Reference mask**: binary mask covering the object; if the source image has
  an alpha channel, the alpha channel can be used as the mask.
- **Target image**: RGB background image containing the region to customize.
- **Target mask**: binary mask of the object region in the target image.

## Useful conventions from the source

- Masks are thresholded around `128` in the repo scripts.
- Binary masks are usually represented as `0` and `1` before later conversion.
- The preprocessing code expects the object region to be non-empty.
- Target masks should not be so small that the bbox disappears, and not so large
  that the crop becomes uninformative.

## What the validator should check

- Image and mask files exist.
- Image and mask dimensions are compatible.
- Masks are not blank.
- Masks are close to binary, or at least thresholdable to binary values.
- Reference and target objects are large enough to yield a meaningful crop.

## Shape-control note

If shape control is enabled, the target mask is used more directly in the
collage path. That makes mask quality even more important than in the default
path.

## Common mistakes

- Passing the background image as the reference image.
- Forgetting to supply the separate reference mask when the image has no alpha
  channel.
- Feeding a soft mask without thresholding it.
- Using the wrong label in a dataset-derived parse mask.
- Handing the model a crop that does not actually contain the object.

## Resulting guidance

When this format is wrong, the fix is almost always to validate or repair the
mask first. Changing guidance scale or DDIM steps rarely fixes a bad mask.
