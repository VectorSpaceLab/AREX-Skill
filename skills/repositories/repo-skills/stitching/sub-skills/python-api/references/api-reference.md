# Python API Reference

## When to read this

Read this when you need the verified public constructor signatures, default
settings, or object behavior for the `stitching` Python API.

## Verified public imports

```python
from stitching import Stitcher, AffineStitcher
```

The package version at the referenced snapshot is `0.6.1`.

## Core signatures

| Object | Signature | Notes |
| --- | --- | --- |
| `Stitcher` | `(**kwargs)` | Accepts a settings dictionary keyed by the public defaults below. |
| `Stitcher.stitch` | `(self, images, feature_masks=[])` | Returns a panorama or raises `StitchingError`. |
| `Stitcher.stitch_verbose` | `(self, images, feature_masks=[], verbose_dir=None)` | Produces verbose artifacts and returns the panorama. |
| `AffineStitcher` | `(**kwargs)` | Same constructor style, with affine defaults preloaded. |
| `FeatureDetector` | `(detector='orb', **kwargs)` | Wraps OpenCV feature detectors. |
| `FeatureMatcher` | `(matcher_type='homography', range_width=-1, **kwargs)` | Wraps OpenCV matchers. |
| `Images.of` | `(images, medium_megapix=0.6, low_megapix=0.1, final_megapix=-1)` | Accepts a list of filenames or a list of loaded images. |

## Public defaults and choices

### `Stitcher.DEFAULT_SETTINGS`

| Key | Default |
| --- | --- |
| `medium_megapix` | `0.6` |
| `detector` | `orb` |
| `nfeatures` | `500` |
| `matcher_type` | `homography` |
| `range_width` | `-1` |
| `try_use_gpu` | `False` |
| `match_conf` | `None` |
| `confidence_threshold` | `1` |
| `matches_graph_dot_file` | `None` |
| `estimator` | `homography` |
| `adjuster` | `ray` |
| `refinement_mask` | `xxxxx` |
| `wave_correct_kind` | `horiz` |
| `warper_type` | `spherical` |
| `low_megapix` | `0.1` |
| `crop` | `True` |
| `compensator` | `gain_blocks` |
| `nr_feeds` | `1` |
| `block_size` | `32` |
| `finder` | `dp_color` |
| `final_megapix` | `-1` |
| `blender_type` | `multiband` |
| `blend_strength` | `5` |
| `timelapse` | `no` |
| `timelapse_prefix` | `fixed_` |

### `AffineStitcher.AFFINE_DEFAULTS`

| Key | Default |
| --- | --- |
| `estimator` | `affine` |
| `wave_correct_kind` | `no` |
| `matcher_type` | `affine` |
| `adjuster` | `affine` |
| `warper_type` | `affine` |
| `compensator` | `no` |

### Detector, matcher, and workflow choices

| Class | Verified choices |
| --- | --- |
| `FeatureDetector` | `orb`, `sift`, `brisk`, `akaze` |
| `FeatureMatcher` | `homography`, `affine` |
| `CameraEstimator` | `homography`, `affine` |
| `CameraAdjuster` | `ray`, `reproj`, `affine`, `no` |
| `WaveCorrector` | `horiz`, `vert`, `auto`, `no` |
| `Warper` | `spherical`, `plane`, `affine`, `cylindrical`, `fisheye`, `stereographic`, `compressedPlaneA2B1`, `compressedPlaneA1.5B1`, `compressedPlanePortraitA2B1`, `compressedPlanePortraitA1.5B1`, `paniniA2B1`, `paniniA1.5B1`, `paniniPortraitA2B1`, `paniniPortraitA1.5B1`, `mercator`, `transverseMercator` |
| `ExposureErrorCompensator` | `gain_blocks`, `gain`, `channel`, `channel_blocks`, `no` |
| `SeamFinder` | `dp_color`, `dp_colorgrad`, `gc_color`, `gc_colorgrad`, `voronoi`, `no` |
| `Blender` | `multiband`, `feather`, `no` |
| `Timelapser` | `no`, `as_is`, `crop` |

### Image resolutions

`Images.Resolution` values:

- `MEDIUM = 0.6`
- `LOW = 0.1`
- `FINAL = -1`

## Verified behavior

### `Images.of`

- Input must be a list.
- An empty list raises `StitchingError("images must not be an empty list")`.
- A list of `numpy.ndarray` values produces a `_NumpyImages` instance.
- A list of strings produces a `_FilenameImages` instance.
- Mixed element types raise a `StitchingError`.
- Filename lists resolve globs when needed.

### `FeatureMatcher.get_match_conf`

- `None` + `orb` resolves to `0.3`.
- `None` + any other detector resolves to `0.65`.
- Explicit values are preserved.

### `FeatureDetector.detect_with_masks`

- Image and mask lists must have equal length.
- Each mask must match the corresponding image resolution exactly.
- The method raises `StitchingError` with a message that mentions the mask
  index when a mask resolution is wrong.

### `Stitcher`

- Unknown keyword arguments raise `StitchingError("Invalid Argument: ...")`.
- `AffineStitcher` warns if you overwrite an affine default.
- `stitch` returns the final panorama image.
- `stitch_verbose` writes verbose artifacts to the provided directory.

## Expected error types

| Situation | Type | Message pattern |
| --- | --- | --- |
| Empty image list | `StitchingError` | `images must not be an empty list` |
| Invalid kwargs | `StitchingError` | `Invalid Argument:` |
| No panorama component survives thresholding | `StitchingError` | `No match exceeds the given confidence threshold` |
| Affine default override | `StitchingWarning` | `You are overwriting an affine default` |

## Minimal Python examples

### From filenames

```python
from stitching import Stitcher

stitcher = Stitcher()
panorama = stitcher.stitch(["img1.jpg", "img2.jpg"])
```

### From loaded images

```python
import cv2 as cv
from stitching import Stitcher

stitcher = Stitcher(crop=False)
images = [cv.imread("img1.jpg"), cv.imread("img2.jpg")]
panorama = stitcher.stitch(images)
```

### Affine mode

```python
from stitching import AffineStitcher

stitcher = AffineStitcher(detector="sift", crop=False)
panorama = stitcher.stitch(["scan1.jpg", "scan2.jpg"])
```

## Next places to read

- [Workflow recipes](workflows.md) for concrete Python snippets.
- [Troubleshooting](troubleshooting.md) for invalid input, crop, and warning
  handling.
- [Inspect defaults helper](../scripts/inspect_stitching_defaults.py) for a
  safe machine-readable summary of the installed package.
