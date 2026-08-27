# Feature Detection Troubleshooting

## Empty `FeatureSet`

**Symptoms**

- `if features:` is false.
- Indexing `features[0]` fails.

**Likely causes**

- Thresholds are too strict.
- The image was resized or color-converted unexpectedly.
- The target object is too small for `minsize` or detector defaults.
- Optional backend/detector support is missing.

**Recovery**

1. Confirm `img.size()` and that the image is non-empty.
2. Draw or save the source image to verify the target is visible.
3. Loosen thresholds or `minsize` and rerun on a known sample image.
4. Add explicit empty-result handling before measuring or drawing.

## Blob order confusion

**Symptoms**

- The example chooses `blobs[-1]`, but the selected blob is not expected.

**Cause**

`FeatureSet` ordering can depend on detector output and helper methods. Native examples often assume a sample-image-specific ordering.

**Recovery**

Sort or filter by explicit metrics such as area, radius, x/y position, or bounding box rather than relying on index alone.

## Template match produces false positives or no matches

**Causes**

- Scale or rotation changed.
- Threshold semantics differ by method.
- The template and source were color/grayscale converted inconsistently.

**Recovery**

- Record the method (`SQR_DIFF_NORM`, `CCOEFF`, `CCORR`, etc.).
- Test at least one known sample pair (`template.png`, `templatetest.png`).
- Use keypoints when scale/rotation invariance is required and the OpenCV build supports the requested detector.

## Keypoints fail with SURF/SIFT/FREAK

**Symptoms**

- OpenCV reports missing detector/extractor constructors.
- `findKeypoints(flavor='SURF')` fails or returns no descriptors.

**Cause**

SimpleCV targets older OpenCV feature APIs. Many builds do not include nonfree SURF/SIFT or old feature-factory names.

**Recovery**

- Inspect available OpenCV features before changing SimpleCV code.
- Try a different flavor if the task permits it.
- Use template matching, corners, or blobs as a simpler fallback.
- Document the OpenCV build limitation if the user specifically asked for SURF/SIFT.

## Haar features return nothing

**Causes**

- Wrong cascade path or name.
- Scale/min-neighbor/min-size parameters unsuitable for the image.
- The image does not contain the target object.

**Recovery**

Use `HaarCascade(fname=None, name=None)` for built-in cascades when available, then tune `scale_factor`, `min_neighbors`, and size bounds. Verify with a sample image before using a user image.

## Barcode or OCR fails

**Causes**

- ZXing or tesseract is absent.
- The external executable or model data is not on the path.

**Recovery**

Run the root environment check and treat the dependency as optional. Install ZXing only for barcode tasks and tesseract only for OCR tasks. Do not block core feature detection on these optional integrations.
