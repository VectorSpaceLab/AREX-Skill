# Diagnostic Workflows

## When to read this

Read this when you already know stitching is failing or producing a weak result
and you want a stage-by-stage recovery plan.

## 1) Check the verbose output first

If a run used `stitch_verbose(...)` or `stitch --verbose`, inspect the output
folder before changing settings.

Expected stage names commonly include:

- `00_stitcher.txt`
- `01_features_img*.jpg`
- `02_matches_img*_to_img*.jpg`
- `03_matches_graph.txt`
- `04_warped_img*.jpg`
- `05_timelapse_img*.jpg`
- `06_estimated_mask_to_crop.jpg`
- `06_lir.jpg`
- `07_timelapse_cropped_img*.jpg`
- `08_seam_mask*.jpg`
- `08_compensated*.jpg`
- `09_result.jpg`
- `09_result_with_seam_lines.jpg`
- `09_result_with_seam_polygons.jpg`

## 2) If images are dropped, inspect matches and confidence

Use this when a warning says not all images are included.

### What to check
- Are the image contents overlapping enough?
- Is the detector appropriate for the scene?
- Is `confidence_threshold` too strict?
- Does the matches graph show a disconnected component?

### Recovery order
1. Lower `confidence_threshold` or `match_conf`.
2. Try another detector such as `sift`.
3. Reduce `range_width` only if the image order is known and local.
4. Re-run with verbose outputs.

## 3) If feature masks are involved, check them before rerunning

### What to check
- One mask per image.
- Each mask has the same width and height as its image.
- The mask actually covers the region you want to keep.

### Recovery order
1. Confirm the count and dimensions.
2. Recreate the masks if the image size changed.
3. Re-run a safe validator before a full stitch.

## 4) If crop fails, inspect the seam and crop stages

### What to check
- Does `06_estimated_mask_to_crop.jpg` show a clean mask?
- Does `06_lir.jpg` show a valid interior rectangle?
- Are the seam masks sensible before cropping?

### Recovery order
1. Re-run with `--no-crop` or `crop=False`.
2. Keep verbose outputs for later comparison.
3. Only try more aggressive crop settings if the panorama shape is stable.

## 5) If timelapse outputs look wrong

### What to check
- Are the early frames blank because the input order is wrong?
- Does the final frame show the same geometry as the panorama?

### Recovery order
1. Confirm the input order.
2. Compare timelapse and final panorama sizes.
3. Use the verbose directory to find the first stage that diverged.

## 6) If GUI preview fails, treat it as an environment issue

### What to check
- Is the environment headless?
- Is the OpenCV build a headless build?

### Recovery order
1. Remove preview usage.
2. Install the headless package for server/container sessions.
3. If you need a window, move to a GUI-capable environment.

## Recommended next commands

- `python scripts/check_install.py` for install/import checks.
- `python scripts/download_sample_images.py --dest ./sample-images` when you
  need the public fixture set.
- `python sub-skills/diagnostics/scripts/inspect_verbose_dir.py --help` for a
  structure check on an existing verbose directory.
