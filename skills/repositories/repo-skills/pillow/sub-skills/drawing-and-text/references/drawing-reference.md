# Drawing Reference

## Drawing context and modes

`ImageDraw.Draw(im, mode=None)` returns a drawing object bound to `im` and mutates that image in place.

- Use the image's native mode for ordinary replacement drawing.
- On an RGB image, `ImageDraw.Draw(im, "RGBA")` blends RGBA fill values into the base pixels.
- On an RGBA image, drawing a semi-transparent color replaces the pixel with that exact RGBA value; draw onto a transparent overlay and alpha-composite when you want source-over blending.
- Set `draw.fontmode = "1"` for non-antialiased text or `"L"` for antialiased text. Embedded color glyph drawing internally uses RGBA masks.

## Coordinates and color

- Pillow coordinates start at `(0, 0)` in the top-left corner.
- Drawing outside image bounds is clipped, not wrapped.
- Shape boxes generally accept either `[(x0, y0), (x1, y1)]` or `(x0, y0, x1, y1)`.
- Rectangle-style bounding boxes include both endpoints.
- Fill colors follow image-mode rules: tuples for RGB/RGBA-like modes, integers for palette/index modes, and recognized color names or hex strings.

## Primitive calls

| Task | Call | Notes |
| --- | --- | --- |
| Points | `draw.point(xy, fill=None)` | Draw one or more pixels. |
| Lines | `draw.line(xy, fill=None, width=1, joint=None)` | `xy` can be tuples or a flat coordinate list; `joint="curve"` rounds joins for wider polylines. |
| Rectangles | `draw.rectangle(xy, fill=None, outline=None, width=1)` | `x1 >= x0`, `y1 >= y0`; outline width is in pixels. |
| Rounded rectangles | `draw.rounded_rectangle(xy, radius=0, fill=None, outline=None, width=1, corners=None)` | `corners=(tl, tr, br, bl)` can disable individual rounded corners. |
| Ellipses | `draw.ellipse(xy, fill=None, outline=None, width=1)` | Draws inside the bounding box. |
| Circles | `draw.circle(xy, radius, fill=None, outline=None, width=1)` | Center plus radius convenience wrapper. |
| Arcs | `draw.arc(xy, start, end, fill=None, width=1)` | Angles are degrees from 3 o'clock, increasing clockwise. |
| Chords | `draw.chord(xy, start, end, fill=None, outline=None, width=1)` | Arc plus straight line between endpoints. |
| Pieslices | `draw.pieslice(xy, start, end, fill=None, outline=None, width=1)` | Arc plus radial lines to center. |
| Polygons | `draw.polygon(xy, fill=None, outline=None, width=1)` | Outline closes from last point to first. |
| Regular polygons | `draw.regular_polygon(bounding_circle, n_sides, rotation=0, fill=None, outline=None, width=1)` | `bounding_circle` is `(x, y, radius)` or `((x, y), radius)`; `n_sides` must be an integer greater than 2. |
| Bitmaps | `draw.bitmap(xy, bitmap, fill=None)` | Bitmap must be a transparency mask-like image (`1`, `L`, or `RGBA`). |

## Reliable overlay pattern

For repeatable watermarks and badges, draw geometry and text onto an overlay with the same size as the base image, then composite:

```python
from PIL import Image, ImageDraw, ImageFont

base = Image.new("RGBA", (800, 450), "white")
overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)
font = ImageFont.load_default(size=28)

draw.rounded_rectangle((540, 360, 780, 430), radius=16, fill=(0, 0, 0, 144))
draw.text((760, 415), "Draft", font=font, anchor="rd", fill=(255, 255, 255, 230))
out = Image.alpha_composite(base, overlay)
```

This avoids the common surprise where direct drawing onto RGBA images replaces alpha rather than blending with existing pixels.

## Validation checklist

- Normalize user-provided boxes so `left <= right` and `top <= bottom` before calling shape methods.
- Clamp or reject coordinates if clipped output is not acceptable.
- Use `textbbox()` to reserve space for labels; do not assume text height equals font size.
- Convert to an alpha-capable mode (`RGBA` or overlay) before drawing translucent shapes.
- For palette images, consider converting to `RGB`/`RGBA` before drawing arbitrary color overlays.
