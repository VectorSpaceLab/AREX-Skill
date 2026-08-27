# Experimental Imaging API Reference

Import Squidpy as `import squidpy as sq`. Experimental imaging entry points live under `sq.experimental.im`, `sq.experimental.tl`, and `sq.experimental.pl`.

These APIs are intentionally separated from stable `sq.im.ImageContainer` workflows. Route stable image-container tasks to `image-analysis`.

## Public Experimental Image APIs

| API | Purpose | Primary output |
| --- | --- | --- |
| `sq.experimental.im.detect_tissue` | Detect tissue regions from a SpatialData image | mask in `sdata.labels[...]` or returned NumPy mask |
| `sq.experimental.im.make_tiles` | Create regular image tiles and classify tissue coverage | polygons in `sdata.shapes[...]` |
| `sq.experimental.im.make_tiles_from_spots` | Create Visium spot-centered tiles | polygons in `sdata.shapes[...]`, optional spot classification |
| `sq.experimental.im.qc_image` | Compute tile-based image QC scores | table in `sdata.tables[...]`, grid in `sdata.shapes[...]` |
| `sq.experimental.im.calculate_image_features` | Compute per-cell image/label features from SpatialData | SpatialData-linked AnnData table or returned AnnData |
| `sq.experimental.im.fit_stain_reference` | Fit Reinhard, Macenko, or Vahadane reference | `StainReference` |
| `sq.experimental.im.normalize_stains` | Normalize RGB image to a fitted reference | image in `sdata.images[...]` or returned DataArray |
| `sq.experimental.im.decompose_stains` | Project image into per-stain concentration maps | one image per stain or returned dict |
| `sq.experimental.im.estimate_white_point` | Estimate background white point from non-tissue pixels | shape `(3,)` NumPy array |

## Public Experimental Tool/Plot APIs

| API | Purpose | Primary output |
| --- | --- | --- |
| `sq.experimental.tl.calculate_tiling_qc` | Score cells for tile-boundary segmentation artifacts | QC AnnData table in `sdata.tables[...]` or returned AnnData |
| `sq.experimental.tl.assign_stitch_groups` | Annotate likely pieces of cut cells that should be stitched | columns added to the QC table or returned AnnData |
| `sq.experimental.pl.qc_image` | Plot summary panels from `im.qc_image` results | Matplotlib axes or displayed figure |
| `sq.experimental.pl.tiling_qc` | Plot labels colored by tiling QC scores | displayed figure |

## Tissue Detection

Signature:

```python
sq.experimental.im.detect_tissue(
    sdata,
    image_key,
    *,
    scale="auto",
    method="otsu",
    method_params=None,
    channel_format="infer",
    background_detection_params=None,
    corners_are_background=True,
    border_margin_px=0,
    min_specimen_area_frac=0.01,
    n_samples=None,
    auto_max_pixels=5_000_000,
    close_holes_smaller_than_frac=0.0001,
    mask_smoothing_cycles=0,
    new_labels_key=None,
    inplace=True,
)
```

Behavior and outputs:

- `image_key` must name an image in `sdata.images`.
- `scale="auto"` chooses the smallest available scale for processing; pass an explicit scale when reproducibility matters.
- `new_labels_key=None` defaults to a derived tissue key; choose an explicit key such as `"image_tissue"` in automation.
- `inplace=True` writes a labels element and returns `None`; `inplace=False` returns a NumPy mask.
- `channel_format` can be `"infer"`, `"rgb"`, `"rgba"`, or `"multichannel"`.

Related dataclasses:

| Dataclass | Fields | Use |
| --- | --- | --- |
| `BackgroundDetectionParams` | `ymin_xmin_is_bg=True`, `ymax_xmin_is_bg=True`, `ymin_xmax_is_bg=True`, `ymax_xmax_is_bg=True`, `corner_size_pct=0.01` | Mark which image corners are background and how large corner boxes are. |
| `FelzenszwalbParams` | `grid_rows=100`, `grid_cols=100`, `sigma_frac=0.008`, `scale_coef=0.25`, `min_size_coef=0.20` | Tune superpixel segmentation when `method="felzenszwalb"`. |
| `WekaParams` | `sigma_min=1.0`, `sigma_max=16.0`, `edges=True`, `pseudo_tissue_percentile=90.0`, `pseudo_min_pixels=50`, `rf_estimators=100`, `rf_max_depth=10`, `rf_max_samples=0.05`, `random_state=0`, `refine_with_classifier=True`, `refine_n_samples_per_class=50000`, `refine_bg_prob_threshold=0.6` | Tune WEKA-like trainable segmentation when `method="weka"`. |

