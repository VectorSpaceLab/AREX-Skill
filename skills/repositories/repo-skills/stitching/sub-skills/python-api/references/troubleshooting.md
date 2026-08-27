# Python API Troubleshooting

## When to read this

Read this when Python code imports the package successfully but the panorama
workflow fails or produces an unexpected result.

## Common problems

### `StitchingError: images must not be an empty list`

**Cause**: you passed an empty list or filtered all inputs out before calling
`stitch`.

**Fix**: verify the list before calling the API and make sure at least two
images are present.

### `StitchingError: Invalid Argument: ...`

**Cause**: the settings dictionary includes a key that the package does not
recognize.

**Fix**: compare your settings with `Stitcher.DEFAULT_SETTINGS`.

### `StitchingError` about masks

**Cause**: the feature-mask list length does not match the image list length,
or a mask resolution does not match the image.

**Fix**:
- Build one mask per image.
- Make sure the mask dimensions match the image dimensions exactly.
- Use the diagnostics sub-skill if you need to inspect the mask coverage.

### A stitch succeeds but drops an image

**Cause**: the overlap is weak, the detector is not a good fit, or the
confidence threshold is too strict.

**Fix**:
- Lower `confidence_threshold`.
- Try `detector="sift"` or another detector choice.
- Write a matches graph to inspect the component structure.

### `AffineStitcher` warns about overwritten defaults

**Cause**: you passed a value that differs from one of the affine defaults.

**Fix**:
- Confirm that the override is intentional.
- If you want the default affine behavior, remove the override.

### Crop fails after a valid panorama is built

**Cause**: the warped mask does not support a valid largest interior rectangle.

**Fix**:
- Set `crop=False`.
- If you only need the panorama output, skipping crop is the safe recovery.

### Reusing the same stitcher looks inconsistent

**Cause**: the scale adapts to the current image set.

**Fix**:
- Treat each call as a new run.
- Re-check your assumptions when the input image sizes or overlap pattern change.

## Next checks

- [API reference](api-reference.md) for the exact signatures and defaults.
- [Workflow recipes](workflows.md) for copyable Python snippets.
- The root [troubleshooting](../../../references/troubleshooting.md) for package
  install/import and headless GUI issues.
