# Image Workflows

This reference covers stable `squidpy.im` workflows for `ImageContainer`, image processing, segmentation, crops, and AnnData image features. It intentionally excludes experimental `squidpy.experimental.im` SpatialData tiling, tissue detection, stain, QC, stitching, and tile-feature APIs.

## Core Mental Model

- `ImageContainer` wraps an `xarray.Dataset` whose layers share spatial axes.
- Squidpy normalizes image layers to `(y, x, z, channels)` after ingestion. `z` stores library slices or z-stack positions; `channels` stores color or intensity channels.
- A layer is a named image entry such as `"image"`, `"image_smooth"`, `"image_gray"`, or `"segmentation"`. Use explicit `layer` and `layer_added` names in reusable code.
- `library_id` selects z slices. For Visium-like AnnData, image z labels should match `adata.uns["spatial"]` library ids and, for multi-library data, the observation-to-library mapping.
- `scale` maps image pixels to AnnData spatial coordinates. If crop centers are shifted or spot crops are blank, verify both `ImageContainer(..., scale=...)` and AnnData scalefactors.
- High-level image functions mutate by default and return `None`. Use `copy=True` when you need a returned `ImageContainer` or `DataFrame`.

## Construct an ImageContainer

Use generated arrays for deterministic, local workflows:

```python
import numpy as np
import squidpy as sq

rgb = np.zeros((64, 64, 3), dtype=np.float32)
rgb[20:40, 20:40, 0] = 1.0
img = sq.im.ImageContainer(rgb, layer="image", lazy=False, scale=1.0)
```

Accepted in-memory shapes are 2D, 3D, or 4D arrays. If a shape is ambiguous, pass `dims=` to `ImageContainer(...)` or `add_img(...)` so Squidpy knows which axes are `y`, `x`, `z`, and `channels`:

```python
# Grayscale: stored as (y, x, z=1, channels=1).
gray = sq.im.ImageContainer(np.zeros((32, 32)), layer="image")

# RGB channels-last: stored as (y, x, z=1, channels=3).
rgb = sq.im.ImageContainer(np.zeros((32, 32, 3)), layer="image")

# Explicit two-library stack.
stack = np.zeros((32, 32, 2, 3))
img = sq.im.ImageContainer(
    stack,
    layer="image",
    dims=("y", "x", "z", "channels"),
    library_id=["library_a", "library_b"],
)
```

Use `ImageContainer.from_adata(adata, img_key="hires", library_id=...)` when the image already lives in standard AnnData spatial metadata. Route local data reading and AnnData metadata construction to `datasets-and-io` before using this sub-skill.

## Add and Name Layers

Use `add_img` for additional aligned image layers:

```python
img.add_img(mask_array, layer="mask", dims=("y", "x"), lazy=False)
```

Layer rules:

- Added layers must align with existing `y`, `x`, and `z` coordinates.
- A different channel count is allowed; Squidpy may rename channel dimensions when channel coordinates cannot align.
- If there is exactly one layer and `layer=None`, high-level functions can infer it. Once multiple layers exist, always pass `layer=`.
- Prefer stable layer names: `"image"`, `"image_smooth"`, `"image_gray"`, `"segmentation"`.
- Do not rely on generated layer names for custom callables; pass `layer_added=`.

## Processing Recipes

`sq.im.process` applies transformations to a layer.

Smoothing:

```python
sq.im.process(
    img,
    layer="image",
    method="smooth",
    sigma=[1, 1, 0, 0],
    layer_added="image_smooth",
)
```

Grayscale conversion:

```python
sq.im.process(img, layer="image", method="gray", layer_added="image_gray")
```

Custom processing callback:

```python
def clip01(arr):
    return np.clip(arr, 0, 1)

sq.im.process(img, layer="image", method=clip01, layer_added="image_clipped")
```

Processing details:

- `method="smooth"` uses Gaussian filtering. When `library_id=None`, the callback sees the full `(y, x, z, channels)` layer and `sigma` must have length 4. When `library_id` selects z slices, callbacks see `(y, x, channels)` and `sigma` must have length 3.
- Integer `sigma` expands to spatial smoothing with zeros for non-spatial axes.
- `method="gray"` expects exactly 3 input channels and writes a one-channel layer.
- `apply_kwargs` is forwarded to `ImageContainer.apply`; use it for overlap depth or block behavior.
- `chunks=` enables dask block processing. `lazy=True` keeps output lazy where supported.
- With `copy=False`, processing mutates `img` and returns `None`. With `copy=True`, it returns a new container containing the processed layer.

## Segmentation Recipes

Watershed segmentation on one channel:

```python
sq.im.segment(
    img,
    layer="image_smooth",
    method="watershed",
    channel=0,
    thresh=0.2,
    geq=True,
    layer_added="segmentation",
)
```

Direct model object:

```python
model = sq.im.SegmentationWatershed()
sq.im.segment(img, layer="image", method=model, channel=0, layer_added="segmentation")
```

Custom segmentation callback:

