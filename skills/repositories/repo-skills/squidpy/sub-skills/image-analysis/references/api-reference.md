# Stable Image API Reference

This reference summarizes stable public `squidpy.im` APIs for image containers, processing, segmentation, and AnnData image features. Experimental `squidpy.experimental.im` APIs belong to `experimental-imaging`.

## Public Entry Points

`import squidpy as sq` exposes the stable image module as `sq.im`.

| API | Use |
| --- | --- |
| `sq.im.ImageContainer` | Store image layers in a shared `(y, x, z, channels)` container. |
| `sq.im.process` | Add processed image layers using smooth, gray, or custom callbacks. |
| `sq.im.segment` | Add segmentation mask layers using watershed, custom callables, or segmentation model objects. |
| `sq.im.calculate_image_features` | Compute per-observation image features into `AnnData.obsm` or return a table. |
| `sq.im.SegmentationModel` | Base class for segmentation models. |
| `sq.im.SegmentationCustom` | Adapter for custom segmentation callables. |
| `sq.im.SegmentationWatershed` | Watershed segmentation model used by `segment(..., method="watershed")`. |

## `ImageContainer`

Signature:

```python
squidpy.im.ImageContainer(img=None, layer="image", lazy=True, scale=1.0, **kwargs)
```

Purpose:

- Holds one or more image layers with shared spatial axes.
- Normalizes arrays to `(y, x, z, channels)`.
- Stores image-level attributes such as `scale`, crop coordinates, crop padding, and circular-mask state.
- Provides crop, compute, layer-management, and feature helper methods.

Important constructor and `add_img` arguments:

| Argument | Meaning |
| --- | --- |
| `img` | NumPy/dask array, `xarray.DataArray`, image path, Zarr/NetCDF store, URL to Zarr, or another compatible image object. |
| `layer` | Layer name to create; default is `"image"`. |
| `lazy` | Keep file/dask inputs lazy when possible. Set `False` for eager small-array workflows. |
| `scale` | Image-to-AnnData spatial coordinate scale factor. |
| `dims` | Explicit dimension names for ambiguous arrays. |
| `library_id` | Labels for z dimension; should match AnnData spatial library ids for spot crops/features. |
| `chunks` | Dask chunking for lazy loading or array-backed workflows. |

Common members:

| Member | Behavior |
| --- | --- |
| `img.data` | Underlying `xarray.Dataset`. |
| `img["layer"]` | Access an `xarray.DataArray` layer. |
| `layer in img` / `list(img)` | Inspect layer names. |
| `img.shape` | Spatial `(height, width)` shape. |
| `img.library_ids` | z-coordinate/library labels. |
| `img.add_img(...)` | Add or overwrite an aligned layer. |
| `img.compute(layer=None)` | Materialize dask-backed layers. |
| `img.copy(deep=False)` | Copy container and attributes. |
| `img.rename(old, new)` | Rename a layer in place and return the container. |
| `ImageContainer.from_adata(adata, img_key=None, library_id=None, spatial_key="spatial", **kwargs)` | Build a container from standard AnnData spatial image metadata. |
| `ImageContainer.concat(imgs, library_ids=...)` | Concatenate single-z containers along z/library dimension. |
| `ImageContainer.load(path, lazy=True, chunks=None)` / `img.save(path)` | Load or save container stores. |

Feature methods on `ImageContainer`:

| Method | Output |
| --- | --- |
| `features_summary(layer, quantiles=(0.9, 0.5, 0.1), channels=None, ...)` | Dict with per-channel quantile, mean, and std keys. |
| `features_histogram(layer, bins=10, v_range=None, channels=None, ...)` | Dict with per-channel histogram bin counts. |
| `features_texture(layer, props=..., distances=(1,), angles=..., channels=None, ...)` | Dict with GLCM texture properties. |
| `features_segmentation(label_layer, intensity_layer=None, props=("label", "area", "mean_intensity"), ...)` | Dict with region properties from a segmentation layer. |
| `features_custom(func, layer, channels=None, feature_name=None, **kwargs)` | Dict generated from a custom function returning a scalar or sequence. |

