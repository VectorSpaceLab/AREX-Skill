# Image Core Workflows

These recipes use installed Pillow only and are safe to adapt into application code. Keep metadata- or format-specific save choices in the format-focused sub-skill.

## Identify Images Quickly

`Image.open()` reads enough header data to determine format, size, and mode without decoding all pixels.

```python
from PIL import Image, UnidentifiedImageError

for path in paths:
    try:
        with Image.open(path) as im:
            print(path, im.format, im.size, im.mode)
    except (UnidentifiedImageError, OSError) as exc:
        print(f"skip {path}: {exc}")
```

If downstream code needs pixels after the `with` block, call `copy()` or `load()` while the file is still open:

```python
with Image.open(path) as im:
    detached = im.copy()
# detached can now be used after the source file is closed
```

## Verify Then Reopen

`verify()` is for integrity checks. Reopen before processing.

```python
from PIL import Image

with Image.open(path) as im:
    im.verify()

with Image.open(path) as im:
    processed = im.convert("RGB")
```

## Create, Crop, and Paste Without Off-by-One Errors

```python
from PIL import Image

canvas = Image.new("RGB", (320, 200), "white")
region = Image.new("RGB", (80, 40), "royalblue")
left, upper = 20, 30
box = (left, upper, left + region.width, upper + region.height)
canvas.paste(region, box)
```

For reusable crop/paste code, assert the geometry:

```python
def require_box(box):
    left, upper, right, lower = box
    if right <= left or lower <= upper:
        raise ValueError(f"invalid box {box!r}")
    return right - left, lower - upper
```

## Preserve Transparent Logos

Use `RGBA` for straight alpha, resize with a high-quality filter, and composite via alpha-aware operations.

```python
from PIL import Image

with Image.open(background_path) as bg, Image.open(logo_path) as logo:
    base = bg.convert("RGBA")
    mark = logo.convert("RGBA")
    mark.thumbnail((base.width // 4, base.height // 4), Image.Resampling.LANCZOS)
    base.alpha_composite(mark, dest=(base.width - mark.width - 24, base.height - mark.height - 24))
    base.save(output_path, "PNG")
```

If output must be JPEG, flatten intentionally onto a background color first:

```python
flattened = Image.new("RGB", base.size, "white")
flattened.paste(base, mask=base.getchannel("A"))
flattened.save(output_path, "JPEG")
```

## Resize, Thumbnail, Contain, Fit, and Pad

Use the operation that matches the target contract:

```python
from PIL import Image, ImageOps

with Image.open(input_path) as im:
    exact = im.resize((300, 200), Image.Resampling.LANCZOS)
    contained = ImageOps.contain(im, (300, 200), Image.Resampling.BICUBIC)
    cropped = ImageOps.fit(im, (300, 200), Image.Resampling.BICUBIC, centering=(0.5, 0.5))
    padded = ImageOps.pad(im, (300, 200), Image.Resampling.BICUBIC, color="white")
```

- `resize()` always returns the exact requested dimensions and may distort aspect ratio.
- `thumbnail()` mutates in place and preserves aspect ratio within a maximum box.
- `contain()` returns a new aspect-preserving image that fits inside the box.
- `fit()` crops and resizes to exactly fill the box.
- `pad()` preserves aspect ratio and adds margins to reach the exact size.

## Apply Enhancements and Filters

```python
from PIL import Image, ImageEnhance, ImageFilter

with Image.open(input_path) as im:
    work = im.convert("RGB")
    work = ImageEnhance.Contrast(work).enhance(1.15)
    work = ImageEnhance.Sharpness(work).enhance(1.4)
    work = work.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))
    work.save(output_path)
```

Enhancement factors are relative: `1.0` is unchanged; lower values reduce the effect; higher values increase it.

## Compare Two Images

`ImageChops.difference()` plus `ImageStat.Stat()` is a compact regression-debug pattern.

```python
from PIL import Image, ImageChops, ImageStat

with Image.open(expected_path) as expected, Image.open(actual_path) as actual:
    a = expected.convert("RGB")
    b = actual.convert("RGB").resize(a.size)
    diff = ImageChops.difference(a, b)
    stat = ImageStat.Stat(diff)
    mean_abs_error = sum(stat.mean) / len(stat.mean)
    bbox = diff.getbbox()
    print({"mean_abs_error": mean_abs_error, "changed_box": bbox})
```

`getbbox()` returns `None` when all channels are zero, which is useful for exact equality checks after ensuring the same mode and size.

## Process In-Memory Bytes

```python
from io import BytesIO
from PIL import Image, ImageOps

def make_preview(image_bytes: bytes) -> bytes:
    with Image.open(BytesIO(image_bytes)) as im:
        preview = ImageOps.contain(im.convert("RGB"), (512, 512), Image.Resampling.LANCZOS)
        out = BytesIO()
        preview.save(out, format="JPEG")
        return out.getvalue()
```

Use binary streams. Text streams or partially-read streams are common causes of open/save failures.

## Guard Against Very Large Inputs

Pillow warns or errors when images exceed the configured decompressed pixel limit.

```python
import warnings
from PIL import Image

warnings.simplefilter("error", Image.DecompressionBombWarning)
with Image.open(path) as im:
    im.load()
```

For trusted internal workloads that deliberately use huge rasters, set `Image.MAX_IMAGE_PIXELS` to a larger integer or `None` in a narrow scope and document why.

## Use the Bundled Inspector

```bash
python scripts/inspect_image.py input.png
python scripts/inspect_image.py input.png --thumbnail thumb.jpg --max-size 256 256 --format JPEG
```

The script reports `format`, `mode`, `size`, band names, and optional thumbnail output. It is meant as a tiny fixture generator and debugging helper, not a full converter.
