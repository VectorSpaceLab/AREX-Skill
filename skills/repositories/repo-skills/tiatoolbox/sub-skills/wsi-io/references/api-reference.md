# WSI I/O API Reference

This reference covers TIAToolbox whole-slide/image reading surfaces: reader selection, metadata, resolution handling, region reads, thumbnails, tiles, multichannel behavior, CLI wrappers, and registration setup.

## Reader Selection

Prefer `WSIReader.open(...)` unless a task specifically needs one reader class.

| Surface | Use when | Notes |
| --- | --- | --- |
| `WSIReader.open(input_img, mpp=None, power=None, post_proc="auto", **kwargs)` | General entry point for paths, arrays, and existing readers | Dispatches based on input type and file format. If passed an existing `WSIReader`, it returns it unchanged. |
| `OpenSlideWSIReader(input_img, mpp=None, power=None, post_proc="auto")` | Explicit OpenSlide-backed reads for common WSI formats such as SVS, NDPI, MRXS, and compatible TIFF | Requires native OpenSlide support to be installed and able to open the file. |
| `VirtualWSIReader(input_img, mpp=None, power=None, info=None, mode="rgb", post_proc="auto")` | Numpy arrays, small RGB images, masks, thumbnails, and synthetic fixtures | Uses a single image as a virtual WSI. Can carry custom `WSIMeta` for virtual baseline dimensions and scale. |
| `WSIMeta(...)` | Construct or override metadata for virtual reads, masks, features, or missing slide metadata | Required fields are `slide_dimensions` and `axes`; scale metadata is optional but important for `mpp`/`power` reads. |

`WSIReader.open` recognizes path-like WSI/image inputs including OpenSlide formats, TIFF/OME-TIFF/QPTIFF, JP2, NGFF Zarr, DICOM WSI, fsspec JSON, annotation-store DB, common image files, and `.npy` arrays when supported by the installed optional dependencies.

## Metadata Model

`wsi.info` returns a cached `WSIMeta` object. Use `wsi.info.as_dict()` when a serializable metadata summary is needed.

Key `WSIMeta` fields:

- `slide_dimensions`: `(width, height)` for baseline/full-resolution coordinates.
- `axes`: axis ordering, usually `"YXS"`; valid axis characters are `Y`, `X`, `S`, `T`, and `Z`.
- `level_dimensions`: list of `(width, height)` per pyramid/resolution level.
- `level_downsamples`: scale factors relative to baseline; level `0` is baseline and normally has downsample `1.0`.
- `level_count`: number of levels; defaults from `level_dimensions` when omitted.
- `objective_power`: scanner objective magnification, if known.
- `mpp`: `(x, y)` microns per pixel, if known; may be manually supplied to a reader.
- `vendor`, `file_path`, `raw`: scanner and raw metadata details when available.

Validation warnings are actionable: missing `mpp`/`objective_power` means `mpp` or `power` unit reads may fail or be ambiguous; inconsistent levels/downsamples mean resolution-dependent reads need extra caution.

## Resolution Units

TIAToolbox read methods accept `resolution` plus `units`:

| Unit | Meaning | Good choice when |
| --- | --- | --- |
| `"level"` | Pyramid/resolution level. `0` is baseline; integer levels use stored levels; fractional levels interpolate between downsample factors. | You know the WSI pyramid level or want metadata-independent reads. |
| `"mpp"` | Microns per pixel. Can be scalar or `(x, y)`. Lower mpp means higher resolution. | Physical scale is important and `wsi.info.mpp` is known or supplied. |
| `"power"` | Objective magnification. Higher power means higher resolution. | Working in pathologist/scanner magnification and `objective_power` is known or supplied. |
| `"baseline"` | Scale relative to baseline pixels. `1.0` is full resolution; `0.5` is half the baseline linear resolution. | Metadata is missing or you want an explicit pixel-scale ratio. |

Use `wsi.convert_resolution_units(input_res, input_unit, output_unit=None)` to convert between units. Conversions to `mpp` require baseline `mpp`; conversions to `power` require `objective_power`. If both are missing, use `units="baseline"` or `units="level"` rather than guessing.

Use `wsi.slide_dimensions(resolution, units)` to estimate output slide size at a requested resolution before allocating arrays or scheduling expensive work.

## Region Read Semantics

Choose the read API by what must stay fixed:

| API | Coordinates | Output size | Field of view | Use for |
| --- | --- | --- | --- | --- |
| `read_rect(location, size, resolution=0, units="level", ...)` | `location=(x, y)` in baseline by default | Exactly `size=(width, height)` | Changes as resolution changes | Model input patches, fixed-size crops, OpenSlide-like patch reads with TIAToolbox units. |
| `read_bounds(bounds, resolution=0, units="level", ...)` | `bounds=(left, top, right, bottom)` in baseline by default | Changes with resolution | Fixed baseline field of view | ROI export, annotations-aligned regions, visual comparisons across levels. |
| `read_region(location, level, size)` | OpenSlide-compatible arguments | Exactly `size` | Level-based | Porting OpenSlide code; internally maps to `read_rect(..., units="level")`. |
| `read_rect_at_resolution(location, size, resolution, units, ...)` | Location and size in requested resolution space | Exactly requested-resolution size | Equivalent to `read_bounds(..., coord_space="resolution")` | When incoming coordinates are already at the requested output resolution. |

