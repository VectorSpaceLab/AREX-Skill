---
name: pillow
description: "Use this repo skill when working with Pillow (PIL fork) image
  processing: opening/saving images, transforms, formats, metadata,
  drawing/text, fonts, and custom image plugins."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Pillow

Use this skill when an agent needs to write, debug, or explain Pillow code for image processing in Python. Pillow imports as `PIL` and centers on `PIL.Image.Image` objects created by `Image.open()` or `Image.new()`.

## Quick Start

```python
from PIL import Image, ImageOps

with Image.open("input.jpg") as im:
    im = ImageOps.exif_transpose(im)
    out = ImageOps.contain(im.convert("RGB"), (1024, 1024))
    out.save("output.jpg", quality=90)
```

Minimal import and feature check:

```python
from PIL import Image, features
print(Image.__version__)
print(features.check("jpg"), features.check("zlib"), features.check("webp"))
```

Use `python -m PIL` for Pillow's installed feature report. Run [`scripts/pillow_smoke_check.py`](scripts/pillow_smoke_check.py) when you need a safe in-memory check of imports, feature flags, open/save, drawing, and format registration.

## Route by Task

| User request | Go to |
| --- | --- |
| Open images, inspect size/mode, crop, paste, resize, thumbnail, convert modes, preserve alpha, composite, filter, enhance, use `BytesIO` | [`image-core`](sub-skills/image-core/SKILL.md) |
| Choose PNG/JPEG/GIF/TIFF/WebP/AVIF/JPEG2000/PDF/EPS behavior, preserve EXIF/ICC/XMP, handle animations or multi-page files, check codecs | [`formats-and-metadata`](sub-skills/formats-and-metadata/SKILL.md) |
| Draw lines/shapes, render text, use anchors, fonts, strokes, multiline layout, direction/language/OpenType features, watermarks | [`drawing-and-text`](sub-skills/drawing-and-text/SKILL.md) |
| Write or debug a custom `ImagePlugin`, register formats/extensions, inspect `PIL.features`, use `python -m PIL` plugin reports | [`plugins-and-extension`](sub-skills/plugins-and-extension/SKILL.md) |

## Shared References

- [`references/installation-and-features.md`](references/installation-and-features.md) explains public installation choices, source-build libraries, optional features, and feature-report commands.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install/import/build, codec, file lifecycle, and API misuse failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) records the repository snapshot and evidence baseline used to generate this skill.

## General Decision Rules

- Use `Image.open(fp, mode="r", formats=None)` for input; it identifies images from file contents and reads image data lazily.
- Keep source files open until the image is loaded, copied, or all lazy frame access is complete.
- Pass `format="PNG"`, `format="JPEG"`, etc. when saving to file-like objects or extensionless paths.
- Carry metadata explicitly across transforms: EXIF, ICC, XMP, palettes, durations, loops, and TIFF tags do not automatically survive every copy/convert/resize path.
- Convert modes intentionally before saving: JPEG cannot store alpha, palette transparency is format-specific, and many operations are simpler in `RGB` or `RGBA`.
- Check optional features before promising a codec or text-layout behavior; compiled libraries vary across Pillow builds.

## Useful Bundled Scripts

- [`scripts/pillow_smoke_check.py`](scripts/pillow_smoke_check.py): safe in-memory sanity check for installed Pillow.
- [`sub-skills/image-core/scripts/inspect_image.py`](sub-skills/image-core/scripts/inspect_image.py): inspect an input image and optionally write a thumbnail.
- [`sub-skills/formats-and-metadata/scripts/format_capability_report.py`](sub-skills/formats-and-metadata/scripts/format_capability_report.py): report feature and registered-format support.
- [`sub-skills/drawing-and-text/scripts/render_text_anchor_grid.py`](sub-skills/drawing-and-text/scripts/render_text_anchor_grid.py): render a text-anchor grid for the current installation.
- [`sub-skills/plugins-and-extension/scripts/minimal_spam_plugin.py`](sub-skills/plugins-and-extension/scripts/minimal_spam_plugin.py): self-test a minimal custom Pillow plugin.

## When to Be Careful

- `Image.open()` can raise `UnidentifiedImageError` or `OSError`; do not catch every exception silently unless scanning many files.
- Large or hostile files can trigger `DecompressionBombWarning` or `DecompressionBombError`; set policy before batch processing untrusted inputs.
- `thumbnail()` mutates in place; `resize()`, `ImageOps.contain()`, `ImageOps.fit()`, and `ImageOps.pad()` return new images.
- Boxes are `(left, upper, right, lower)` with right/lower exclusive. Validate geometry before `crop()` and `paste()`.
- `direction`, OpenType `features`, and `language` in text rendering need libraqm support; provide fallbacks when unavailable.
- Custom plugins must be imported before `Image.open()` can dispatch to them.