## `process`

Signature:

```python
squidpy.im.process(
    img,
    layer=None,
    library_id=None,
    method="smooth",
    chunks=None,
    lazy=False,
    layer_added=None,
    channel_dim=None,
    copy=False,
    apply_kwargs={},
    **kwargs,
)
```

Inputs:

- `img`: an `ImageContainer`.
- `layer`: source layer. If omitted, Squidpy resolves a default layer only when unambiguous.
- `library_id`: z/library id or ids to process separately. If omitted, all z slices are processed at once.
- `method`: `"smooth"`, `"gray"`, or a callable.
- `chunks`: dask chunk spec for block processing.
- `lazy`: keep output as dask array where supported.
- `layer_added`: output layer name. If omitted, Squidpy derives a name from source layer and method.
- `channel_dim`: output channel dimension name.
- `copy`: `False` mutates `img` and returns `None`; `True` returns a new `ImageContainer`.
- `apply_kwargs`: forwarded to `ImageContainer.apply`, useful for overlap depth.
- `kwargs`: method-specific options such as `sigma=` for smoothing.

Method behavior:

| Method | Notes |
| --- | --- |
| `"smooth"` | Gaussian smoothing. Default `sigma` is `[1, 1, 0, 0]` for full 4D layers or `[1, 1, 0]` when processing selected library ids. Integer `sigma` expands to spatial smoothing. |
| `"gray"` | Converts RGB to grayscale and expects exactly 3 input channels. |
| callable | Receives the selected layer array and must return an array with compatible dimensions. |

Common errors:

- Missing `layer` raises `KeyError`.
- Unknown `method` raises `NotImplementedError`.
- Wrong `sigma` length raises `ValueError`.
- `method="gray"` on non-RGB data raises a channel-dimension error.

## `segment`

Signature:

```python
squidpy.im.segment(
    img,
    layer=None,
    library_id=None,
    method="watershed",
    channel=0,
    chunks=None,
    lazy=False,
    layer_added=None,
    copy=False,
    **kwargs,
)
```

Inputs:

- `img`: an `ImageContainer`.
- `layer`: source image layer.
- `library_id`: z/library id or ids. If omitted, Squidpy segments each z slice separately.
- `method`: `"watershed"`, a `SegmentationModel`, or a callable.
- `channel`: source channel index; `None` passes all channels to custom segmentation.
- `chunks`: dask chunking for chunked segmentation.
- `lazy`: keep output lazy when supported.
- `layer_added`: output mask layer name. If omitted, Squidpy derives a segmentation name.
- `copy`: `False` mutates `img`; `True` returns a new container.
- `kwargs`: forwarded to the segmentation model. For watershed, common options are `thresh=` and `geq=`.

Model behavior:

| Method | Notes |
| --- | --- |
| `"watershed"` | Built-in threshold/watershed segmentation. Requires a single selected channel when the input has multiple channels. |
| callable | Wrapped as `SegmentationCustom`; callable receives `(height, width, channels)` and returns a 2D or 3D integer mask. |
| `SegmentationModel` | Custom model object implementing the segmentation protocol. |

Output:

- Segmentation is stored as an integer image layer.
- Background should be `0`; object labels are positive integers.
- Output keeps image spatial dimensions and z/library coordinates.
- With `copy=True`, the returned container has the segmentation layer. With `copy=False`, inspect the original container.

Common errors:

- Direct model segmentation accepts only 2D or 3D arrays; pass 4D image data through `sq.im.segment` rather than directly to `SegmentationCustom.segment`.
- Watershed with `channel=None` on a multi-channel layer raises `ValueError`.
- Custom callables that return non-integer masks raise `TypeError`.
- Unsupported method strings raise `NotImplementedError`.

