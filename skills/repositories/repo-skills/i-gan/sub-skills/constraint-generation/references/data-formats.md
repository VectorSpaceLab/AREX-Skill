# Constraint data formats

Use this reference to prepare and inspect the three image inputs accepted by iGAN's headless constrained generation workflow.

## Required triplet

The workflow consumes exactly three image paths:

| Role | CLI flag | Meaning | Preferred header |
| --- | --- | --- | --- |
| Color image | `--input_color` | Desired RGB colors in constrained regions | 8-bit RGB PNG |
| Color mask | `--input_color_mask` | Where color constraints apply | 8-bit grayscale PNG |
| Edge image | `--input_edge` | Desired edge/sketch structure and edge mask source | 8-bit RGB or grayscale PNG |

The documented sample contract uses 64 by 64 images. The native script will resize images to the loaded model's image size, but matching the model size before execution is safer and more reproducible.

## Channel behavior

The native script reads every input with OpenCV's color image mode. This has important effects:

- A grayscale mask file is expanded to a 3-channel array by OpenCV.
- The color mask passed to the optimizer is the first channel of that expanded mask.
- The edge image is passed as a color image.
- The edge mask passed to the optimizer is the first channel of the edge image.
- The color image is converted from OpenCV BGR order to RGB before optimization.

Because the mask and edge-mask logic uses the first channel, avoid multicolor masks unless the first channel is intentionally meaningful.

## Pixel value semantics

- Pixel values are expected in the normal image range `[0, 255]`.
- Mask values are normalized to `[0, 1]` by dividing by 255.
- Black mask pixels mean little or no constraint at that location.
- White mask pixels mean full constraint at that location.
- Gray mask pixels act as soft weights.
- Sparse color masks are usually easier for the generator than fully white masks.
- Sparse edge masks usually represent user sketches.
- Empty masks can make optimization appear to ignore an input image.

The bundled validator performs header and dimension checks only. It does not decode pixels or prove that masks are binary.

## Dimensions

Recommended rules:

1. Make all three images the same width and height.
2. Match the model resolution when known.
3. Use square images for the documented model family.
4. Keep the color, mask, and edge coordinate systems aligned.
5. Avoid relying on the native script's independent resizing to repair mismatched inputs.

The native script resizes each input independently to `npx`. If one input starts from a different aspect ratio, OpenCV resize will still force it to a square, which can shift constraints relative to the other images. Treat such mismatches as likely user error unless explicitly intended.

## Preferred safe validation

Run:

```bash
python scripts/validate_constraint_inputs.py \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --target-size 64
```

Use strict size mode if the user's workflow requires exact model-size images:

```bash
python scripts/validate_constraint_inputs.py \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --target-size 64 \
  --strict-size
```

Use JSON output for automated checks:

```bash
python scripts/validate_constraint_inputs.py \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --target-size 64 \
  --json
```

## Header families accepted by the validator

The validator is intentionally lightweight and avoids OpenCV. It can inspect:

- PNG dimensions, bit depth, and color type,
- JPEG dimensions and channel family from SOF markers,
- BMP dimensions and approximate channel depth,
- GIF dimensions for coarse checks.

If the validator reports an unsupported header, the file may still be readable by OpenCV, but the safe preflight could not prove it. Prefer converting the file to PNG before a native run.

## Color image checklist

- File exists and is readable.
- Header reports a color format, preferably RGB.
- Width and height match the mask and edge images.
- Width and height match the target model size or the user accepts resizing.
- The visible content contains only the intended color constraints, not unrelated annotations.
- If large white/black background regions are present, the mask should prevent them from over-constraining the generator.

## Color mask checklist

- File exists and is readable.
- Header is preferably grayscale.
- Dimensions match the color and edge images.
- Nonzero pixels align with intended color strokes or regions.
- The first channel is the mask channel when a color file is used.
- Binary black/white masks are preferred for reproducibility.
- Soft gray masks are acceptable when the user intentionally wants weighted constraints.

## Edge image checklist

- File exists and is readable.
- Header is grayscale or RGB.
- Dimensions match the color image and color mask.
- Edge strokes are high contrast.
- The first channel is nonzero where edge constraints should apply.
- If the edge image is blank or all white, it may provide little useful structure.
- If using a sketch-oriented model, confirm the model-inference sub-skill's model choice before execution.

## Output file expectations

The native script writes one visualization image to `--output_result`. It does not write separate candidate files or latent vectors. The visualization is a horizontal strip containing the three input panels followed by candidate panels.

If separate candidates, latent vectors, or intermediate optimization traces are needed, that is an extension task, not the documented headless script behavior.

## Common input mistakes

| Symptom | Likely data issue | Fix |
| --- | --- | --- |
| Validator says a path is missing | Wrong working directory or typo | Use explicit paths or run from the intended checkout/work directory |
| Validator says dimensions differ | Mixed files from different examples or edited canvas sizes | Resize all three images together from the same source canvas |
| Validator warns target size differs | Image is not the model's native size | Resize to model size or accept the native script's resizing |
| Native output ignores colors | Color mask is empty or wrong first channel | Inspect the mask and ensure constrained regions are nonzero |
| Native output ignores edges | Edge first channel is empty or low contrast | Convert sketches to high-contrast grayscale/RGB before execution |
| Native output looks globally tinted | Color mask is too broad | Restrict the mask to intended regions |
| Native output strip is very wide | Large `top_k` | Reduce `top_k` or post-process generated candidates separately |
