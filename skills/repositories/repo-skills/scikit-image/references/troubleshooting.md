# Package-wide troubleshooting

Use this reference for failures that cross workflow boundaries. For algorithm-specific issues, continue with the `references/troubleshooting.md` file under the routed sub-skill.

## Import and installation failures

### Import the distribution under the right name

The distribution is installed as `scikit-image` but imported as `skimage`:

```bash
python -m pip install scikit-image
python -c "import skimage; print(skimage.__version__)"
```

Do not try `import scikit_image`. Confirm that `python` and `pip` refer to the same environment with `python -m pip`, not a separate `pip` executable.

### Avoid importing an unbuilt source tree

scikit-image includes compiled extensions. If imports fail with a missing internal module or shared library while the current directory is a source checkout, first test from another directory. For source development, use the checkout's documented Meson-based build workflow and its supported Python/dependency versions. For runtime use, prefer a compatible wheel.

Useful diagnostics:

```bash
python -m pip show scikit-image
python -m pip check
python -c "import sys, skimage; print(sys.executable); print(skimage.__file__); print(skimage.__version__)"
```

A path pointing into an unexpected checkout, old environment, or user site-packages usually indicates environment shadowing rather than an algorithm failure.

### Compiled-extension errors

Errors mentioning an internal Cython extension, incompatible NumPy ABI, undefined symbols, or a failed Meson build require an environment/build fix. Reinstall mutually compatible NumPy, SciPy, and scikit-image builds in one environment. Do not copy a compiled `.so`, `.pyd`, or build directory between Python environments or platforms.

The source snapshot used for this skill requires Python 3.12 or newer. A released wheel can have different support bounds; check the metadata for the version being installed.

## `skimage` versus `skimage2`

Use `skimage` for stable production workflows. `skimage2` in the source snapshot is an explicitly experimental namespace whose API can change without notice. An import warning is expected and should not be silenced as proof of stability. Read `experimental-api.md` before translating code between namespaces.

If only `skimage2` fails, retry the equivalent stable `skimage` workflow before treating the whole installation as broken. If exact `skimage2` behavior matters, verify the installed version and live signature rather than assuming stable-namespace compatibility.

## Image dtype and range failures

### `astype` changed image brightness or contrast

Casting changes representation but does not apply scikit-image's image range rules. Use:

```python
from skimage import util

image_f = util.img_as_float(image)
image_u8 = util.img_as_ubyte(image_f)
```

Before converting, inspect:

```python
print(image.shape, image.dtype, image.min(), image.max())
```

Float images are commonly interpreted in `[0, 1]` (or `[-1, 1]` where signed values are meaningful), while integer images use their dtype range. Do not infer range from dtype alone when upstream data has physical units.

### An operation unexpectedly rescales values

When an API offers `preserve_range`, pass `preserve_range=True` if native values must remain meaningful. This is independent of whether the output dtype is floating point. Convert output for storage only after processing semantics are correct.

### Metrics reject float input or give misleading scores

For float inputs, pass an explicit `data_range` to metrics such as SSIM and PSNR when it cannot be inferred safely. Both images must have compatible shapes, channel layout, and numeric meaning.

## Shape and channel-axis failures

A three-dimensional array may mean a 2-D color image or a 3-D scalar volume. Set `channel_axis` explicitly when supported:

- `channel_axis=-1` for channels-last color data such as `(rows, cols, 3)`;
- `channel_axis=0` for channels-first data;
- `channel_axis=None` for grayscale images and scalar volumes.

If an API has no `channel_axis`, check whether it expects a scalar image. Convert color data first or process each channel deliberately. Never guess from `ndim` alone.

For labels and masks, keep spatial shape aligned with the source image. Do not interpolate label IDs with linear or cubic interpolation; use `order=0` for geometric resizing or warping.

## Coordinate and geometry failures

scikit-image generally expresses array coordinates in row/column order, not Cartesian x/y order. Transform point APIs can have their own coordinate contract, so read the transform leaf before swapping columns.

`warp` consumes an inverse mapping. Registration shifts describe the correction to apply, which can have the opposite sign from the observed motion. Route inverse-map, shift-sign, interpolation, and output-shape issues to `sub-skills/transform-registration/`.

For physical measurements or anisotropic volumes, pass `spacing` where supported. A result in pixels or voxels is not automatically a result in physical units.

## Optional dependencies and data access

The base package supports the core CPU workflows in this skill, but particular operations can require optional packages or external resources. Examples include plotting, graph/solver accelerators, some I/O formats, sample-data downloads, and interactive tooling.

- Install only the optional dependency required by the selected workflow.
- Separate a missing optional dependency from a scikit-image API failure.
- Prefer bundled sample images or tiny synthetic arrays for offline checks.
- Treat `skimage.data.download_all()` and non-bundled datasets as network/cache operations; they can fail because of proxies, certificates, permissions, or an unavailable cache.
- Prefer direct `imageio` usage when modern plugin control, format-specific options, or video handling is the main requirement. The old `skimage.io` plugin arguments are deprecated.

## Deprecations and stale examples

When a keyword or import from an old example is rejected:

1. print the installed scikit-image version;
2. inspect the live function signature;
3. check whether the example targets `skimage`, `skimage2`, or an older release;
4. replace deprecated plugin, channel, or parameter conventions with the current documented form;
5. consult `repo-provenance.md` to determine whether this skill predates the active environment.

Do not fix version drift by blindly suppressing warnings. Warnings often identify a changed dtype, channel, namespace, or parameter contract.

## Minimal offline isolation sequence

From the scikit-image skill directory:

```bash
python sub-skills/data-io/scripts/check_install.py
```

If that passes, the package import and a local temporary-file path work. Then reproduce the failing workflow with a tiny array or bundled image and read the routed leaf's troubleshooting reference. If it fails, fix the environment before debugging the algorithm.
