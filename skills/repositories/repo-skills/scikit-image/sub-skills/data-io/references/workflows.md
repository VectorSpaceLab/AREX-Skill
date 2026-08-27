# Data I/O Workflows

Use these recipes when the task starts with bundled sample data or local image files and ends with NumPy arrays, temporary files, or image collections that later subskills can consume.

## 1. Load bundled sample data first

`skimage.data` provides curated sample images and a few on-demand datasets. Prefer these inputs when you want deterministic examples, fast smoke checks, or documentation-friendly code.

```python
import skimage as ski

camera = ski.data.camera()
astronaut = ski.data.astronaut()
coins = ski.data.coins()
text = ski.data.text()
logo = ski.data.logo()

assert camera.ndim == 2
assert astronaut.shape[-1] in (3, 4)
```

Typical conventions:
- grayscale images are 2-D arrays shaped `(rows, cols)`
- color images are usually shaped `(rows, cols, channels)`
- sample images already follow NumPy indexing, so row comes before column

Some datasets are downloaded on demand the first time they are requested. If you need offline access, prefetch them with `skimage.data.download_all()` after installing the optional dataset dependency required for on-demand assets. Keep that as environment setup, not as a default runtime step.

## 2. Read and write local images

Use `skimage.io.imread` for local files, `pathlib.Path` objects, or file URLs. Use `skimage.io.imsave` for round trips to a temporary file or a user-provided path.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

import skimage as ski

with TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    src = tmp / "camera.png"
    ski.io.imsave(src, ski.data.camera())
    camera = ski.io.imread(src)
    assert camera.shape == (512, 512)
    assert camera.dtype == ski.data.camera().dtype
```

Useful reminders:
- `imread(path, as_gray=True)` returns a 2-D grayscale image with floating-point dtype
- already grayscale images are left alone by `as_gray=True`
- `imsave` is best checked with a temp-file round trip that asserts shape, dtype, and approximate values rather than exact bytes
- if you need direct control over codecs, use `imageio` or another I/O library directly and keep `skimage.io` as a convenience layer

## 3. Work with collections and multi-frame files

Use `imread_collection` when you want the convenience wrapper around `ImageCollection`; it behaves like a lazily loaded image collection and is handy for local file sequences, globs, or custom loaders that should lazily load items on demand. Use `ImageCollection` directly when you need the class itself, and use `MultiImage` when a single multi-frame TIFF should be treated as one collection item whose first axis indexes frames.

```python
import skimage as ski

collection = ski.io.imread_collection("frames/frame*.png")
frame0 = collection[0]
subset = collection[:2]  # returns a new ImageCollection
```

Key behavior:
- filenames are returned in alphanumeric order
- slicing returns a new collection, not a view
- `conserve_memory=True` keeps only one image cached by default
- `ImageCollection.concatenate()` and `skimage.io.concatenate_images()` require identical shapes
- `MultiImage` keeps all TIFF frames together as one item shaped like `(frames, rows, cols)`
- if a `Path` object is rejected by `MultiImage` on your installed version, coerce it with `str(path)` before construction
- for animated GIFs, `MultiImage` only reads the first frame; use `ImageCollection` if you need every frame separately

When you already have an image sequence on disk, this route is the safest way to model video-like inputs without turning the sub-skill into a video decoder.

## 4. Convert dtypes safely

Image conversion is a data model problem, not a plain NumPy cast. Use the `img_as_*` helpers so values are rescaled correctly.

```python
import numpy as np
import skimage as ski

image = ski.data.camera()
float_image = ski.util.img_as_float(image)
ubyte_image = ski.util.img_as_ubyte(float_image)

assert float_image.dtype == np.float64
assert ubyte_image.dtype == image.dtype
```

Rules of thumb:
- `astype` only changes the dtype representation; it does not rescale values for image semantics
- `img_as_float` preserves float precision and does not rescale float inputs
- unsigned and signed integer ranges are handled according to scikit-image's image dtype conventions
- negative values are clipped when converting signed values to unsigned outputs
- use `preserve_range=True` in functions such as `transform.rescale` when the values are physical measurements and should not be normalized to `[0, 1]`

When in doubt, print `image.dtype`, `image.min()`, and `image.max()` before and after the conversion.

## 5. Follow NumPy image conventions

The library follows NumPy indexing, so the first dimension is rows and the second is columns. For multichannel data, make the channel axis explicit.

```python
import numpy as np
import skimage as ski

camera = ski.data.camera()
patches = ski.util.view_as_windows(camera, (32, 32), step=16)
tile = ski.util.montage(np.stack([camera[:64, :64], camera[64:128, 64:128]]))
inverted = ski.util.invert(camera)
```

Use these helpers carefully:
- `view_as_windows` makes a rolling window view; it is cheap to create but can explode in size if you later materialize all windows
- `montage` expects equally shaped images and can rescale intensity or add padding when building a preview grid
- `invert` complements grayscale, signed, unsigned, or boolean images according to dtype rules
- `lookfor` is a discovery tool for docstrings, useful when the user only remembers a keyword and not the exact API name

## 6. Keep video and bulk download out of the primary route

If the request is about `.avi`, `.mov`, `.mp4`, or another video format, do not turn that into the main data-io workflow. Convert the video to an image sequence first or use a dedicated video library such as `imageio`, PyAV, MoviePy, or OpenCV.

If the request is about prefetching all on-demand sample datasets, keep it as an environment preparation step. That path depends on optional download support and should not be the default answer for ordinary image loading.
