# ANTsPy Visualization and Interop Workflows

These recipes are self-contained and avoid source-repository files. They use tiny in-memory data where possible. For realistic medical image examples, first load or construct images through [image-core](../../image-core/SKILL.md), then return here for display and interop mechanics.

## Headless Plot Saving

Set a non-interactive backend before importing `ants` or `matplotlib.pyplot` in scripts that run on CI, servers, containers, SSH sessions, or batch jobs:

```python
import matplotlib
matplotlib.use("Agg")

import ants
import numpy as np

img = ants.from_numpy(np.arange(64, dtype="float32").reshape(8, 8))
ants.plot(img, filename="preview.png", title="Tiny image", dpi=120)
```

Rules:

- Prefer `filename=` over `plt.show()` for automation.
- Use a temporary or caller-provided output directory; do not write beside input medical images unless the user asked for batch previews.
- Keep `dpi` small for smoke checks and high only for publication figures.
- Use `try/finally` or Matplotlib close calls when manually saving figures after APIs without `filename`, such as `ants.plot_hist`.

## Single-Image Slices and Overlays

Basic saved scalar image:

```python
ants.plot(img, filename="slice_panel.png", axis="z", nslices=6, ncol=3, crop=True)
```

Overlay workflow:

```python
if not ants.image_physical_space_consistency(base, overlay):
    overlay = ants.resample_image_to_target(overlay, base, interp_type="linear")

ants.plot(
    base,
    overlay=overlay,
    filename="overlay.png",
    overlay_cmap="turbo",
    overlay_alpha=0.6,
    cbar=True,
)
```

Label-mask overlay variation:

```python
if not ants.image_physical_space_consistency(base, labels):
    labels = ants.resample_image_to_target(labels, base, interp_type="nearestNeighbor")

ants.plot(base, overlay=labels, filename="labels_overlay.png", overlay_alpha=0.7)
```

Notes:

- `ants.plot` accepts `axis=0/1/2` or aliases `x`, `y`, and `z` for 3D images.
- Relative `slices` values below `1` are interpreted as fractions of the selected axis.
- `blend=True` combines base and overlay intensities into one image; it is not label-aware.
- Route thresholding, smoothing, masking, and resampling choices to [image-ops-math](../../image-ops-math/SKILL.md) when preprocessing is the main task.

## Orthographic Views

Single 3D orthographic view:

```python
ants.plot_ortho(
    volume,
    filename="ortho.png",
    xyz=(32, 32, 16),
    xyz_lines=True,
    title="Crosshair view",
    flat=False,
)
```

Stacked comparison:

```python
images = [baseline, followup]
overlays = [baseline_mask, followup_mask]
for i, (image, overlay) in enumerate(zip(images, overlays)):
    if not ants.image_physical_space_consistency(image, overlay):
        overlays[i] = ants.resample_image_to_target(overlay, image, interp_type="nearestNeighbor")

ants.plot_ortho_stack(
    images,
    overlays=overlays,
    filename="ortho_stack.png",
    title="Baseline vs follow-up",
    xyz_lines=True,
)
```

Notes:

- `plot_ortho` and `plot_ortho_stack` require 3D scalar images.
- `reorient=True` uses an ANTsPy orientation default before display; set an explicit orientation string if consistency across scripts matters.
- `resample=True` in `plot_ortho` helps when spacing is strongly anisotropic, but explicit resampling is clearer when output geometry matters.

## Grid Figures

Use `plot_grid` for publication-style panels with consistent row and column labels:

```python
import numpy as np

images = np.asarray([[img_a, img_b], [img_c, img_d]], dtype=object)
slices = np.asarray([[20, 20], [20, 20]])
axes = np.asarray([[0, 1], [2, 2]])

ants.plot_grid(
    images=images,
    slices=slices,
    axes=axes,
    filename="grid.png",
    rlabels=["Raw", "Smoothed"],
    clabels=["Subject A", "Subject B"],
    colorbar=True,
)
```

Rules:

- If `images` is a 2D NumPy array, ANTsPy converts it to nested lists.
- Grid-shaped `slices` must match the image grid shape.
- A single scalar `slices` value is reused for every panel; `None` selects each image's middle slice.
- For already-sliced 2D images, omit `slices`.

## Histograms Without a GUI

`ants.plot_hist` has no `filename` parameter, so save through Matplotlib:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ants.plot_hist(img, threshold=0.0, title="Intensity histogram")
plt.savefig("histogram.png", dpi=120, bbox_inches="tight")
plt.close()
```

If `fit_line=True` fails in a newer Matplotlib environment because legacy `matplotlib.mlab.normpdf` is unavailable, compute the fitted normal curve with NumPy/SciPy or omit the fit line.

## Movies and Animations

For MP4 output, `ants.movie(volume, filename="movie.mp4")` uses Matplotlib's `FFMpegWriter` by default and requires an ffmpeg executable. For GIF output, provide a writer explicitly when Pillow is installed:

```python
from matplotlib import animation