Validation notes:

- Passing `method_params` with `method="otsu"` is not supported.
- `border_margin_px` accepts an int or `(top, bottom, left, right)` sequence; negative values are rejected.
- `min_specimen_area_frac`, `close_holes_smaller_than_frac`, and smoothing parameters can strongly alter small tissue islands.

## Tile Generation

Regular grid signature:

```python
sq.experimental.im.make_tiles(
    sdata,
    image_key,
    *,
    image_mask_key=None,
    tissue_mask_key=None,
    tile_size=(224, 224),
    center_grid_on_tissue=False,
    scale="auto",
    min_tissue_fraction=1.0,
    new_shapes_key=None,
    preview=True,
)
```

Spot-centered signature:

```python
sq.experimental.im.make_tiles_from_spots(
    sdata,
    *,
    spots_key,
    image_key=None,
    tissue_mask_key=None,
    scale="auto",
    min_tissue_fraction=1.0,
    new_shapes_key=None,
    preview=True,
)
```

Behavior and outputs:

- `make_tiles` writes a tile grid to `sdata.shapes[new_shapes_key]`; the default key is based on `image_key`.
- `make_tiles_from_spots` reads `sdata.shapes[spots_key]`, derives square tiles from spot spacing, writes tile polygons, and can propagate `tile_classification` to the spot shapes.
- Tile grid columns include `pixel_y0`, `pixel_x0`, `pixel_y1`, `pixel_x1`, and `tile_classification`.
- `tile_size` is `(height, width)` in pixels on the largest image scale.
- `scale="auto"` chooses a labels scale closest to the full-resolution image when reading masks.
- If a tissue mask is missing, the functions can invoke `detect_tissue` to create the default mask; for predictable workflows, run tissue detection explicitly first.

## Image QC

Signature:

```python
sq.experimental.im.qc_image(
    sdata,
    image_key,
    *,
    scale="scale0",
    metrics=None,
    tile_size="auto",
    is_hne=True,
    detect_outliers=True,
    detect_tissue=True,
    outlier_threshold=0.1,
    progress=True,
    tissue_mask_key=None,
    preview=True,
)
```

Metric enum values from `sq.experimental.im.QCMetric`:

| Category | Metrics |
| --- | --- |
| Sharpness | `TENENGRAD`, `VAR_OF_LAPLACIAN`, `VARIANCE`, `FFT_HIGH_FREQ_ENERGY`, `HAAR_WAVELET_ENERGY` |
| Intensity | `BRIGHTNESS_MEAN`, `BRIGHTNESS_STD`, `ENTROPY` |
| H&E staining | `HEMATOXYLIN_MEAN`, `HEMATOXYLIN_STD`, `EOSIN_MEAN`, `EOSIN_STD`, `HE_RATIO` |
| H&E artifacts | `FOLD_FRACTION` |
| Tissue coverage | `TISSUE_FRACTION` |

Behavior and outputs:

- `metrics=None` uses H&E defaults when `is_hne=True`, and generic sharpness/intensity defaults when `is_hne=False`.
- H&E-only metrics are rejected when `is_hne=False`.
- `outlier_threshold` must be in `(0, 1)`; `0.1` flags the worst 10% of tissue tiles by sharpness-derived unfocus score.
- Output table key is `f"qc_img_{image_key}"`.
- Output shape key is `f"qc_img_{image_key}_grid"`.
- Metadata is recorded in `sdata.tables[table_key].uns['qc_image']`.

Plot signature:

```python
sq.experimental.pl.qc_image(
    sdata,
    image_key,
    metrics=None,
    figsize=None,
    return_ax=False,
    **kwargs,
)
```

Use `return_ax=True` when a caller needs to customize or test the Matplotlib axes.

## Experimental Image Features

Signature:

