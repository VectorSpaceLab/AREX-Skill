# Image Troubleshooting

Use this guide when stable `squidpy.im` workflows fail or produce surprising layers, masks, crops, or feature tables.

## Unsupported or Ambiguous Image Dimensionality

Symptoms:

- `ValueError` about expecting a 2D, 3D, or 4D image.
- Stored image shape or orientation does not match the input array.
- Segmentation fails after passing a raw 4D array directly to a segmentation model.

Checks and fixes:

1. Inspect the raw array shape before constructing an `ImageContainer`.
2. For ambiguous 3D or 4D arrays, pass explicit dimensions:

```python
img = sq.im.ImageContainer(arr, dims=("y", "x", "z", "channels"), layer="image")
```

3. Remember that Squidpy stores layers as `(y, x, z, channels)` even if input files or arrays arrive in another order.
4. Verify normalization with `img["image"].dims`, `img["image"].shape`, `img.shape`, and `img.library_ids`.
5. Do not call `SegmentationCustom(...).segment(raw_4d_array)` directly. Use `sq.im.segment(img, layer=..., channel=...)`, which selects z/library and channels before calling the model.

## Missing or Wrong Image Layers

Symptoms:

- `KeyError` for a missing image layer.
- A function processes or segments the wrong layer after earlier steps added layers.
- A layer appears missing after using `copy=True`.

Checks and fixes:

1. List layers with `list(img)`.
2. Pass `layer=` explicitly whenever the container has more than one layer.
3. Pass `layer_added=` explicitly for reusable code and custom callables.
4. Confirm whether the previous call used `copy=True` or mutated in place:

```python
out = sq.im.process(img, layer="image", method="smooth", copy=True, layer_added="image_smooth")
# The processed layer is in out, not img.
```

5. If `copy=False`, the function returns `None`; inspect the original container.

## Channel and `channel_dim` Confusion

Symptoms:

- Grayscale conversion fails because the channel dimension is not length 3.
- Watershed segmentation fails because it received multiple channels.
- Feature extraction raises an invalid-channel error.
- New layers have channel dimensions such as `channels:0`, `channels:all`, or renamed channel axes.

Checks and fixes:

1. Inspect `img[layer].dims` and `img[layer].shape[-1]`.
2. Use `method="gray"` only for RGB-like three-channel layers.
3. For watershed, pass a single channel:

```python
sq.im.segment(img, layer="image", method="watershed", channel=0, layer_added="segmentation")
```

4. For multi-channel segmentation, use a custom callable and `channel=None`:

```python
def segment_all_channels(arr):
    labels = np.zeros(arr.shape[:2], dtype=np.uint32)
    labels[arr.mean(axis=-1) > 0.5] = 1
    return labels

sq.im.segment(img, layer="image", method=segment_all_channels, channel=None, layer_added="segmentation")
```

5. For feature methods, pass existing integer channel indices such as `channels=[0, 1]`.
6. If a processing callback changes channel count, pass `channel_dim=` to preserve clear output semantics.

## Segmentation Method and Dtype Errors

Symptoms:

- `ValueError: Watershed segmentation does not work with multiple channels.`
- `ValueError` about expected 2D or 3D arrays.
- `TypeError` about expected integer segmentation dtype.
- Empty or all-zero masks.
- Objects split differently at chunk boundaries.

Checks and fixes:

1. For built-in watershed, select one channel and tune `thresh=` and `geq=`:

```python
sq.im.segment(
    img,
    layer="image",
    method="watershed",
    channel=0,
    thresh=0.2,
    geq=True,
    layer_added="segmentation",
)
```

2. If low values are foreground and high values are background, try `geq=False`.
3. For custom segmentation, return a 2D or 3D integer array, preferably `np.uint32`, with background `0`.
4. If segmenting dask-backed images, validate the callable on a small eager crop first.
5. If chunked labels look duplicated or split, increase overlap depth, reduce chunk size, or segment smaller image regions eagerly.
6. Confirm the segmentation layer was created in the expected container: `copy=True` returns a new container; `copy=False` mutates the original.

## Crop and Image Scale Mismatch

Symptoms:

- Spot crops are blank, padded, shifted, or clipped.
- Feature values are all zero, `NaN`, or biologically implausible.
- Crophood coordinates look correct in AnnData but wrong on the image.

