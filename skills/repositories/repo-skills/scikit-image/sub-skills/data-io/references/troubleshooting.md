# Data I/O Troubleshooting

Use this checklist when data loading, saving, dtype conversion, or collection handling behaves unexpectedly.

## 1. Imports and installation

Symptoms:
- `ModuleNotFoundError: No module named 'skimage'`
- a generated example imports an internal package name or an outdated API path
- `skimage.data.download_all()` fails because the optional download helper is missing

Fixes:
- install `scikit-image` in the target environment
- use Python 3.12 or newer for the current released package line
- if `download_all()` complains about a missing helper, install the optional dataset dependency such as `pooch` or skip bulk-prefetching altogether
- keep new examples on the public `skimage` namespace instead of copying private module paths

## 2. `skimage.io` plugin warnings

Symptoms:
- `FutureWarning` mentions `plugin`, `mode`, `append`, `available_plugins`, or other plugin arguments
- old code calls `use_plugin`, `find_available_plugins`, or plugin-specific kwargs for `imread` / `imsave`

Fixes:
- treat `skimage.io` plugin plumbing as deprecated behavior, not as a primary feature
- prefer `imageio` or another direct I/O package when you need format-specific control
- keep new runtime recipes on `imread`, `imsave`, `ImageCollection`, and `MultiImage` with local files and default behavior only
- do not build new workflows around custom plugins

## 3. Wrong dtype or pixel range

Symptoms:
- an image looks washed out or clipped after `astype`
- converting integers to float gives values that do not match the expected normalized range
- converting signed values to unsigned values discards negative intensities
- downstream code breaks because a float image is no longer in the range the next function expects

Fixes:
- do not use `astype` to change image semantics; use `skimage.util.img_as_float`, `img_as_ubyte`, `img_as_uint`, `img_as_int`, or `img_as_bool`
- remember that `img_as_float` preserves the values of float inputs and rescales integer inputs
- when you must keep physical units, use `preserve_range=True` in the function that would otherwise normalize values
- inspect `min`, `max`, `dtype`, and `shape` at each boundary before blaming the I/O layer

Quick sanity check:

```python
import skimage as ski

image = ski.data.camera()
float_image = ski.util.img_as_float(image)
assert float_image.min() >= 0
assert float_image.max() <= 1
```

## 4. Local file and collection quirks

Symptoms:
- `imread` behaves differently on a `Path` than on a string
- `as_gray=True` returns a float image when the caller expected `uint8`
- `ImageCollection` loads files out of the expected order
- slicing an `ImageCollection` does not act like a view
- `MultiImage` does not expose the number of frames the user expected or rejects a `Path` object

Fixes:
- `imread` accepts file paths, `pathlib.Path` objects, and file URLs
- `as_gray=True` intentionally returns a grayscale float image
- `ImageCollection` sorts filenames alphanumerically; rename files or provide a custom loader if lexical order is wrong
- slicing returns a new `ImageCollection`, not a view into the original cache
- `MultiImage` is for multi-frame TIFF behavior; for GIFs it only reads the first frame; if a `Path` object fails, pass `str(path)` instead
- call `concatenate_images()` only when every item has the same shape

## 5. Sample data and downloads

Symptoms:
- a dataset exists in the docs but the file is not already on disk
- the first call to a sample-data function tries to download something
- offline tests fail on the first access to an on-demand dataset

Fixes:
- prefer bundled sample images such as `camera`, `coins`, `astronaut`, `text`, `logo`, or `horse` when you need deterministic examples
- on-demand datasets are fetched once and cached; do not assume network access during smoke checks
- if offline access matters, prefetch the assets ahead of time and record the cache location instead of hard-coding absolute paths into examples

## 6. Video handling is reference-only

Symptoms:
- the request is about `.avi`, `.mov`, `.mp4`, or another video container
- a user wants a single `skimage.io` call to decode video frames

Fixes:
- do not make video decoding the primary route for this sub-skill
- convert the video to an image sequence and load it with `ImageCollection`, or use a dedicated video library directly
- keep any discussion of codecs, frame readers, or random access in troubleshooting notes rather than in the main workflow

## 7. Utility-function mistakes

Symptoms:
- `view_as_windows` consumes far more memory than expected
- `montage` raises because the images do not have compatible shapes
- `invert` returns an unexpected result on float or signed data
- `lookfor` prints results that include internal names

Fixes:
- `view_as_windows` is a view, but later computations can still materialize a huge array; keep windows small
- `montage` expects an ensemble of equally shaped images and is best used on tiny tiles or previews
- `invert` follows dtype-specific rules; use `signed_float=True` only when the float image really uses the signed `[-1, 1]` convention
- `lookfor` is a docstring search helper, not a stable API-discovery contract

## Quick diagnosis checklist

1. Print `shape`, `dtype`, `min`, and `max` for the source image and the result.
2. Verify whether the image is grayscale or multichannel and whether `channel_axis` is explicit.
3. Replace `astype` with the matching `img_as_*` helper.
4. Use a temporary directory and a one-file round trip before debugging the real data source.
5. If the task is really about video or bulk prefetching, move that part out of the main route.
