# Diagnostics Troubleshooting

## When to read this

Read this when you need to map an observed failure back to the likely stage in
`stitch` or `stitch_verbose`.

## Common failure surfaces

### The verbose directory is empty or missing expected files

**Cause**: the stitch never reached the stage that writes those files, or the
wrong output directory was inspected.

**Fix**:
- Confirm the exact `verbose_dir` value.
- Check whether the run failed before features, matching, warping, or cropping.
- Use `inspect_verbose_dir.py` to summarize the directory layout.

### The matches graph is sparse or disconnected

**Cause**: the overlap is weak, the detector is a poor fit, or the confidence
threshold is too strict.

**Fix**:
- Lower `confidence_threshold` or `match_conf`.
- Try a different detector.
- Confirm the image order and overlap.

### A panorama drops an image even though the stitch completes

**Cause**: the biggest connected component does not include every input.

**Fix**:
- Use the matches graph and feature visualizations.
- Lower the threshold if the graph is only slightly disconnected.
- If one image is truly unrelated, remove it from the input list.

### Mask diagnostics look wrong

**Cause**: masks are the wrong size, shape, or order.

**Fix**:
- Ensure the mask list length matches the image list.
- Ensure each mask has the exact same resolution as the corresponding image.
- Confirm the masks were built for the same image resize scale.

### Crop diagnostics look wrong

**Cause**: the panorama mask is irregular or too fragmented for the largest
interior rectangle step.

**Fix**:
- Retry with `--no-crop` / `crop=False`.
- Keep the seam and crop outputs for later comparison.

### Timelapse diagnostics look inconsistent

**Cause**: the input order or scaling differs from the final panorama stage.

**Fix**:
- Compare the first and last frames to the final panorama.
- Re-check input ordering and any custom settings.

## Helper next step

Use `sub-skills/diagnostics/scripts/inspect_verbose_dir.py` to report which
expected verbose files are present and which stage is probably missing.
