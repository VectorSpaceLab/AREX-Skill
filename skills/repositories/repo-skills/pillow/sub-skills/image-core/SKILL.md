---
name: image-core
description: "Create, open, inspect, transform, composite, resize, crop,
  convert, enhance, filter, and validate ordinary Pillow Image workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Image Core

Use this sub-skill when an agent needs day-to-day `PIL.Image.Image` workflows: construct or open images, inspect dimensions and modes, crop/paste/resize/thumbnail, convert modes, preserve alpha, composite layers, apply core `ImageOps`, `ImageChops`, `ImageEnhance`, `ImageFilter`, and compute basic `ImageStat` metrics.

## Route Here

- Open files or file-like objects with `Image.open()`, understand lazy loading, and safely copy or load images before closing files.
- Create new images with `Image.new()`, use pixel boxes and Pillow's coordinate conventions, and debug crop/paste geometry.
- Resize, thumbnail, contain, cover, fit, pad, transpose, rotate, filter, enhance, compare, composite, and validate ordinary single-image pipelines.
- Handle `BytesIO` input/output, basic `save()` calls, decompression-bomb guardrails, and common errors like `UnidentifiedImageError` or invalid crop boxes.

## Route Elsewhere

- Format-specific encoder options, EXIF/XMP/ICC metadata, multi-frame GIF/TIFF/WebP, animation, or orientation metadata policy: use [`formats-and-metadata`](../formats-and-metadata/SKILL.md).
- Drawing primitives, text, fonts, anchors, shaping, strokes, or embedded-color glyphs: use [`drawing-and-text`](../drawing-and-text/SKILL.md).
- Custom file handlers, plugin registration, decoders, encoders, or extension hooks: use [`plugins-and-extension`](../plugins-and-extension/SKILL.md).

## Primary References

- [`references/api-reference.md`](references/api-reference.md) summarizes the core API surface, signatures, modes, coordinate boxes, and module roles.
- [`references/workflows.md`](references/workflows.md) gives copy-pasteable image pipelines for open/inspect, crop/paste, alpha-preserving logos, resizing, filtering, and `BytesIO`.
- [`references/troubleshooting.md`](references/troubleshooting.md) maps common failures to fixes and guardrails.
- [`scripts/inspect_image.py`](scripts/inspect_image.py) is a small installed-Pillow-only helper for identifying images and optionally writing thumbnails.

## Fast Patterns

```python
from PIL import Image, ImageOps

with Image.open(input_path) as im:
    im = ImageOps.exif_transpose(im)  # if metadata-aware orientation is desired
    work = im.convert("RGBA")
    thumb = ImageOps.contain(work, (512, 512))
    thumb.save(output_path, format="PNG")
```

```python
from PIL import Image

base = Image.new("RGBA", (400, 300), (255, 255, 255, 0))
logo = Image.open(logo_path).convert("RGBA")
base.alpha_composite(logo, dest=(20, 20))
base.save(output_path, "PNG")
```

## Decision Checklist

- Keep source files open until `load()`, `copy()`, or all needed pixel operations are complete; `Image.open()` reads headers lazily.
- Treat boxes as `(left, upper, right, lower)` with right/lower exclusive; validate `right > left`, `lower > upper`, and expected size before `paste()`.
- Use `thumbnail()` only when in-place mutation is wanted; use `resize()`, `ImageOps.contain()`, `fit()`, or `pad()` when a new image is clearer.
- Preserve transparency by converting to `RGBA` before resizing, filtering, or compositing; flatten intentionally before saving to formats without alpha.
- Choose resampling deliberately: `NEAREST` for masks/pixel art, `BICUBIC` as a balanced default, `LANCZOS` for high-quality downscaling.