Checks and fixes:

1. Confirm `adata.obsm["spatial"]` exists and uses image pixel coordinates expected by Squidpy.
2. Confirm the image was built with the intended `scale=` or from AnnData metadata containing the right scalefactor.
3. Confirm `adata.uns["spatial"][library_id]["scalefactors"]["spot_diameter_fullres"]` exists, or pass a compatible `spot_diameter_key` and crop options.
4. Compare one known observation coordinate to the expected image pixel location before batch feature extraction.
5. Inspect a few crops before computing all features:

```python
crops = list(img.generate_spot_crops(adata, obs_names=adata.obs_names[:3], library_id="library", as_array=False))
print([crop.shape for crop in crops])
```

6. If working with a cropped image, remember that crop metadata and scale must remain compatible with the AnnData coordinates.

## Feature Table Is Empty, Missing, or Misaligned

Symptoms:

- `adata.obsm[key_added]` is absent after feature extraction.
- Returned table has expected rows but no useful columns.
- Feature rows do not align with observations.
- Segmentation feature columns are missing or unexpected.

Checks and fixes:

1. Confirm copy behavior:

```python
features = sq.im.calculate_image_features(adata, img, features="summary", copy=True, n_jobs=1)
# With copy=False, inspect adata.obsm[key_added] instead.
```

2. Confirm `adata.obs_names` are unique and the returned `DataFrame` index matches them.
3. Confirm requested `features` values are one or more of `"summary"`, `"histogram"`, `"texture"`, `"segmentation"`, or `"custom"`.
4. Confirm `layer=` exists and is the intended intensity layer.
5. For segmentation features, name the label and intensity layers explicitly:

```python
features = sq.im.calculate_image_features(
    adata,
    img,
    layer="image",
    features="segmentation",
    features_kwargs={
        "segmentation": {
            "label_layer": "segmentation",
            "intensity_layer": "image",
            "props": ["label", "area"],
        }
    },
    copy=True,
    n_jobs=1,
)
```

6. Set `n_jobs=1` and `show_progress_bar=False` while debugging; increase parallelism only after geometry and layers are correct.

## Library ID and Z-Dimension Problems

Symptoms:

- Ambiguous library-id errors.
- Errors about expected z dimensions when adding layers.
- Crops or features use the wrong library image.

Checks and fixes:

1. Inspect `img.library_ids` and `adata.uns["spatial"].keys()`.
2. For single-library workflows, pass `library_id="library"` during image construction and feature calls when ambiguity appears.
3. For multiple libraries, construct one single-z container per image and combine with `ImageContainer.concat(..., library_ids=[...])`.
4. When adding layers to a multi-library container, the new layer must have the same z dimension length or an explicitly compatible `library_id`.
5. When AnnData has multiple libraries, ensure observations can be mapped to library ids or subset to one library and pass `library_id=`.

## Lazy, Dask, Chunks, and Memory

Symptoms:

- Operations unexpectedly trigger large computation.
- Output remains dask-backed after a function call.
- Chunked segmentation has boundary artifacts.
- Processing is slow or memory spikes.

Checks and fixes:

1. Inspect `type(img[layer].data)` to see whether a layer is dask-backed.
2. Use `lazy=True` to keep output lazy where supported, but remember that `.values`, feature extraction, and scikit-image algorithms may materialize data.
3. Use `img.compute(layer)` to materialize only one layer instead of all layers.
4. Use `chunks=` for large image processing. For filters, pass `apply_kwargs={"depth": {0: y_overlap, 1: x_overlap}}` if boundaries matter.
5. Start segmentation and features on a small crop or selected observations before running a whole slide.
6. Avoid full-slide `.values` calls in diagnostics; prefer crops, selected channels, selected libraries, and observation subsets.

## Quick Diagnostic Checklist

Run these checks before changing code:

```python
print(list(img))
print(img.shape)
print(img.library_ids)
print(img["image"].dims, img["image"].shape, img["image"].dtype)
print(adata.obsm.keys())
print(adata.uns.get("spatial", {}).keys())
```

Then verify:

- The source layer exists.
- The channel index is valid.
- `library_id` matches image z labels and AnnData metadata.
- `scale` and `spot_diameter_fullres` are compatible.
- The function's `copy` mode matches where you are inspecting results.
- Large-image code avoids accidental whole-layer materialization.
