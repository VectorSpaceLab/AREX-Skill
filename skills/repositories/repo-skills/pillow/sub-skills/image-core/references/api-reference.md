# Image Core API Reference

This reference covers ordinary `PIL.Image.Image` workflows. It intentionally avoids format-specific encoder flags, metadata policy, multi-frame behavior, drawing/text APIs, and plugin registration.

## Imports and Constructors

```python
from PIL import Image, ImageOps, ImageChops, ImageEnhance, ImageFilter, ImageStat
```

- `Image.open(fp, mode="r", formats=None)` opens an image file path or binary file-like object and identifies the format from file contents. It reads headers immediately but decodes pixel data lazily.
- `Image.new(mode, size, color=0)` creates a new image. `size` is `(width, height)` in pixels. `color` may be a scalar for single-band modes or a tuple matching the mode bands.
- `Image.Image.save(fp, format=None, **params)` writes an image. If `format` is omitted, Pillow usually infers it from a filename extension; file-like outputs normally need an explicit format.
- `Image.alpha_composite(im1, im2)`, `Image.blend(im1, im2, alpha)`, `Image.composite(image1, image2, mask)`, and `Image.merge(mode, bands)` build or combine images.

## Image Object Basics

Common attributes and methods:

- `im.format`: source format such as `"JPEG"` or `"PNG"`; `None` for images created in memory.
- `im.size`, `im.width`, `im.height`: dimensions as `(width, height)` or individual integers.
- `im.mode`: pixel mode such as `"1"`, `"L"`, `"P"`, `"RGB"`, `"RGBA"`, `"CMYK"`, `"I"`, or `"F"`.
- `im.getbands()`: band names, for example `("R", "G", "B", "A")`.
- `im.info`: format-provided auxiliary data. Treat it as input metadata; most ordinary image operations do not preserve every key automatically.
- `im.load()`: forces pixel decoding and returns a pixel-access object for many modes.
- `im.copy()`: returns a detached image copy; use it when image data must outlive a `with Image.open(...)` block.
- `im.verify()`: checks file integrity where supported, but leaves the object unsuitable for subsequent pixel operations; reopen after `verify()`.

## Modes, Bands, and Transparency

- `"L"` is 8-bit grayscale; `"RGB"` is true color; `"RGBA"` adds an alpha channel; `"P"` is palette-indexed.
- Palette images may carry transparency through `im.info["transparency"]` instead of an alpha band. Convert to `RGBA` before alpha-sensitive composition or resizing.
- `RGBa` and `La` are premultiplied-alpha modes; do not assume they behave exactly like straight-alpha `RGBA` and `LA` when doing channel math.
- Many `ImageOps` and `ImageChops` operations are most predictable on `L`, `RGB`, or `RGBA`. Convert explicitly when a mode-specific error appears.

## Coordinate and Box Conventions

Pillow coordinates start at `(0, 0)` in the upper-left corner. Rectangles are `(left, upper, right, lower)`, with `right` and `lower` referring to the pixel boundary after the last included pixel.

```python
box = (10, 20, 110, 70)
region = im.crop(box)  # 100 by 50 pixels
```

Validate boxes before using them in reusable code:

```python
left, upper, right, lower = box
if right <= left or lower <= upper:
    raise ValueError("box must have positive width and height")
```

## Transform and Geometry Methods

- `im.crop(box=None)` returns a rectangular region. The result is a new image. Boxes outside the source may produce padded pixels rather than the intended content; validate bounds when exact crops matter.
- `im.paste(source, box=None, mask=None)` mutates `im`. If `box` is a 4-tuple, source size must match the box size. Use a mask or alpha channel for transparent paste.
- `im.resize(size, resample=None, box=None, reducing_gap=None)` returns a new image with exact `size`. `box` can crop before resizing. `reducing_gap` can improve downscale speed/quality tradeoffs.
- `im.thumbnail(size, resample=Image.Resampling.BICUBIC, reducing_gap=2.0)` mutates the image in place and preserves aspect ratio within `size`.
- `im.rotate(angle, resample=..., expand=False, center=None, translate=None, fillcolor=None)` returns a rotated copy; set `expand=True` to resize the output bounds.
- `im.transpose(method)` flips or rotates using `Image.Transpose.FLIP_LEFT_RIGHT`, `FLIP_TOP_BOTTOM`, `ROTATE_90`, `ROTATE_180`, `ROTATE_270`, or transpose/transverse constants.
- `im.transform(size, method, data=None, resample=..., fill=..., fillcolor=None)` supports affine, perspective, extent, and mesh transforms; prefer higher-level methods unless you need custom geometry.