```python
sq.experimental.im.calculate_image_features(
    sdata,
    image_key=None,
    labels_key=None,
    shapes_key=None,
    scale=None,
    channels=None,
    features=None,
    tile_size=2048,
    overlap_margin="auto",
    align_mode="strict",
    adata_key_added="morphology",
    invalid_as_zero=True,
    n_jobs=1,
    inplace=True,
)
```

Inputs:

- `sdata`: SpatialData object with images, labels, and optionally shapes/tables.
- `image_key`: image element used for intensity, summary, texture, and color features; morphology-only runs can omit image input when labels are sufficient.
- `labels_key`: segmentation labels element. Use integer labels where background is `0` and cells are positive ids.
- `shapes_key`: optional shapes element for region alignment or ownership.
- `scale`: image/label scale. Use explicit scale when images and labels are multiscale.
- `channels`: channel names to select; use names from the SpatialData image when available.
- `features`: required explicit feature string or list.

Supported feature names:

| Feature request | Meaning |
| --- | --- |
| `skimage:morphology` | All supported morphology `regionprops` fields. |
| `skimage:morphology:<prop>` | One morphology property such as `area`, `eccentricity`, or `perimeter`. |
| `skimage:intensity` | All supported intensity properties. |
| `skimage:intensity:<prop>` | One intensity property such as `intensity_mean`. |
| `squidpy:summary` | Squidpy-native per-cell summary statistics. |
| `squidpy:texture` | GLCM texture-style features. |
| `squidpy:color_hist` | Color histogram features. |

Output:

- `inplace=True` writes a SpatialData-linked AnnData table with feature columns and returns `None`.
- `inplace=False` returns an AnnData object.
- `invalid_as_zero=True` replaces invalid feature values with zero; set `False` if NaNs should remain visible for QC.
- `n_jobs` controls joblib parallelism; use `1` for deterministic debugging.

## Stain Dataclasses

`StainReference` signature:

```python
sq.experimental.im.StainReference(
    method,
    stain_matrix=None,
    mu=None,
    sigma=None,
    white_point=None,
    max_concentrations=None,
)
```

Validation rules:

- `method` must be `"macenko"`, `"vahadane"`, or `"reinhard"`.
- Macenko/Vahadane references require `stain_matrix` shape `(3, 3)` and strictly positive `white_point` shape `(3,)`.
- Macenko/Vahadane references forbid `mu` and `sigma`.
- Reinhard references require finite `mu` and strictly positive `sigma`, both shape `(3,)`.
- Reinhard references forbid `stain_matrix`, `white_point`, and `max_concentrations`.

Parameter dataclasses:

| Dataclass | Signature | Validation/use |
| --- | --- | --- |
| `ReinhardParams` | `(luminosity_threshold=0.8, mask_background=True)` | Threshold must be in `(0, 1]`; controls Ruderman Lab tissue-statistics fit. |
| `MacenkoParams` | `(alpha=1.0, beta=0.15)` | `alpha` must be in `(0, 50)` and `beta >= 0`; controls angular percentiles and absorbance tissue cutoff. |
| `VahadaneParams` | `(beta=0.15, lambda1=0.1, n_iter=200, random_state=0)` | `beta >= 0`, `lambda1 >= 0`, `n_iter >= 1`; controls sparse NMF fit. |

Mappings with matching field names are accepted anywhere `method_params`, `tiling_qc_params`, or `stitch_params` are accepted. Unknown fields raise `ValueError`.

## Stain Fitting, Normalization, And Decomposition

Fit signature:

```python
sq.experimental.im.fit_stain_reference(
    sdata,
    image_key,
    *,
    method="macenko",
    scale="auto",
    method_params=None,
    white_point=None,
    tissue_mask_key=None,
    max_angle_deg=45.0,
    canonical_reference=None,
)
```

Normalize signature:

```python
sq.experimental.im.normalize_stains(
    sdata,
    image_key,
    reference,
    *,
    scale="auto",
    method_params=None,
    image_key_added=None,
    inplace=True,
    output_dtype=None,
    tissue_mask_key=None,
    preserve_background=True,
)
```

Decompose signature:

```python
sq.experimental.im.decompose_stains(
    sdata,
    image_key,
    reference_or_method,
    *,
    scale="auto",
    method_params=None,
    white_point=None,
    image_key_added=None,
    inplace=True,
    output_dtype=np.float16,
    tissue_mask_key=None,
    include_residual=True,
)
```