```python
def simple_segment(arr):
    labels = np.zeros(arr.shape[:2], dtype=np.uint32)
    labels[arr[..., 0] > 0.5] = 1
    return labels

sq.im.segment(img, layer="image", method=simple_segment, channel=None, layer_added="segmentation")
```

Segmentation details:

- Public high-level segmentation uses `sq.im.segment` and model classes `SegmentationModel`, `SegmentationCustom`, and `SegmentationWatershed`.
- Built-in watershed cannot segment multiple channels at once. Pass `channel=0`, `channel=1`, etc. Use a custom callable with `channel=None` when all channels are needed.
- Custom segmentation functions receive `(height, width, channels)` after z/library and channel selection, and must return a 2D or 3D integer label mask.
- Background should be `0`; object labels should be positive integers. Squidpy stores valid segmentation outputs as unsigned integer masks.
- Segmentation outputs are image layers, not plots. Route overlays and rendering to `visualization`.
- For chunked segmentation, `chunks=`, overlap/depth kwargs, and label relabeling can affect boundary behavior. Validate on a small synthetic image or crop before whole-slide runs.

## Spot Crops and Image Features

`calculate_image_features` generates crops around AnnData observations with `ImageContainer.generate_spot_crops` and computes per-observation features.

Minimal AnnData feature extraction:

```python
import anndata as ad
import numpy as np
import squidpy as sq

adata = ad.AnnData(np.ones((2, 1), dtype=np.float32))
adata.obs_names = ["spot_a", "spot_b"]
adata.obsm["spatial"] = np.array([[16.0, 16.0], [32.0, 32.0]], dtype=np.float32)
adata.uns["spatial"] = {"library": {"scalefactors": {"spot_diameter_fullres": 9}}}

image = np.random.default_rng(0).random((48, 48, 3), dtype=np.float32)
img = sq.im.ImageContainer(image, layer="image", library_id="library", lazy=False, scale=1.0)
features = sq.im.calculate_image_features(
    adata,
    img,
    layer="image",
    library_id="library",
    features="summary",
    copy=True,
    n_jobs=1,
    show_progress_bar=False,
)
```

Feature categories:

- `summary`: per-channel mean, standard deviation, and quantiles.
- `histogram`: per-channel binned intensity counts.
- `texture`: gray-level co-occurrence texture features.
- `segmentation`: region properties from a label layer, usually after `sq.im.segment`.
- `custom`: user-defined feature function through `features_kwargs={"custom": {"func": ...}}`.

Feature workflow checklist:

1. Confirm `adata.obsm["spatial"]` exists and uses image-space coordinates.
2. Confirm `adata.uns["spatial"][library_id]["scalefactors"]["spot_diameter_fullres"]` exists, or pass a compatible `spot_diameter_key` and/or crop options.
3. Confirm `img.library_ids` match the AnnData library id or the observation library mapping.
4. Confirm image `scale` and AnnData scalefactors use the same coordinate system.
5. Confirm requested `layer` exists and `features` names are valid.
6. For segmentation features, ensure the label layer exists and pass `features_kwargs={"segmentation": {"label_layer": "segmentation", ...}}` when needed.
7. Use `copy=True` while debugging so the returned `DataFrame` can be inspected before writing to `adata.obsm[key_added]`.

## Cropping and Coordinates

Useful crop helpers:

- `crop_corner(y, x, size=..., library_id=..., scale=..., mask_circle=...)` extracts from an upper-left corner.
- `crop_center(y, x, radius=..., library_id=..., scale=..., mask_circle=...)` extracts a centered crop.
- `generate_equal_crops(size=...)` iterates over tiled crops and pads edge crops when needed.
- `generate_spot_crops(adata, spatial_key="spatial", library_id=..., spot_diameter_key="spot_diameter_fullres", spot_scale=...)` iterates crops around observations.
- `ImageContainer.uncrop(crops, shape=...)` reconstructs an image from compatible crop metadata.

When crops are scaled or padded, Squidpy stores crop coordinate and padding metadata in container attributes. Feature methods use this metadata for some segmentation-derived full-image coordinates.

## Lazy and Memory Practices

- File inputs and dask arrays can stay lazy. Use `ImageContainer(..., lazy=True)` for large files and compute only the layer needed by a downstream algorithm.
- `.values`, feature extraction, and many scikit-image algorithms materialize arrays. Avoid calling `.values` on whole-slide images unless the layer is small enough.
- For `process`, set `chunks=` for dask block processing; use `apply_kwargs={"depth": {0: y_overlap, 1: x_overlap}}` when a filter needs overlap.
- For `segment`, chunking uses overlap and label relabeling. Validate labels near block boundaries before trusting whole-slide chunked segmentation.
- For feature extraction, start with `n_jobs=1` and a subset of observations while debugging coordinate, crop, or layer issues.

## Smoke Script

The bundled `scripts/image_container_smoke.py` builds a tiny NumPy-backed workflow with no downloads, repository fixtures, or output files. Use it to check that a local Squidpy environment can construct, process, segment, and feature a small image.
