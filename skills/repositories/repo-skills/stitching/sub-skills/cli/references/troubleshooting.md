# CLI Troubleshooting

## When to read this

Read this when a `stitch` command parses but the run does not behave as
expected.

## Common symptoms

### The command says files are missing

**Likely cause**: the glob matches nothing or a path is wrong.

**Fix**:
- Expand the glob yourself or use the validator helper.
- Confirm the files exist before stitching.

### The CLI rejects feature masks

**Likely cause**: the number of masks does not match the number of images, or a
mask resolution does not match its image.

**Fix**:
- Run `python scripts/validate_cli_args.py -- stitch ...` to check counts.
- Recreate the masks at the exact image dimensions.

### The panorama is missing one or more images

**Likely cause**: the confidence threshold is too high, the detector is too
weak for the image content, or the image ordering is poor.

**Fix**:
- Lower `--confidence_threshold`.
- Try `--detector sift` or another detector choice.
- Use `--matches_graph_dot_file` and `--verbose` to inspect the matches.

### `--preview` hangs or fails

**Likely cause**: there is no GUI display.

**Fix**:
- Remove `--preview`.
- Use the headless package if you are running on a server or in Docker.

### Crop fails after warping

**Likely cause**: the resulting mask does not have a clean valid contour for the
largest-interior-rectangle step.

**Fix**:
- Retry with `--no-crop`.
- Keep the verbose outputs so you can inspect the seam and crop stages.

### `--try_use_gpu` has no visible effect

**Likely cause**: the installed OpenCV build is CPU-only.

**Fix**:
- Treat the flag as optional.
- Do not assume GPU support unless you installed a CUDA-enabled OpenCV build.

## Next checks

- Use [CLI reference](cli-reference.md) to confirm the exact flag spelling.
- Use [Workflow recipes](workflows.md) for a copyable command.
- Use the root [diagnostics](../../diagnostics/SKILL.md) sub-skill when the
  issue is about dropped images or verbose output interpretation.