writer = animation.PillowWriter(fps=8)
ants.movie(volume, filename="slices.gif", writer=writer, fps=8)
```

Use small volumes for quick previews. For deterministic CI smoke checks, prefer still PNG plots over movie generation because external writers vary by environment.

## Batch Directory Previews

`ants.plot_directory(directory, regex="*.nii.gz", recursive=True)` writes PNG previews next to matching `.nii.gz` files. Use it only when side effects in that directory are acceptable:

```python
ants.plot_directory(
    directory=input_dir,
    recursive=False,
    regex="*.nii.gz",
    save_prefix="preview_",
    axis=[0, 1, 2],
    crop=True,
)
```

For controlled pipelines, iterate files yourself and write previews to a separate output directory with `ants.plot(..., filename=...)`.

## Channels, RGB, and Vector Images

Merge scalar channels:

```python
red = ants.from_numpy(np.full((8, 8), 255, dtype="uint8"))
green = ants.from_numpy(np.zeros((8, 8), dtype="uint8"))
blue = ants.from_numpy(np.zeros((8, 8), dtype="uint8"))
vec = ants.merge_channels([red, green, blue])
channels = ants.split_channels(vec)
```

Create an RGB image from a channel-last array:

```python
rgb_array = np.zeros((8, 8, 3), dtype="uint8")
rgb_array[..., 0] = 255
rgb = ants.from_numpy(rgb_array, is_rgb=True)
vec = ants.rgb_to_vector(rgb)
rgb_again = ants.vector_to_rgb(vec)
```

Convert channel-first external arrays before creating ANTsPy images:

```python
channel_first = np.zeros((3, 8, 8), dtype="float32")
channel_last = np.moveaxis(channel_first, 0, -1)
vec = ants.from_numpy(channel_last, has_components=True)
```

Avoid `ants.scalar_to_rgb` in current ANTsPy workflows. It is present but raises a not-supported exception. For scalar visualization, use Matplotlib colormaps through plotting APIs or build explicit RGB arrays yourself.

## Images to Matrix and Back

Matrix extraction inside a mask:

```python
mask = ants.from_numpy((img.numpy() > img.mean()).astype("float32"), origin=img.origin, spacing=img.spacing, direction=img.direction)
images = [img, img + 1]
matrix = ants.images_to_matrix(images, mask=mask, epsilon=0.5)
restored = ants.matrix_to_images(matrix, mask)
```

Validate round-trip assumptions:

```python
assert matrix.shape[0] == len(images)
assert matrix.shape[1] == int((mask.numpy() >= 0.5).sum())
assert ants.image_physical_space_consistency(restored[0], mask)
```

Rules:

- Rows are in the same order as `image_list`.
- Columns follow ANTsPy/NumPy indexing order over voxels where `mask >= epsilon`.
- `matrix_to_images` checks `mask >= 0.5`, so use a binary mask or keep thresholding consistent.
- If an input image shape differs from the mask, `images_to_matrix` resamples to the mask grid. Validate whether that is desired before extraction.

## N-Dimensional Image Lists

Split a 3D image into 2D sections and rebuild it:

```python
sections = ants.ndimage_to_list(nd_image)
rebuilt = ants.list_to_ndimage(nd_image, sections)
assert rebuilt.dimension == nd_image.dimension
```

For time-series-style matrices:

```python
matrix = ants.timeseries_to_matrix(timeseries, mask=mask)
rebuilt = ants.matrix_to_timeseries(timeseries, matrix, mask=mask)
```

Use the original target image as the first argument to `list_to_ndimage` or `matrix_to_timeseries` so spacing, origin, direction, and output dimensions are restored.

## NumPy Interop for Display

Use `img.numpy()` for read-only external plotting; it returns a copy. Use `img.view()` only when intentional mutation is acceptable:

```python
arr = img.numpy()
plt.imshow(arr.T, cmap="gray", origin="lower")
plt.axis("off")
plt.savefig("numpy_display.png", dpi=120, bbox_inches="tight")
plt.close()
```

ANTsPy plotting rotates/reorients slices for medical display conventions. If using raw NumPy/Matplotlib directly, document the orientation convention so users do not compare it visually against ANTsPy plots without checking axes.

## nibabel Round Trip

Guard the optional dependency:

```python
try:
    import nibabel as nib
except ImportError:
    nib = None

if nib is not None:
    nib_img = ants.to_nibabel_nifti(img)
    ants_img = ants.from_nibabel_nifti(nib_img, pixeltype="float")
```

Notes:

- nibabel uses RAS+ affine conventions; ANTsPy uses ITK/ANTs LPS+ metadata. The conversion helpers handle the convention swap.
- Set NIfTI spatial units to millimeters and time units to seconds before conversion.
- 5D nibabel images map components from the last dimension into ANTsPy component images.
- Use `header=` in `to_nibabel_nifti` when downstream code requires a specific header payload, but expect the transform to be replaced with the ANTs image transform when they differ.

## SimpleITK Round Trip

Guard the optional dependency:

```python
try:
    import SimpleITK as sitk
except ImportError:
    sitk = None

if sitk is not None:
    sitk_img = ants.to_sitk(img)
    ants_img = ants.from_sitk(sitk_img)
```

Notes:

- The bridge supports 2D, 3D, and 4D scalar/vector images.
- Axis order is transposed for array storage: SimpleITK arrays are z-y-x style, while ANTsPy arrays are x-y-z style with trailing components.
- Origin, spacing, direction, shape, and component count should be checked after conversion in safety-critical workflows.

## Choosing Output Formats

| Goal | Recommended output |
| --- | --- |
| CI smoke evidence | PNG from `ants.plot(..., filename=...)` with small `dpi`. |
| Publication static figure | PNG or PDF via Matplotlib; set `figsize`, `dpi`, labels, and colorbars explicitly. |
| Interactive notebook display | `ants.plot(...)` without `filename` is acceptable when a display backend exists. |
| Batch previews of NIfTI files | Controlled loop to a separate output directory, or `plot_directory` when writing next to inputs is intended. |
| Animated slice preview | GIF with `PillowWriter` or MP4 with ffmpeg, depending on installed writers. |
| Downstream Python image ecosystem | nibabel or SimpleITK object conversion, guarded by optional imports and metadata assertions. |