## Resampling Choices

Use `from PIL import Image` and reference `Image.Resampling`:

- `NEAREST`: fastest and exact for masks, labels, palettes, and pixel art; poor for photos.
- `BOX`: useful for simple downscaling and averaging; resize/thumbnail only.
- `BILINEAR`: moderate speed and quality.
- `HAMMING`: resize/thumbnail only; often sharper than bilinear.
- `BICUBIC`: balanced default for many photo and UI assets.
- `LANCZOS`: high-quality downscaling; slower and resize/thumbnail only.

## ImageOps Helpers

`ImageOps` offers ready-made operations, mostly reliable on `L` and `RGB` and often useful on `RGBA` after explicit conversion:

- `ImageOps.contain(image, size, method=Image.Resampling.BICUBIC)` returns a new image fitting within `size` while preserving aspect ratio.
- `ImageOps.cover(image, size, method=Image.Resampling.BICUBIC)` returns an image that covers `size` while preserving aspect ratio; one dimension may exceed `size`.
- `ImageOps.fit(image, size, method=Image.Resampling.BICUBIC, bleed=0.0, centering=(0.5, 0.5))` crops and resizes to exactly `size`.
- `ImageOps.pad(image, size, method=Image.Resampling.BICUBIC, color=None, centering=(0.5, 0.5))` letterboxes/pillarboxes to exactly `size`.
- Other common helpers: `grayscale`, `invert`, `mirror`, `flip`, `expand`, `crop`, `autocontrast`, `equalize`, `posterize`, `solarize`, and `exif_transpose`.

## ImageChops Channel Operations

`ImageChops` performs arithmetic channel operations and returns new images. Most functions are intended for 8-bit modes such as `L` and `RGB`.

- Comparisons/combinations: `difference`, `darker`, `lighter`, `multiply`, `screen`, `overlay`, `soft_light`, `hard_light`.
- Arithmetic: `add(image1, image2, scale=1.0, offset=0)`, `subtract(image1, image2, scale=1.0, offset=0)`, plus modulo variants.
- Logic: `logical_and`, `logical_or`, `logical_xor` for compatible binary-like images.
- Positioning: `offset(image, xoffset, yoffset=None)` wraps pixels around image edges.

## ImageEnhance, ImageFilter, and ImageStat

Enhancement classes share `enhance(factor)`:

- `ImageEnhance.Color(image)`: `0.0` is grayscale, `1.0` unchanged, larger increases color.
- `ImageEnhance.Contrast(image)`: `0.0` approaches flat gray, `1.0` unchanged.
- `ImageEnhance.Brightness(image)`: `0.0` black, `1.0` unchanged.
- `ImageEnhance.Sharpness(image)`: `0.0` blurred, `1.0` unchanged, `2.0` sharpened.

Filtering uses `im.filter(filter)`:

- Constants: `BLUR`, `CONTOUR`, `DETAIL`, `EDGE_ENHANCE`, `EDGE_ENHANCE_MORE`, `EMBOSS`, `FIND_EDGES`, `SHARPEN`, `SMOOTH`, `SMOOTH_MORE`.
- Parameterized filters: `GaussianBlur(radius)`, `BoxBlur(radius)`, `UnsharpMask(radius=2, percent=150, threshold=3)`, `Kernel(size, kernel, scale=None, offset=0)`, `MedianFilter(size=3)`, `MinFilter`, `MaxFilter`, `ModeFilter`.

Statistics:

```python
stat = ImageStat.Stat(im.convert("RGB"))
print(stat.mean, stat.median, stat.extrema, stat.stddev)
```

`ImageStat.Stat(image_or_histogram, mask=None)` calculates per-band statistics for an image, optional mask, or histogram.

## BytesIO Workflows

```python
from io import BytesIO
from PIL import Image

with Image.open(BytesIO(input_bytes)) as im:
    out = im.convert("RGB").resize((256, 256), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    out.save(buffer, format="JPEG")
result_bytes = buffer.getvalue()
```

Always pass `format=` when saving to a `BytesIO` object unless another layer provides a filename-like object with a useful extension.