Both `read_rect` and `read_bounds` support `interpolation` values such as `"optimise"`, `"linear"`, `"cubic"`, `"lanczos"`, and `"area"`, plus padding controls such as `pad_mode` and `pad_constant_values`. `coord_space="baseline"` is the default; use `coord_space="resolution"` only when bounds or locations are already expressed at the requested resolution.

Safe crop checklist:

1. Inspect `wsi.info.slide_dimensions`, `level_downsamples`, `mpp`, and `objective_power`.
2. Pick units: prefer `mpp` or `power` only when metadata exists; otherwise choose `level` or `baseline`.
3. For fixed model inputs, use `read_rect`; for fixed tissue/annotation extent, use `read_bounds`.
4. Keep patch/region dimensions small enough to fit memory after scaling.
5. Decide edge behavior: default constant padding may introduce black borders; `pad_mode="reflect"` can be useful near slide edges.

## Thumbnails and Tiles

- `wsi.slide_thumbnail(resolution=1.25, units="power")` reads the whole slide via `read_bounds((0, 0, *slide_dimensions), ...)`.
- `wsi.save_tiles(output_dir="tiles", tile_objective_value=20, tile_read_size=(5000, 5000), tile_format=".jpg", verbose=False)` writes a per-slide tile directory with thumbnail and metadata CSV outputs.
- `tile_objective_value` depends on `objective_power`; if objective metadata is missing, set or avoid power-based tiling.
- Large `tile_read_size` values can create huge intermediate reads. Start smaller for validation and increase only after checking output counts.

## Multichannel and Virtual Reads

Multichannel behavior depends on reader and `post_proc`:

- For multiplex TIFF/QPTIFF/OME-TIFF reads, `post_proc="auto"` may convert multichannel data to RGB using TIAToolbox post-processing; set `post_proc=None` to preserve raw channels for quantitative work.
- For `VirtualWSIReader` arrays with non-RGB channel counts, the reader can switch to feature mode and preserve native channel count unless a post-processing function is explicitly applied.
- Preserve channel semantics by recording `axes`, channel order, and any dye/channel metadata in workflow notes. `WSIMeta.axes="YXS"` means image coordinates are `Y`, `X`, then samples/channels.
- For binary masks, use `VirtualWSIReader(..., mode="bool")` so nearest-neighbor behavior is used where appropriate.
- For feature maps, use `mode="feature"` or let non-RGB array shape trigger feature-mode warnings.

## CLI Entry Points

The console entry point is `tiatoolbox`. Exact shared option catalogs belong in `cli-and-configuration`; WSI-specific examples are:

```bash
tiatoolbox slide-info --img-input slide.svs --mode show
```

```bash
tiatoolbox slide-thumbnail --img-input slides/ --file-types "*.svs, *.ndpi" --output-path thumbnails
```

```bash
tiatoolbox read-bounds --img-input slide.svs --region 1000 2000 2500 3500 --resolution 0.5 --units mpp --mode save --output-path roi.jpg
```

```bash
tiatoolbox save-tiles --img-input slides/ --file-types "*.svs, *.ndpi" --tile-objective-value 10 --tile-read-size 1024 1024 --tile-format .jpg --output-path tiles
```

CLI defaults mirror the API: `read-bounds` uses `--resolution 0`, `--units level`, and a default region when none is supplied; `slide-thumbnail` saves thumbnails by default; `slide-info` shows metadata by default; `save-tiles` writes tiles.

## Registration Setup

`DFBRegister(patch_size=(224, 224))` aligns a moving image to a fixed image:

```python
from tiatoolbox.tools.registration.wsi_registration import DFBRegister

registrar = DFBRegister(patch_size=(224, 224))
transform = registrar.register(fixed_img, moving_img, fixed_mask, moving_mask)
```

Requirements and routing:

- `fixed_img` and `moving_img` must be RGB arrays shaped `(height, width, 3)`.
- `fixed_mask` and `moving_mask` are binary tissue masks; 3D masks are squeezed to their first channel internally.
- The returned affine transform maps/warps the moving image toward the fixed image frame. If overlays move in the wrong direction, verify source/target ordering before tuning registration parameters.
- Build input images with `read_bounds` or thumbnails at the same physical resolution and comparable field of view before registration.
- Route mask construction details to `image-preprocessing`; route visualization overlays to `annotation-visualization`.
