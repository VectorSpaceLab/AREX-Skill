# Troubleshooting

## When to read this

Read this when installation succeeds but stitching fails, the CLI produces no
useful panorama, the cropper errors, or the environment is missing GUI or image
fixtures.

## Common failures and recovery paths

### `ImportError` or `ModuleNotFoundError` for `stitching`, `cv2`, or `largestinteriorrectangle`

**Symptoms**
- `python -c "import stitching"` fails.
- `stitch --help` is missing or crashes.
- `ImportError` mentions `cv2` or `largestinteriorrectangle`.

**Likely causes**
- The package was not installed in the active environment.
- `opencv-python-headless` or the GUI build is missing.
- The environment has an incomplete dependency set.

**Recovery**
- Re-run the install guidance from [Installation](installation.md).
- Use `python scripts/check_install.py` to confirm the public package imports.
- If you need a server-friendly build, install `stitching-headless` instead of
  the GUI package.

### `StitchingError: No match exceeds the given confidence threshold`

**Symptoms**
- A stitch attempt stops before a panorama is produced.
- The error mentions confidence threshold, overlap, or common features.

**Likely causes**
- The images do not overlap enough.
- The chosen detector or matcher is too strict for the input.
- A bad `feature_masks` selection hides useful keypoints.

**Recovery**
- Lower `confidence_threshold` / `match_conf`.
- Try a different detector such as `orb`, `sift`, `brisk`, or `akaze`.
- Use the diagnostics workflow to inspect matches and mask coverage.

### `StitchingWarning: Not all images are included`

**Symptoms**
- The stitch completes, but a warning reports dropped images.

**Likely causes**
- One image has weaker overlap or a different viewpoint.
- `range_width` or matching settings exclude a needed neighbor.

**Recovery**
- Inspect the matches graph and verbose output.
- Reduce the confidence threshold if the match graph looks sparse.
- Confirm the input list order and detector choice.

### Feature-mask resolution errors

**Symptoms**
- An error says the mask resolution does not match the image resolution.
- The CLI fails when `--feature_masks` are supplied.

**Likely causes**
- The masks were created for the wrong image size.
- The image and mask lists are different lengths.

**Recovery**
- Make sure each mask matches its image shape exactly.
- Make sure the list lengths match.
- Use the diagnostics workflow to confirm the masks are the intended size.

### Crop or largest-interior-rectangle failures

**Symptoms**
- An error mentions an invalid contour or asks to use `--no-crop`.
- Cropping fails after warping.

**Likely causes**
- The stitched panorama mask is not a single clean contour.
- The cropper cannot find a valid largest interior rectangle.

**Recovery**
- Re-run with `--no-crop` or `crop=False`.
- Compare the result with `stitch_verbose` outputs to see where the mask became irregular.
- If you only need a panorama result, skipping crop is often the safest fix.

### GUI preview problems

**Symptoms**
- `--preview` hangs, opens no window, or errors in a headless session.

**Likely causes**
- The environment lacks a display server.
- You installed the headless OpenCV build.

**Recovery**
- Omit `--preview`.
- Use `stitching-headless` for server environments.
- If you need a preview, run in an environment with a working GUI stack.

### `--try_use_gpu` does nothing

**Symptoms**
- The CLI accepts `--try_use_gpu`, but no GPU path appears to run.

**Likely causes**
- The installed OpenCV build is CPU-only.
- CUDA support is optional and not part of the minimum contract.

**Recovery**
- Treat the flag as optional.
- Only expect GPU use with a CUDA-enabled OpenCV build.
- Do not rely on this flag as proof of a required GPU workflow.

## Useful next steps

- [CLI troubleshooting examples](../sub-skills/cli/references/troubleshooting.md)
- [Python API troubleshooting](../sub-skills/python-api/references/troubleshooting.md)
- [Diagnostics workflow guide](../sub-skills/diagnostics/references/diagnostic-workflows.md)
- `scripts/check_install.py` for install and import smoke checks
- `scripts/download_sample_images.py` when you need the public native fixtures
