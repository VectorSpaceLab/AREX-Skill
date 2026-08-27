# Segmentation and Tracking Troubleshooting

## Mask is empty or all foreground

**Causes**

- Color model was built from the wrong crop or color.
- Difference threshold is too high or too low.
- Frames are identical or misordered.
- Background model has not warmed up.

**Recovery**

1. Save the raw input frames.
2. Save `getRawImage()` and `getSegmentedImage()` separately.
3. Tune threshold/model crop on a known sample before using user data.
4. Check `isReady()` before treating output as meaningful.

## `getSegmentedBlobs()` returns no blobs

**Causes**

- The mask is empty.
- Foreground is too small or noisy for blob extraction.
- The segmentation model is not ready.

**Recovery**

Inspect the mask image first. If the mask is valid but blobs are missing, route to `feature-detection` and tune blob thresholds/minsize.

## Tracking fails after the first frame

**Causes**

- Missing or wrong initial bounding box.
- Current and previous frames are not paired correctly.
- Object leaves the frame or changes appearance.
- The tracker relies on an unavailable OpenCV feature.

**Recovery**

- Validate frame order and dimensions.
- Draw the bounding box on the first frame before tracking.
- Try a simpler method (`CAMShift` or `DiffSegmentation` + blobs) before SURF/LK/MF.
- Keep live loops finite until one track update works.

## Live tracking examples block or fail

**Cause**

Original tracking examples use cameras, display windows, or mouse interaction.

**Recovery**

Use `VirtualCamera` or static sample frame pairs for automation. Route camera/display setup to `../acquisition-display-shell/` and return to this sub-skill for the segmentation/tracking algorithm once frames are available.

## MOG or advanced tracking breaks on OpenCV version

**Cause**

SimpleCV uses old OpenCV APIs. A build that imports `cv2` may still miss older tracker, MOG, or nonfree feature constructors.

**Recovery**

Run the root OpenCV compatibility checks. If the specific OpenCV method is unavailable, document the build limitation and choose a simpler segmentation or feature-detection fallback.
