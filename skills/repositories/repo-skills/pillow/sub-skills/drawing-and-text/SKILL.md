---
name: drawing-and-text
description: "Draw primitives, text overlays, anchors, fonts, strokes, embedded
  color glyphs, and complex text layout on Pillow images."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Drawing and Text

Use this sub-skill when an agent needs to annotate or generate Pillow images with vector-like primitives, text, font metrics, anchored placement, strokes, or multilingual shaping.

## Start with the drawing context

```python
from PIL import Image, ImageDraw, ImageFont, features

im = Image.new("RGBA", (640, 360), "white")
draw = ImageDraw.Draw(im)
# For translucent overlays on RGB images, use ImageDraw.Draw(rgb_image, "RGBA").
```

- `ImageDraw.Draw(image, mode=None)` mutates the image in place.
- Coordinates use Pillow's top-left origin; drawing outside image bounds is clipped.
- Colors accept mode-appropriate tuples, integers, or color names; palette images use palette indexes unless Pillow can allocate RGB colors.
- For RGB bases with semi-transparent fills, pass `mode="RGBA"` to `ImageDraw.Draw`; for true RGBA compositing, draw on a transparent overlay and combine with `Image.alpha_composite` or `paste(..., mask=...)`.

## Draw primitives

Use `references/drawing-reference.md` for shape details. Common calls:

```python
draw.line([(20, 20), (120, 80), (220, 20)], fill="navy", width=6, joint="curve")
draw.rectangle((30, 120, 230, 210), fill=(255, 255, 0, 80), outline="black", width=3)
draw.rounded_rectangle((260, 120, 460, 210), radius=18, fill="#eef", outline="#36c", width=3)
draw.ellipse((500, 120, 600, 220), fill="tomato", outline="maroon", width=2)
draw.regular_polygon((540, 280, 48), n_sides=5, rotation=-18, fill="#ffc", outline="#960")
```

Validate bounding boxes before drawing: rectangle-like calls expect `x1 >= x0` and `y1 >= y0`; Pillow raises `ValueError` for invalid rounded rectangles and invalid regular polygon arguments.

## Load fonts safely

Use explicit TrueType/OpenType files when reproducible rendering matters:

```python
try:
    font = ImageFont.truetype("Inter-Regular.ttf", size=36)
except OSError:
    font = ImageFont.load_default(size=36)
```

- `ImageFont.truetype(font, size=10, index=0, encoding="", layout_engine=None)` needs FreeType and raises `OSError` for unreadable fonts or `ValueError` for invalid sizes.
- `ImageFont.load_default(size=...)` uses a bundled FreeType-backed default when FreeType is available; otherwise it falls back to a limited bitmap font.
- Check capabilities with `features.check_module("freetype2")` and `features.check_feature("raqm")` before relying on advanced fonts or shaping.
- See `references/text-and-fonts.md` for layout engines, measurement, anchors, and `ImageText.Text`.

## Place and validate text

Prefer anchor-based placement plus bounding-box validation over hand-tuned offsets:

```python
xy = (im.width - 24, im.height - 24)
text = "© Example"
font = ImageFont.load_default(size=24)
bbox = draw.textbbox(xy, text, font=font, anchor="rd", stroke_width=2)
if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > im.width or bbox[3] > im.height:
    raise ValueError(f"text would be clipped: {bbox}")
draw.text(xy, text, font=font, anchor="rd", fill="white", stroke_width=2, stroke_fill="black")
```

- Horizontal text defaults to anchor `la`; vertical `direction="ttb"` defaults to `lt`.
- Anchor strings are two characters. Horizontal anchors commonly use `l/m/r` plus `a/t/m/s/b/d`; multiline horizontal text does not support `t` or `b` vertical anchors.
- `textbbox()` and `multiline_textbbox()` return pixel boxes `(left, top, right, bottom)`; `textlength()` returns the advance length and may differ from visible pixels because of bearings, accents, italics, or kerning.
- Use `multiline_text(..., spacing=4, align="left|center|right|justify")` for multiline placement; `text()` delegates to multiline handling when text contains newlines.

## Use complex layout only when supported

```python
layout_engine = ImageFont.Layout.RAQM if features.check_feature("raqm") else ImageFont.Layout.BASIC
font = ImageFont.truetype("NotoSans-Regular.ttf", 32, layout_engine=layout_engine)
kwargs = {"direction": "rtl", "language": "ar"} if features.check_feature("raqm") else {}
draw.text((320, 100), "English عربي", font=font, anchor="mm", fill="black", **kwargs)
```

- `direction="rtl"`, `direction="ltr"`, `direction="ttb"`, OpenType `features=[...]`, and `language="..."` require libraqm for correct shaping.
- When libraqm is unavailable, omit direction/features/language or use `ImageFont.Layout.BASIC` and document the fallback quality.
- Embedded color glyphs use `embedded_color=True` and require RGB or RGBA drawing modes; otherwise Pillow raises `ValueError`.

## Bundled helper

Run the anchor-grid helper to verify anchor behavior in the current Pillow installation:

```bash
python sub-skills/drawing-and-text/scripts/render_text_anchor_grid.py anchor-grid.png --text "Anchor"
```

The script is self-contained, uses installed Pillow only, supports `--help`, optional `--font`, `--font-size`, and validates anchor placement with `textbbox()` before saving.

## Troubleshooting

Use `references/troubleshooting.md` for failures around missing fonts, missing FreeType, missing libraqm, invalid anchors, bbox/advance confusion, alpha surprises, and embedded color mode errors.

## Boundary reminders

- Use the root `image-core` guidance for resizing, cropping, compositing strategy, and generic transforms.
- Use `formats-and-metadata` for save options, metadata, color profiles, and file-format behavior.
- Use `plugins-and-extension` for custom decoders, plugins, and format registration.
