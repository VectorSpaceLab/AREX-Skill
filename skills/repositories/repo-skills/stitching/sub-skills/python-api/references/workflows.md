# Python API Workflows

## When to read this

Read this when you want a usable Python snippet rather than a flag catalog.

## 1) Stitch a list of filenames

```python
from stitching import Stitcher

stitcher = Stitcher()
panorama = stitcher.stitch(["img1.jpg", "img2.jpg", "img3.jpg"])
```

### Notes
- This is the simplest path when the images are already on disk.
- Use `stitcher.stitch_verbose(...)` when you want diagnostic outputs too.

## 2) Stitch already loaded images

```python
import cv2 as cv
from stitching import Stitcher

stitcher = Stitcher(crop=False)
images = [cv.imread("img1.jpg"), cv.imread("img2.jpg")]
panorama = stitcher.stitch(images)
```

### Notes
- The images must be a list of NumPy arrays.
- Use `crop=False` when you want to keep the full warped canvas.

## 3) Stitch with feature masks

```python
from stitching import Stitcher

stitcher = Stitcher()
panorama = stitcher.stitch(
    ["barcode1.png", "barcode2.png"],
    ["mask1.png", "mask2.png"],
)
```

### Notes
- The feature-mask list must have one entry per image.
- Each mask must match the corresponding image dimensions.
- Use masks when you want to suppress features from a noisy border or a
  distracting region.

## 4) Use affine mode for scans or flat documents

```python
from stitching import AffineStitcher

stitcher = AffineStitcher(detector="sift", crop=False)
panorama = stitcher.stitch(["scan1.jpg", "scan2.jpg"])
```

### Notes
- `AffineStitcher` preloads affine-friendly defaults.
- If you overwrite an affine default, expect a `StitchingWarning` and confirm
  that the override is intentional.

## 5) Capture verbose outputs from Python

```python
from stitching import Stitcher

stitcher = Stitcher()
panorama = stitcher.stitch_verbose(
    ["img1.jpg", "img2.jpg"],
    verbose_dir="stitch-debug",
)
```

### What to expect
- A verbose directory with step-by-step outputs.
- The final panorama as the return value.
- Useful artifacts for match, warp, seam, crop, and timelapse debugging.

## 6) Build a settings dictionary from CLI thinking

If you know the CLI flags, translate them into a Python settings dictionary:

```python
from stitching import Stitcher

settings = {
    "detector": "orb",
    "confidence_threshold": 0.8,
    "crop": False,
    "matches_graph_dot_file": "matches.dot",
}
stitcher = Stitcher(**settings)
```

### Notes
- This is the best path when you want to keep the same options in code and in
  the shell.
- Use `AffineStitcher` when the CLI equivalent would use `--affine`.

## 7) Reuse a stitcher carefully

You can call the same `Stitcher` instance on more than one image set, but the
image scaling is recalculated from the current input set.

```python
from stitching import Stitcher

stitcher = Stitcher()
_ = stitcher.stitch(["s1.jpg", "s2.jpg"])
_ = stitcher.stitch(["boat1.jpg", "boat2.jpg"])
```

### Notes
- Do not assume a previous run fixed the scale for later runs.
- If the image types, sizes, or overlap pattern change, re-check your settings.

## Good recovery order

1. Confirm the input list type: filenames or loaded arrays.
2. Confirm that each mask matches its image.
3. If images are dropped, lower the confidence threshold or try a different
   detector.
4. If crop fails, retry with `crop=False`.
5. If you need to diagnose the issue, switch to `stitch_verbose(...)`.
