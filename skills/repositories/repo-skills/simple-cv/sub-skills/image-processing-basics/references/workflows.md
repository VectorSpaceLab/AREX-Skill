# Image Processing Workflows

## When to read this

Read this when a task needs concrete SimpleCV static-image steps: load, save, transform, color-process, draw, filter, or validate images without reopening original examples.

## Load images safely

Use package sample names when possible:

```python
from SimpleCV import Image, ImageSet
logo = Image('simplecv')
coins = Image('coins.jpg', sample=True)
imgs = ImageSet('samples')
```

If the user gives a path, check the image is non-empty before continuing:

```python
img = Image(user_path)
if img.isEmpty():
    raise RuntimeError('SimpleCV loaded an empty image; check path or package data')
```

## Save instead of show in automation

Most source examples call `img.show()` or run display loops. For reusable automation, save finite outputs:

```python
img = Image('simplecv')
img.drawText('SimpleCV', 10, 10)
rendered = img.applyLayers()
rendered.save('annotated.png')
```

Use `show()` only when a real display is part of the user request.

## Transform recipe

Equivalent to the safe part of the original rotation example:

```python
from SimpleCV import Image
img = Image('orson_welles.jpg', sample=True)
rot = img.rotate(45)
small = img.crop(0, 0, min(100, img.width), min(100, img.height)).scale(64, 64)
rot.save('rotated.png')
small.save('crop_scaled.png')
```

Decision points:

- `rotate(angle)` keeps fixed-size output by default.
- Use the `fixed` and `point` arguments when a user needs full extents or rotation around a specific point.
- `warp(cornerpoints)` and `shear(cornerpoints)` expect corner point lists in image coordinates.

## Color and threshold recipe

```python
from SimpleCV import Image, Color
img = Image('coins.jpg', sample=True)
gray = img.grayscale()
binary = gray.binarize()
mask = img.hueDistance(Color.BLACK)
binary.save('binary.png')
mask.save('hue_distance.png')
```

Use `ColorModel` when a user wants learned foreground/background colors rather than a single threshold.

## Drawing and compositing recipe

```python
from SimpleCV import Image, Color
img = Image('simplecv')
img.drawRectangle(10, 10, 80, 40, color=Color.RED, width=2)
img.drawText('box', 15, 15, color=Color.BLUE)
out = img.applyLayers()
out.save('boxed.png')
```

If a test compares images, render drawing layers before comparison.

## DFT and scanline ownership

- Use DFT methods such as `getDFTLogMagnitude`, `highPassFilter`, `lowPassFilter`, `bandPassFilter`, and `applyDFTFilter` for frequency-domain workflows.
- Use `getLineScan`, `getHorzScanline`, and `getVertScanline` when the task needs intensity profiles, edge fitting, or one-dimensional signal operations.
- Validate grayscale/color expectations before using DFT or line-scan methods because some return matrix-like objects and some return `Image` instances.

## Native evidence replacing original examples

| Source repo artifact | Runtime replacement |
|---|---|
| `examples/manipulation/RotationExample.py` | `scripts/image_recipe.py --recipe rotate`; finite, no infinite display loop. |
| `examples/detection/CoinDetector.py` | Use `feature-detection` helper for blob measurement; static image loading guidance lives here. |
| `examples/detection/TemplateMatching.py` | Use `feature-detection` helper; save output instead of displaying each method. |
| `tests/tests.py` image/color cases | Final verification candidates after integration. |

## Validation checklist

- `Image(...)` returns non-empty dimensions.
- Output directory exists before saving.
- Headless code uses `save()` rather than `show()`.
- Color tuple order is explicit when crossing into OpenCV/cv2 code.
- Drawing layers are applied before saving or diffing.
- Optional sample images are loaded through SimpleCV package data, not source paths.
