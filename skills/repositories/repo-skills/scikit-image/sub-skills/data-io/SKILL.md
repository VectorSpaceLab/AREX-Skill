---
name: data-io
description: "Load and save images with skimage.data and skimage.io, reason
  about NumPy image conventions and dtype conversion, and handle safe local
  round-trips and collections."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data I/O

Use this sub-skill when the task is about bundled sample images, local image files, image collections, or the conversion boundary between file data and NumPy arrays.

Route away from this sub-skill when the task is mainly about:
- color, exposure, filtering, or restoration: use `../enhancement/SKILL.md`
- feature extraction, measurements, or image metrics: use `../analysis/SKILL.md`
- masks, morphology, watershed, or synthetic shapes: use `../segmentation-and-shapes/SKILL.md`
- geometric transforms, warps, or registration: use `../transform-registration/SKILL.md`
- video decoding or plugin internals as the primary task: keep that in `references/troubleshooting.md` and prefer `imageio` or another direct video library instead.

## Start Here

- Read `references/workflows.md` for bundled sample data, safe local I/O, dtype conversion, and NumPy image conventions.
- Read `references/troubleshooting.md` when imports fail, `astype` changes the image unexpectedly, `skimage.io` plugin warnings appear, or collection and download behavior is confusing.
- Run `scripts/check_install.py` for a safe import and temp-file round-trip smoke test.

## Fast Paths

- Use `skimage.data.camera()`, `coins()`, `astronaut()`, `text()`, `logo()`, `horse()`, or `binary_blobs()` for bundled inputs.
- Load local files with `skimage.io.imread(path)`; write temporary round trips with `skimage.io.imsave(path, image)`.
- Convert data with `skimage.util.img_as_float`, `img_as_ubyte`, `img_as_uint`, `img_as_int`, or `img_as_bool`; never use `astype` to rescale an image.
- Remember the core image convention: rows and columns come first, channels are explicit, and `channel_axis` is how most multichannel APIs stay clear.
- Use `imread_collection` when you want the convenience wrapper around `ImageCollection`; use `ImageCollection` directly for file sequences or custom loaders, and use `MultiImage` for multi-frame TIFFs when a single file should expose a frame list.
- Use `view_as_windows`, `invert`, `montage`, and `lookfor` as lightweight utilities in this route, but keep them secondary to data loading and saving.
- Prefer `imageio` or another direct I/O package when the task needs modern plugin control, video handling, or format-specific features. `skimage.io` plugin arguments are deprecated.
- Optional offline bulk download is a setup step, not a primary route; see troubleshooting before using `skimage.data.download_all()`.

## Reference Map

- `references/workflows.md` — sample-data, image I/O, dtype, collections, and NumPy conventions.
- `references/troubleshooting.md` — install, deprecation, download, collection, and dtype pitfalls.
- `scripts/check_install.py` — safe import and local image round-trip smoke check.

## Smoke Check

Run from the sub-skill root:

```bash
python scripts/check_install.py
```
