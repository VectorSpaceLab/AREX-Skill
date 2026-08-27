# WSI I/O Troubleshooting

Use this guide to diagnose WSI opening, metadata, crop, CLI, multichannel, tiling, and registration setup problems.

## OpenSlide or Native Reader Fails

Symptoms:

- `OpenSlideError`, `OpenSlideUnsupportedFormatError`, or native library import errors.
- A supported extension still fails to open.
- TIFF opens with a fallback reader but metadata differs from expectation.

Checks and fixes:

1. Use `WSIReader.open(...)` first; it can route to TIFF, NGFF, DICOM, JP2, virtual, or OpenSlide readers as appropriate.
2. Confirm the file is readable and not a placeholder, truncated file, or unsupported vendor variant.
3. For OpenSlide-backed formats, install the native OpenSlide library as well as Python bindings in the runtime environment.
4. For OME-TIFF/QPTIFF/multichannel TIFF, try the TIFF reader path through `WSIReader.open(..., post_proc=None)` if raw channels matter.
5. For plain image arrays or simple PNG/JPEG fixtures, use `VirtualWSIReader` or pass a numpy array to `WSIReader.open`.

## Unsupported Format or Extension

Symptoms:

- `FileNotSupportedError`.
- A Zarr directory is rejected as not being NGFF v0.4.
- A generic TIFF is not tiled or lacks expected pyramid structure.

Checks and fixes:

- Verify the input suffix and actual file content match a TIAToolbox-supported reader path.
- For `.zarr`, confirm it is an OME-NGFF-compatible multiscales store, not an arbitrary Zarr array.
- For `.json`, confirm it is a valid fsspec Zarr reference JSON if using that route.
- For unsupported image-like data, create a numpy array or standard PNG/JPEG and read it with `VirtualWSIReader`.
- Do not route format conversion or data acquisition into this sub-skill unless the user specifically asks for WSI I/O diagnosis.

## Missing `mpp` or `objective_power`

Symptoms:

- `ValueError` mentioning missing `mpp` or `objective_power`.
- `convert_resolution_units` returns `None` for a requested output unit.
- `slide_thumbnail()` fails or gives unexpected scale because its default uses `resolution=1.25`, `units="power"`.

Checks and fixes:

1. Inspect `wsi.info.as_dict()`.
2. If `mpp` is known externally, pass `mpp=(x, y)` to `WSIReader.open`, `OpenSlideWSIReader`, or `VirtualWSIReader`.
3. If objective power is known externally, pass `power=value`.
4. If scale is not known, use `units="level"` or `units="baseline"` and avoid claiming physical scale.
5. For thumbnails with missing power, call `wsi.slide_thumbnail(resolution=1.0, units="baseline")` or use a known `mpp`.

## Resolution Unit Confusion

Symptoms:

- Crops show different tissue at different resolutions.
- Output size is unexpected.
- A lower `mpp` produces a larger or slower read than expected.

Checks and fixes:

- `read_rect` keeps output size fixed; changing resolution changes field of view.
- `read_bounds` keeps baseline field of view fixed; changing resolution changes output size.
- In `mpp`, lower values mean higher resolution and larger memory use for the same field of view.
- In `power`, higher values mean higher resolution.
- In `baseline`, `1.0` is full baseline resolution and `0.5` is half linear resolution.
- In `level`, `0` is baseline; larger levels are usually lower resolution.
- Use `wsi.slide_dimensions(resolution, units)` and a tiny read to validate assumptions before batch reads.

## Out-of-Bounds or Edge Reads

Symptoms:

- Black borders or zeros at crop edges.
- Unexpected padding near negative coordinates or bounds extending past slide dimensions.
- Shape is correct but content includes artificial background.

Checks and fixes:

- Compare requested coordinates against `wsi.info.slide_dimensions`.
- Confirm bounds order is `(left, top, right, bottom)` and not `(x, y, width, height)`.
- Use positive width and height: `right > left`, `bottom > top`.
- Choose padding explicitly: `pad_mode="constant"` for zeros or `pad_mode="reflect"` to reduce artificial borders.
- For annotation-aligned reads, prefer `read_bounds` so the baseline field of view stays stable.

