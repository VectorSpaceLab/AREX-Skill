# Image Preprocessing and Input Quality

## Accepted Inputs

Use local PNG/JPEG-style equation images or clipboard images. The model works
best on tightly cropped equation images at moderate resolution. Very large or
heavily zoomed screenshots can degrade predictions.

## What pix2tex Does Before Inference

1. Converts the input image through `pad()` into a normalized single-channel
   representation.
2. Crops to non-background pixels and pads dimensions to a multiple of 32.
3. Applies max/min dimension constraints from the model config.
4. Optionally uses an auxiliary ResNet image-resizer model to choose a better
   width before final transformation.
5. Generates a token sequence and decodes it into a LaTeX string.

## Practical Guidance

- Crop to the equation, not the surrounding page.
- Prefer high contrast black-on-white or white-on-black equations.
- Avoid tiny captures; the GUI upsamples images below roughly 100 pixels in a
  dimension before prediction.
- If output is close but unstable, lower temperature or retry with a slightly
  different crop/resolution.
- Use `--no-resize` when the auxiliary resizer appears to distort unusual input
  shapes.

## Validation Helper

Run:

```bash
python scripts/inspect_pix2tex_image.py path/to/equation.png --pad-preview
```

The helper reports image mode, dimensions, bounding-box/padding behavior, and
possible quality warnings without loading OCR weights.
