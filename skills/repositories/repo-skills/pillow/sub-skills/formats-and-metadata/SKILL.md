---
name: formats-and-metadata
description: "Use this Pillow sub-skill when an agent needs to open or save
  specific image formats, choose encoder options, preserve metadata, handle
  animated or multi-page images, or diagnose optional codec support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Pillow Formats and Metadata

Use this sub-skill for format I/O decisions: detecting input formats, selecting save formats and encoder options, preserving metadata, iterating multi-frame images, and checking whether the installed Pillow build has optional libraries such as JPEG, JPEG 2000, zlib, libtiff, WebP, AVIF, and LittleCMS.

## Decision Checklist

1. Open images by content with `Image.open(fp, mode="r", formats=None)`; do not trust filename extensions for input identification.
2. Save images by extension only when writing to a real filename; pass `format="PNG"`, `format="JPEG"`, etc. for file-like objects or extensionless paths.
3. Check feature availability before promising optional codecs: `features.check("webp")`, `features.check("avif")`, `features.check("jpg_2000")`, `features.check("libtiff")`, `features.check("littlecms2")`.
4. Preserve metadata explicitly: pass `icc_profile=im.info.get("icc_profile")`, `exif=im.getexif()` or `im.info.get("exif")`, `xmp=im.info.get("xmp")`, and format-specific options when saving.
5. For animations or multi-page files, iterate with `ImageSequence.Iterator(im)` and save with `save_all=True` plus `append_images=[...]`; otherwise many formats save only the first frame.
6. Re-check modes and alpha before saving: JPEG cannot store alpha, palette/transparency behavior is format-specific, and lossy formats may convert modes.

## Common Patterns

### Inspect Capabilities

Run the bundled report when behavior depends on optional libraries or registered extensions:

```bash
python sub-skills/formats-and-metadata/scripts/format_capability_report.py --json
```

Or in Python:

```python
from PIL import features
required = ["jpg", "zlib", "webp", "avif", "jpg_2000", "libtiff", "littlecms2"]
missing = [name for name in required if not features.check(name)]
```

Use `python -m PIL` for Pillow's verbose built-in report. Use `python -m PIL --report` when supported and a shorter report is enough.

### Open, Inspect, and Preserve Metadata

```python
from PIL import Image, ExifTags

with Image.open("input.jpg") as im:
    im.load()
    exif = im.getexif()
    orientation = exif.get(ExifTags.Base.Orientation)
    icc = im.info.get("icc_profile")
    im.convert("RGB").save("output.jpg", quality=90, exif=exif, icc_profile=icc)
```

After `copy()`, `convert()`, `resize()`, or many compositing operations, `format`, `fp`, and format-specific attributes may be absent. Carry needed `info`, EXIF, ICC, XMP, palette, duration, and loop values yourself.

### Save Multi-Frame Output

```python
from PIL import Image, ImageSequence

with Image.open("animation.gif") as im:
    frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(im)]
    durations = [frame.info.get("duration", im.info.get("duration", 0)) for frame in ImageSequence.Iterator(im)]

frames[0].save(
    "animation.webp",
    format="WEBP",
    save_all=True,
    append_images=frames[1:],
    duration=durations,
    loop=im.info.get("loop", 0),
    lossless=False,
    quality=85,
)
```

Keep the source image open while iterating lazy frames. Copy frames that must outlive the source file.

## Format Selection

- Use `PNG` for lossless RGB/RGBA, alpha, palettes, text chunks, ICC, and PNG EXIF; it needs zlib support.
- Use `JPEG` for lossy photos without alpha; convert `RGBA`/`LA`/`P` with transparency to `RGB` after choosing a background or dropping alpha intentionally.
- Use `GIF` for palette animation and broad compatibility; expect palette and mode changes across frames.
- Use `TIFF` for multi-page documents, high-bit-depth, tags, and archival workflows; compressed TIFF depends on libtiff.
- Use `WEBP` for modern lossy/lossless stills or animations with optional ICC/EXIF/XMP; behavior depends on libwebp.
- Use `AVIF` for compact modern stills/sequences; encoder choices and availability vary by libavif codecs.
- Use `JPEG2000` for JP2/J2K workflows; support depends on OpenJPEG and advanced options are strict.
- Use `PDF`/`EPS` for document outputs with limited image semantics; EPS rasterization may require Ghostscript.

## References

- [Format Reference](references/format-reference.md) covers supported format families and save options.
- [Metadata and Sequences](references/metadata-and-sequences.md) covers `Image.info`, EXIF, ICC, XMP, palettes, TIFF tags, and multi-frame handling.
- [Troubleshooting](references/troubleshooting.md) covers missing codecs, unsupported parameters, alpha/mode mismatches, and external dependencies.