## Multichannel Axis or Channel Issues

Symptoms:

- Expected five or more channels but got RGB output.
- RGB previews look plausible but quantitative channel analysis is wrong.
- Channel axis appears swapped or dropped.

Checks and fixes:

1. For raw multiplex data, open with `post_proc=None`.
2. For RGB previews, keep `post_proc="auto"` and document that channels may be composited.
3. Inspect output shape: TIAToolbox image arrays are typically `(height, width, channels)`.
4. Check `wsi.info.axes` and raw metadata for channel ordering and names.
5. For synthetic arrays with more than four channels, use `VirtualWSIReader(..., mode="feature", post_proc=None)` to preserve native channels.
6. Route display overlay questions to `annotation-visualization` if the problem is rendering rather than raw read behavior.

## Huge Tile or Region Memory

Symptoms:

- Process is killed or becomes very slow during `read_bounds`, `slide_thumbnail`, or `save_tiles`.
- Tile generation creates far more files than expected.
- `read_bounds` at high resolution allocates an enormous array.

Checks and fixes:

- Estimate output size with `wsi.slide_dimensions(...)` for whole-slide operations.
- For `read_bounds`, compute baseline width/height and consider the requested resolution scale.
- Start with smaller `tile_read_size`, lower `tile_objective_value`, or lower-resolution units.
- Avoid default power-based thumbnail reads if the slide has no reliable objective power.
- Run a tiny crop first and log shape/dtype before scaling up.
- Use `save_tiles` for WSI tiling, but route patch sampling/filtering logic to `image-preprocessing`.

## CLI Command Does Nothing Useful

Symptoms:

- `slide-info` prints metadata but no files are saved.
- `slide-thumbnail` or `read-bounds` tries to display an image in a headless environment.
- `read-bounds` saves to an unexpected location.

Checks and fixes:

- Use `--mode save` when a file output is required.
- Provide `--output-path` explicitly for reproducibility.
- For directory inputs, set `--file-types` to match the actual slide extensions.
- For `read-bounds`, provide `--region left top right bottom`; it is not width/height syntax.
- Use `cli-and-configuration` for full Click option behavior and shared flags.

## Registration Overlay Mismatch

Symptoms:

- The transformed moving image appears farther from the fixed image.
- The overlay improves if source/target are swapped manually.
- Masks appear aligned to the wrong image.

Checks and fixes:

1. `DFBRegister.register(fixed_img, moving_img, fixed_mask, moving_mask)` returns a transform for moving-to-fixed alignment.
2. Treat `fixed_img` as the reference frame and `moving_img` as the image being warped.
3. Ensure masks are paired with their own images: fixed mask with fixed image, moving mask with moving image.
4. Read both images at the same physical scale and comparable field of view before registration.
5. Confirm image arrays are RGB `(height, width, 3)`; grayscale or 4D arrays raise shape/channel errors.
6. If using a transform initializer, confirm it has the same moving-to-fixed direction expected by `DFBRegister`.
7. Route mask generation details to `image-preprocessing` and overlay rendering checks to `annotation-visualization`.

## Tiny Repro Path

When in doubt, reduce to `VirtualWSIReader`:

```python
import numpy as np
from tiatoolbox.wsicore.wsireader import WSIReader

img = np.zeros((64, 96, 3), dtype=np.uint8)
img[16:48, 24:72] = [200, 50, 80]
wsi = WSIReader.open(img, mpp=(0.5, 0.5))
print(wsi.info.as_dict())
print(wsi.read_rect((0, 0), (16, 16)).shape)
print(wsi.read_bounds((0, 0, 32, 32), resolution=1.0, units="baseline").shape)
```

If this works but a real WSI fails, the problem is likely file format support, native libraries, metadata, or requested read scale rather than the core read API.
