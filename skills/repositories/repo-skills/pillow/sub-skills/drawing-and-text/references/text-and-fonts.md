# Text and Fonts Reference

## Font loading

```python
from PIL import ImageFont, features

if not features.check_module("freetype2"):
    font = ImageFont.load_default()
else:
    try:
        font = ImageFont.truetype("NotoSans-Regular.ttf", 32)
    except OSError:
        font = ImageFont.load_default(size=32)
```

- `ImageFont.truetype(font, size=10, index=0, encoding="", layout_engine=None)` loads TrueType/OpenType and other FreeType-supported fonts.
- It raises `OSError` if the font cannot be opened and `ValueError` if the size is not greater than zero.
- On Linux/macOS/Windows, Pillow may search common system font directories when given a font name, but production code should pass an explicit font path or package the chosen font outside the public skill.
- `ImageFont.load_default(size=None)` is the safest fallback. With FreeType, it returns a bundled Aileron-based font; without FreeType, it returns a limited bitmap font.
- `font.font_variant(size=..., index=..., layout_engine=...)` creates another `FreeTypeFont` variant without reopening selection logic.

## Layout engines and feature checks

```python
layout = ImageFont.Layout.RAQM if features.check_feature("raqm") else ImageFont.Layout.BASIC
font = ImageFont.truetype("NotoSans-Regular.ttf", 32, layout_engine=layout)
```

- `ImageFont.Layout.RAQM` enables complex shaping through libraqm; it is recommended for non-English, bidirectional, and vertical text.
- `ImageFont.Layout.BASIC` is faster and works without libraqm, but it does not provide the same shaping behavior.
- Check `features.check_feature("raqm")` before passing `direction`, `features`, or `language` in user-facing code.
- `direction` can be `"ltr"`, `"rtl"`, or `"ttb"`; top-to-bottom vertical layout may require a recent libraqm build.
- `features` accepts OpenType tags such as `"dlig"`, `"ss01"`, `"-liga"`, and `"-kern"`.
- `language` should be a BCP 47 language code such as `"ar"`, `"sr"`, or `"ja"`.

## Drawing text

```python
draw.text(
    (320, 180),
    "Hello",
    font=font,
    anchor="mm",
    fill="white",
    stroke_width=2,
    stroke_fill="black",
)
```

Important parameters on `draw.text()` and `draw.multiline_text()`:

- `xy`: anchor coordinates, not necessarily the top-left corner.
- `font`: an `ImageFont` or `FreeTypeFont`; if omitted, Pillow uses the default font and optional `font_size`.
- `anchor`: two-character alignment string for TrueType/OpenType fonts.
- `spacing`: pixel spacing between multiline text lines.
- `align`: `"left"`, `"center"`, `"right"`, or `"justify"` for multiline line alignment.
- `stroke_width` and `stroke_fill`: draw outlined text; `stroke_fill` defaults to `fill`.
- `embedded_color=True`: render COLR/CBDT/SBIX color glyphs when the font and mode support them.

## Anchor guide

Anchor strings contain a horizontal character and a vertical character.

Horizontal characters:

- `l`: left of horizontal text.
- `m`: horizontally centered.
- `r`: right of horizontal text.
- `s`: baseline alignment for vertical text.

Vertical characters:

- `a`: ascender/top for horizontal text; stable for mixed glyphs.
- `t`: top; for horizontal text, use mainly with single-line labels.
- `m`: vertical middle.
- `s`: baseline for horizontal text.
- `b`: bottom; for horizontal text, use mainly with single-line labels.
- `d`: descender/bottom for horizontal text; stable for mixed glyphs.

Defaults:

- Horizontal text: `anchor=None` behaves like `"la"`.
- Vertical `direction="ttb"`: `anchor=None` behaves like `"lt"`.

Validation rules to remember:

- Anchor must be a two-character string.
- Invalid combinations raise `ValueError` from font measurement or drawing.
- Horizontal multiline text rejects `t` and `b` as the vertical anchor component; use `a`, `m`, `s`, or `d` instead.
- Bitmap/default fonts may ignore anchors; validate with `textbbox()` if exact placement matters.

## Measurement and clipping

```python
bbox = draw.textbbox((x, y), text, font=font, anchor="mm", stroke_width=2)
left, top, right, bottom = bbox
visible_width = right - left
advance = draw.textlength(text, font=font)
```

- `textbbox()` and `multiline_textbbox()` return visible pixel extents plus stroke margins.
- `textlength()` returns the advance distance with 1/64 pixel precision; it is not the same as visible width.
- Kerning means `textlength("Hello") + textlength("World")` may not equal `textlength("HelloWorld")`.
- To combine measured runs, measure with the following character and subtract it, or disable kerning with `features=["-kern"]` when libraqm is available.
- `textlength()` cannot measure multiline strings; use `multiline_textbbox()` for newlines.

## `ImageText.Text` helper

`ImageText.Text` bundles text, font, mode, layout options, embedded color, stroke, wrapping, measurement, and drawing state.

```python
from PIL import ImageText

label = ImageText.Text("Hello world", font, mode="RGBA", direction="ltr")
label.stroke(2, "black")
box = label.get_bbox((100, 100), anchor="mm")
draw.text((100, 100), label, fill="white", anchor="mm")
```

Use it when multiple operations must share identical layout settings. `Text.wrap(width, height=None, scaling=None)` supports left-to-right text only; it raises for transposed fonts and non-LTR directions.

## Embedded color glyphs

```python
if im.mode not in ("RGB", "RGBA"):
    im = im.convert("RGBA")
draw = ImageDraw.Draw(im)
draw.text((20, 20), "🙂", font=color_font, embedded_color=True)
```

- Embedded color rendering only supports RGB and RGBA modes.
- If `embedded_color=True` is used in modes such as `L`, `P`, `I`, or `F`, Pillow raises `ValueError`.
- The font must actually contain embedded color glyph tables; otherwise output may look like ordinary monochrome glyphs or missing-glyph boxes.
