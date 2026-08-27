# Image Core Troubleshooting

## `UnidentifiedImageError` or `OSError` While Opening

Symptoms:

- `PIL.UnidentifiedImageError: cannot identify image file ...`
- `OSError` for truncated, unsupported, unreadable, or invalid input.

Fixes:

- Open files in binary mode when using file objects: `open(path, "rb")`.
- Ensure a `BytesIO` stream contains complete image bytes and is positioned at the start.
- Catch both `UnidentifiedImageError` and `OSError` in batch-identification tools.
- Use `python -m PIL --report` or the root skill's feature guidance if a format unexpectedly lacks decoder support.
- Keep format-specific recovery, encoder flags, and metadata handling in the formats-and-metadata sub-skill.

## Lazy Loading and Closed Files

`Image.open()` is lazy: it reads headers immediately but delays pixel decoding until `load()`, `copy()`, `save()`, or a pixel operation needs data.

Good patterns:

```python
with Image.open(path) as im:
    work = im.copy()

with Image.open(path) as im:
    im.load()
    mode, size = im.mode, im.size
```

Avoid returning an unopened/lazy image from a closed file context unless it has been copied or loaded. Reopen after `verify()` because `verify()` is a terminal validation operation for that image object.

## `DecompressionBombWarning` or `DecompressionBombError`

Pillow protects callers from images that decompress to huge pixel counts.

- Warning occurs above `Image.MAX_IMAGE_PIXELS`.
- Error occurs above twice that limit.
- Treat warnings as errors for untrusted uploads:

```python
import warnings
from PIL import Image

warnings.simplefilter("error", Image.DecompressionBombWarning)
with Image.open(path) as im:
    im.load()
```

Only disable or raise the limit for trusted, expected large rasters, and do it close to the code that needs it.

## Invalid Crop or Paste Boxes

Pillow boxes are `(left, upper, right, lower)`, not `(x, y, width, height)`. The `right` and `lower` values are exclusive pixel boundaries.

Common mistakes:

- `right <= left` or `lower <= upper` creates an invalid or empty region.
- Passing `(x, y, width, height)` crops the wrong rectangle.
- Pasting with a 4-tuple box whose dimensions do not match the pasted image raises a size mismatch error.
- Expecting the lower/right coordinates to include the final pixel causes off-by-one output.

Debug pattern:

```python
def box_size(box):
    left, upper, right, lower = box
    if right <= left or lower <= upper:
        raise ValueError(f"invalid box: {box}")
    return right - left, lower - upper
```

## Mode Conversion Errors or Surprising Colors

Symptoms:

- Operation works on `RGB` but fails on `P`, `I;16`, `F`, `CMYK`, or alpha modes.
- Palette transparency is lost.
- JPEG output fails because the image is `RGBA`.

Fixes:

- Convert explicitly for the operation: `im.convert("RGB")`, `im.convert("RGBA")`, or `im.convert("L")`.
- For palette images with transparency, prefer `im.convert("RGBA")` before resizing or compositing.
- Flatten alpha intentionally before saving to formats without alpha:

```python
rgba = im.convert("RGBA")
background = Image.new("RGB", rgba.size, "white")
background.paste(rgba, mask=rgba.getchannel("A"))
```

- Use `ImageOps.grayscale()` or `convert("L")` before grayscale statistics or mask workflows.

## Alpha and Palette Handling

Use alpha-aware methods when transparency matters:

- `base.alpha_composite(overlay, dest=(x, y))` for `RGBA` overlays.
- `base.paste(overlay, box, mask=overlay.getchannel("A"))` when using `paste()`.
- Convert `P` images to `RGBA` before resizing if they carry transparency.

Avoid compositing by blindly converting to `RGB`; that discards alpha and can leave black or jagged transparent edges.

## Resampling Quality and Performance

- `NEAREST`: use for masks, label maps, indexed classes, and pixel art.
- `BICUBIC`: balanced default for many ordinary images.
- `LANCZOS`: high-quality downscaling, often slower.
- `thumbnail(..., reducing_gap=2.0)` is an efficient in-place downscale pattern.
- `resize(..., reducing_gap=...)` can improve large downscale performance while preserving quality.

If output looks blurry, avoid multiple resize passes. Resize once from the highest-quality source using the final target dimensions.

## Filters or Channel Operations Fail

Many `ImageFilter`, `ImageOps`, and `ImageChops` functions are mode-sensitive.

- Convert to `L` or `RGB` for arithmetic and comparison operations unless alpha is central to the task.
- Ensure compared images have the same size and mode before `ImageChops.difference()`.
- Preserve alpha separately if a filter should affect color but not transparency:

```python
rgba = im.convert("RGBA")
r, g, b, a = rgba.split()
filtered_rgb = Image.merge("RGB", (r, g, b)).filter(ImageFilter.GaussianBlur(2))
filtered = Image.merge("RGBA", (*filtered_rgb.split(), a))
```

## `BytesIO` Save Produces Empty or Unreadable Data

- Save to a binary `BytesIO`, then call `getvalue()` after `save()`.
- Pass `format="PNG"`, `format="JPEG"`, or another explicit format when no filename extension is available.
- If another consumer reads the same buffer object, call `buffer.seek(0)` after writing.

## `show()` Does Nothing

`im.show()` is a convenience debug helper that writes a temporary file and launches an external viewer. It may fail silently or be unavailable on headless systems. Prefer saving explicit debug artifacts or using `ImageChops.difference()`/`ImageStat.Stat()` in automated workflows.