## `calculate_image_features`

Signature:

```python
squidpy.im.calculate_image_features(
    adata,
    img,
    layer=None,
    library_id=None,
    features="summary",
    features_kwargs={},
    key_added="img_features",
    copy=False,
    n_jobs=None,
    backend="loky",
    show_progress_bar=True,
    **kwargs,
)
```

Inputs:

- `adata`: AnnData with observation names and spatial coordinates.
- `img`: `ImageContainer` aligned to the AnnData coordinate system.
- `layer`: image layer to crop and feature.
- `library_id`: image z/library id or ids. Needed when automatic library resolution is ambiguous.
- `features`: one feature name or a sequence of feature names.
- `features_kwargs`: nested mapping by feature name with options for each feature method.
- `key_added`: `adata.obsm` key when `copy=False`.
- `copy`: `True` returns a `pandas.DataFrame`; `False` writes to `adata.obsm[key_added]`.
- `n_jobs`, `backend`, `show_progress_bar`: parallel execution controls.
- `**kwargs`: crop options forwarded to `ImageContainer.generate_spot_crops`, such as `spatial_key`, `spot_diameter_key`, `spot_scale`, and `mask_circle`.

Feature names:

| Feature | Underlying method | Typical `features_kwargs` |
| --- | --- | --- |
| `"summary"` | `ImageContainer.features_summary` | `{"channels": [0], "quantiles": (0.5,)}` |
| `"histogram"` | `ImageContainer.features_histogram` | `{"channels": [0], "bins": 8}` |
| `"texture"` | `ImageContainer.features_texture` | `{"channels": [0], "distances": (1,), "angles": (0,)}` |
| `"segmentation"` | `ImageContainer.features_segmentation` | `{"label_layer": "segmentation", "intensity_layer": "image", "props": ["label", "area"]}` |
| `"custom"` | `ImageContainer.features_custom` | `{"func": callable, "channels": [0], "feature_name": "my_feature"}` |

Output:

- With `copy=True`, returns a `pandas.DataFrame` indexed by `adata.obs_names`.
- With `copy=False`, writes that DataFrame to `adata.obsm[key_added]` and returns `None`.

Preconditions:

- `adata.obsm[spatial_key]` must exist and contain image-space observation coordinates.
- `adata.uns["spatial"]` must contain a usable library entry and `spot_diameter_fullres`, or the caller must pass compatible crop options.
- `img.library_ids` should match the AnnData library id when library-specific crops are needed.
- Image and AnnData scales must agree; otherwise crops can be empty, off-target, or padded.

## `SegmentationCustom` and `SegmentationWatershed`

Custom callable contract:

```python
def segment_func(arr):
    # arr has shape (height, width, channels)
    labels = np.zeros(arr.shape[:2], dtype=np.uint32)
    labels[arr[..., 0] > 0.5] = 1
    return labels
```

Use it directly through the high-level wrapper:

```python
sq.im.segment(img, layer="image", method=segment_func, channel=None, layer_added="segmentation")
```

Or wrap it explicitly:

```python
model = sq.im.SegmentationCustom(segment_func)
sq.im.segment(img, layer="image", method=model, channel=None, layer_added="segmentation")
```

Use `sq.im.SegmentationWatershed()` directly only when a task needs a configured model object. For ordinary watershed segmentation, prefer `sq.im.segment(..., method="watershed", channel=0, ...)`.

## Stable vs Experimental Feature APIs

Do not confuse these APIs:

- Stable AnnData/ImageContainer feature API: `squidpy.im.calculate_image_features(adata, img, ...)`.
- Experimental SpatialData feature API: `squidpy.experimental.im.calculate_image_features(sdata, image_key=..., labels_key=..., tile_size=..., ...)`.

If the user mentions `SpatialData`, labels/shapes keys, tile size, tissue masks, stain normalization, image QC, or stitching, route to `experimental-imaging` instead of this sub-skill.