White-point signature:

```python
sq.experimental.im.estimate_white_point(
    sdata,
    image_key,
    *,
    tissue_mask_key=None,
    scale="auto",
)
```

Behavior and outputs:

- `fit_stain_reference` reads a coarse scale by default and returns a `StainReference`; it does not write to `sdata`.
- A tissue mask is required for stain fitting and white-point estimation. If the default `f"{image_key}_tissue"` does not exist, run `detect_tissue` or pass `tissue_mask_key`.
- `normalize_stains(..., inplace=True)` writes `sdata.images[image_key_added or f"{image_key}_normalized"]` and returns `None`.
- `normalize_stains(..., inplace=False)` returns a lazy `xarray.DataArray`.
- `preserve_background=True` composites non-tissue pixels from the source image back into the normalized result.
- `decompose_stains(..., inplace=True)` validates all target keys before writing per-stain images such as `<prefix>_hematoxylin`, `<prefix>_eosin`, and optionally `<prefix>_residual`.
- `decompose_stains(..., inplace=False)` returns a dict of stain-name to DataArray.

## Tiling QC

Signature:

```python
sq.experimental.tl.calculate_tiling_qc(
    sdata,
    labels_key,
    scale=None,
    tile_size=2048,
    overlap_margin="auto",
    downsample=1,
    outlier_use_cut=True,
    outlier_use_smoothed=True,
    nmads_cut=1.5,
    nmads_smoothed=3,
    n_neighbors=10,
    tiling_qc_params=None,
    n_jobs=-1,
    table_key_added=None,
    inplace=True,
)
```

`TilingQCParams` signature:

```python
sq.experimental.tl.TilingQCParams(
    distance_tol=0.75,
    min_area=20,
    max_contour_points=500,
)
```

Validation:

- `distance_tol >= 0`.
- `min_area >= 1`.
- `max_contour_points >= 3`.

Behavior and outputs:

- Reads `sdata.labels[labels_key]` and scores cell boundaries for straight, axis-aligned tile cuts.
- Default output table key is `f"{labels_key}_qc"`.
- Scores are stored in `.obs`; `.X` is empty.
- `.uns['tiling_qc']` stores algorithm parameters and provenance.
- Important `.obs` score columns include `max_straight_edge_ratio`, `cardinal_alignment_score`, `cut_score`, `smoothed_cut_score`, `is_outlier`, and `nhood_outlier_fraction`.
- `n_jobs=-1` uses available cores; set `n_jobs=1` while validating masks/scales.

## Stitch Group Assignment

Signature:

```python
sq.experimental.tl.assign_stitch_groups(
    sdata,
    labels_key,
    qc_table_key=None,
    min_confidence=0.7,
    max_gap=3.0,
    max_group_size=4,
    stitch_params=None,
    inplace=True,
)
```

`StitchParams` signature:

```python
sq.experimental.tl.StitchParams(
    distance_tol=0.75,
    min_edge_length=5.0,
    min_edge_length_ratio=0.4,
    min_edge_coverage=0.5,
    candidate_min_iou=0.2,
    close_radius=3,
)
```

Validation:

- `distance_tol`, `min_edge_length`, and `close_radius` must be non-negative.
- `min_edge_length_ratio`, `min_edge_coverage`, and `candidate_min_iou` must be in `[0, 1]`.

Behavior and outputs:

- Reads `is_outlier=True` cells from the tiling QC table.
- Scores candidate pairs using geometric features: `iou`, `endpoint_match`, `merge_compactness`, `merge_solidity`, and `gap_proximity`.
- Writes stitch annotations such as `stitch_group_id`, `is_stitched`, `n_pieces`, and `stitch_confidence` to the QC table when `inplace=True`.
- Does not modify `sdata.labels[labels_key]`; labels remain unchanged unless a separate materialization step exists in the caller's code.

Plot signature:

```python
sq.experimental.pl.tiling_qc(
    sdata,
    labels_key,
    qc_key=None,
    score_col="nhood_outlier_fraction",
    cmap="RdYlGn_r",
    figsize=None,
)
```

Valid `score_col` values include `nhood_outlier_fraction`, `smoothed_cut_score`, `cut_score`, `max_straight_edge_ratio`, `cardinal_alignment_score`, and `is_outlier`.
