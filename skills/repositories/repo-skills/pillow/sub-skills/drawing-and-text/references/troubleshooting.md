# Drawing and Text Troubleshooting

## `OSError: cannot open resource` for fonts

Cause: `ImageFont.truetype()` could not read the requested font path/name, or too many font files are open on Windows.

Fixes:

- Pass an explicit existing `.ttf`/`.otf` path from the application environment.
- Catch `OSError` and fall back to `ImageFont.load_default(size=...)`.
- On Windows, avoid holding hundreds of live `FreeTypeFont` objects; load font bytes into memory if necessary.

## FreeType is unavailable

Symptoms: `features.check_module("freetype2")` is false, TrueType loading fails, default font has limited metrics/glyph support, and anchors may be ignored by bitmap fonts.

Fixes:

- Use `ImageFont.load_default()` as a minimal fallback.
- Avoid exact anchor-dependent layout unless a `FreeTypeFont` is available.
- Treat complex text and color fonts as unsupported in that environment.

## libraqm is unavailable

Symptoms: `features.check_feature("raqm")` is false, complex scripts do not shape as expected, `direction`, OpenType `features`, or `language` do not produce desired output.

Fixes:

- Gate advanced layout options:

```python
kwargs = {}
if features.check_feature("raqm"):
    kwargs.update(direction="rtl", language="ar", features=["-kern"])
draw.text((x, y), text, font=font, **kwargs)
```

- Fall back to `ImageFont.Layout.BASIC` and warn that bidirectional/Arabic/Indic shaping may be degraded.
- Do not compare pixel-perfect output across BASIC and RAQM layout engines.

## Invalid anchors raise `ValueError`

Common invalid examples include empty strings, one-character strings, three-character strings, and unsupported combinations such as `"sa"`, `"xa"`, or `"lx"` for horizontal text. Vertical `direction="ttb"` has different valid combinations; horizontal anchors such as `"la"`, `"ls"`, and `"ld"` are invalid for vertical text.

Fixes:

- Require two-character anchors.
- For horizontal text, prefer stable anchors such as `"la"`, `"ma"`, `"ra"`, `"lm"`, `"mm"`, `"rm"`, `"ls"`, `"ms"`, `"rs"`, `"ld"`, `"md"`, and `"rd"`.
- For horizontal multiline text, avoid `"lt"` and `"lb"`; use `"la"`, `"lm"`, `"ls"`, or `"ld"` families.
- Validate by calling `draw.textbbox(xy, text, font=font, anchor=anchor, ...)` before drawing.

## Text is clipped despite using an anchor

Cause: anchor placement controls where the text is positioned relative to `xy`; it does not guarantee the resulting box fits inside the image.

Fix:

```python
bbox = draw.textbbox(xy, text, font=font, anchor=anchor, stroke_width=stroke_width)
if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > im.width or bbox[3] > im.height:
    raise ValueError(f"text outside image: {bbox}")
```

For multiline strings, use `multiline_textbbox()` or `textbbox()` with the same multiline options because `text()` delegates newline strings to multiline handling.

## `textlength()` disagrees with visible width

Cause: `textlength()` reports advance, not the visible pixel bounding box. Italics, accents, bearings, strokes, and kerning can extend pixels beyond the advance or change combined run lengths.

Fixes:

- Use `textbbox()` for clipping, background rectangles, hit boxes, and watermark validation.
- Use `textlength()` for cursor advance or placing the next run on the baseline.
- Account for kerning by measuring with the following character and subtracting it, or disable kerning with `features=["-kern"]` when RAQM is available.

## Alpha or fill looks wrong

Symptoms: semi-transparent fill fully replaces pixels on RGBA images, or alpha is ignored on RGB images.

Cause and fixes:

- Direct drawing on RGBA replaces the target pixel with the supplied RGBA value.
- Direct drawing on RGB ignores the alpha component unless the draw object was created with `ImageDraw.Draw(im, "RGBA")`.
- For predictable source-over compositing, draw on a transparent RGBA overlay and call `Image.alpha_composite(base, overlay)`.

## Embedded color glyphs fail

Symptoms: `ValueError: Embedded color supported only in RGB and RGBA modes`, monochrome emoji, or missing glyph boxes.

Fixes:

- Convert or create the target image in `RGB` or `RGBA` before `embedded_color=True`.
- Use a font that contains color glyph tables for the requested characters.
- Keep a monochrome fallback path with `embedded_color=False`.

## `ValueError` for very long text

Pillow protects font rendering from denial-of-service inputs with `ImageFont.MAX_STRING_LENGTH`.

Fixes:

- Validate and limit untrusted text before rendering.
- Chunk or wrap trusted long strings intentionally.
- Do not disable `ImageFont.MAX_STRING_LENGTH` for user-provided text.

## Multiline alignment is not anchor alignment

`align="left|center|right|justify"` aligns individual lines within the multiline block. `anchor` positions the whole block relative to `xy`.

Fix: choose `anchor` for overall placement first, then use `align` only for internal line alignment.
