# WSI I/O Workflows

These recipes are self-contained patterns for TIAToolbox WSI reading and registration setup. Replace example paths with user data paths in downstream tasks.

## Inspect Metadata Before Reading

Use this before any expensive crop, tiling, or registration task.

```python
from tiatoolbox.wsicore.wsireader import WSIReader

wsi = WSIReader.open("slide.svs")
info = wsi.info

print(info.as_dict())
print("baseline dimensions:", info.slide_dimensions)
print("levels:", info.level_dimensions)
print("downsamples:", info.level_downsamples)
print("mpp:", info.mpp)
print("objective power:", info.objective_power)
```

Decision rules:

- If `info.mpp` exists, `units="mpp"` is a good choice for scale-stable workflows.
- If only `info.objective_power` exists, `units="power"` is acceptable for magnification-based reads.
- If neither scale field exists, use `units="level"` or `units="baseline"` and document that physical scale is unknown.
- If `level_dimensions` or `level_downsamples` look inconsistent, validate with one tiny read before a batch job.

## Choose `read_rect` or `read_bounds`

Use `read_rect` when the output array size must be fixed:

```python
patch = wsi.read_rect(
    location=(20_000, 12_000),
    size=(512, 512),
    resolution=0.5,
    units="mpp",
)
```

Use `read_bounds` when the baseline slide region must be fixed:

```python
roi = wsi.read_bounds(
    bounds=(20_000, 12_000, 22_048, 14_048),
    resolution=0.5,
    units="mpp",
)
```

If a user reports that crops show different tissue at different resolution settings, check whether they used `read_rect` when they expected `read_bounds`. `read_rect` keeps `(width, height)` fixed and changes field of view; `read_bounds` keeps the baseline field of view fixed and changes output size.

## Safe Crop With Missing Objective Power

When `objective_power` is missing, do not force `units="power"`. Use `mpp` if available; otherwise use `level` or `baseline`.

```python
info = wsi.info
bounds = (50_000, 40_000, 51_024, 41_024)

if info.mpp is not None:
    region = wsi.read_bounds(bounds, resolution=1.0, units="mpp")
elif info.level_count and info.level_count > 1:
    region = wsi.read_bounds(bounds, resolution=1, units="level")
else:
    region = wsi.read_bounds(bounds, resolution=1.0, units="baseline")
```

For a very large WSI, bound the request first:

```python
left, top, right, bottom = bounds
width = right - left
height = bottom - top
if width <= 0 or height <= 0:
    raise ValueError("Bounds must be (left, top, right, bottom) with positive size")
if width * height > 4_000_000:
    raise ValueError("Requested baseline field is too large for an interactive crop")
```

## Estimate Output Size Before Allocating

```python
size_at_mpp = wsi.slide_dimensions(resolution=1.0, units="mpp")
size_at_level = wsi.slide_dimensions(resolution=1, units="level")
print(size_at_mpp, size_at_level)
```

Use this before thumbnails at unusual resolutions, large `read_bounds` calls, or batch tile planning. If metadata is missing for the requested units, catch the error and switch units rather than guessing.

## Read Near Slide Edges

Out-of-bounds reads can be intentional for fixed-size model crops near edges. Choose padding behavior explicitly.

```python
edge_patch = wsi.read_rect(
    location=(-64, -64),
    size=(256, 256),
    resolution=0,
    units="level",
    pad_mode="reflect",
)
```

Use `pad_mode="constant"` when black/zero padding is desired; use `pad_mode="reflect"` when a model should not see artificial black borders near the edge.

## Create a Thumbnail

API:

```python
thumbnail = wsi.slide_thumbnail(resolution=1.25, units="power")
```

CLI:

```bash
tiatoolbox slide-thumbnail --img-input slide.svs --mode save --output-path thumbnails
```

If `objective_power` is unavailable, call `slide_thumbnail` with `units="baseline"` or a known `mpp` instead of the default power-based scale.

## Save Tiles Safely

API:

```python
wsi.save_tiles(
    output_dir="tiles",
    tile_objective_value=10,
    tile_read_size=(1024, 1024),
    tile_format=".jpg",
)
```

CLI:

```bash
tiatoolbox save-tiles --img-input slides/ --file-types "*.svs, *.ndpi" --tile-objective-value 10 --tile-read-size 1024 1024 --output-path tiles
```

Tile planning rules:

- Start with smaller `tile_read_size` during validation.
- Confirm `objective_power` exists before choosing `tile_objective_value`.
- Expect per-slide output directories with tile files plus tile metadata outputs.
- Route tissue-based tile filtering or patch extraction to `image-preprocessing`.

## Preserve Multichannel Data

For multiplex/OME/QPTIFF data, decide whether the user needs an RGB preview or raw channels.

RGB preview:

```python
wsi_rgb = WSIReader.open("multiplex.qptiff", post_proc="auto")
preview = wsi_rgb.read_rect((0, 0), (128, 128))
```

Raw channels:

```python
wsi_raw = WSIReader.open("multiplex.qptiff", post_proc=None)
channels = wsi_raw.read_rect((0, 0), (128, 128))
print(channels.shape)
```

For synthetic or in-memory feature arrays:

```python
import numpy as np
from tiatoolbox.wsicore.wsireader import VirtualWSIReader
from tiatoolbox.wsicore.wsimeta import WSIMeta

features = np.zeros((64, 64, 6), dtype=np.uint8)
meta = WSIMeta(slide_dimensions=(64, 64), axes="YXS", mpp=(0.5, 0.5))
wsi_features = VirtualWSIReader(features, info=meta, mode="feature", post_proc=None)
feature_crop = wsi_features.read_rect((0, 0), (16, 16), resolution=0, units="level")
```

## Register Two Images at Matched Scale

Read the fixed and moving images at the same physical scale and comparable field of view, then pass images and masks to `DFBRegister` in fixed-then-moving order.

```python
from tiatoolbox.tools.registration.wsi_registration import DFBRegister

fixed_img = fixed_wsi.read_bounds(fixed_bounds, resolution=2.5, units="power")
moving_img = moving_wsi.read_bounds(moving_bounds, resolution=2.5, units="power")

# Build masks through image-preprocessing guidance; arrays shown here are placeholders.
fixed_mask = fixed_img[..., 0] > 0
moving_mask = moving_img[..., 0] > 0

registrar = DFBRegister(patch_size=(224, 224))
transform = registrar.register(fixed_img, moving_img, fixed_mask, moving_mask)
```

Interpretation:

- `fixed_img` is the target/reference frame.
- `moving_img` is warped toward the fixed frame.
- If an overlay appears to move away from the target, swap diagnosis starts with argument order and transform direction, not with patch size.
- Use the same resolution units, similar tissue fields, and correctly paired masks before changing registration internals.

## Use the Bundled Smoke Check

```bash
python skills/disco/tiatoolbox/sub-skills/wsi-io/scripts/wsi_io_smoke.py --help
python skills/disco/tiatoolbox/sub-skills/wsi-io/scripts/wsi_io_smoke.py --mode tiny
```

The smoke check uses only `numpy` plus `VirtualWSIReader`; it does not download files or require a WSI fixture.
