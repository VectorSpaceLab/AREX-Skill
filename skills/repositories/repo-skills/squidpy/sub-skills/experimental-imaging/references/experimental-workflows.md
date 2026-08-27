# Experimental SpatialData Image Workflows

This reference covers `squidpy.experimental.im`, `squidpy.experimental.tl`, and `squidpy.experimental.pl` workflows that operate on `SpatialData`. These APIs are experimental, so write tasks defensively: use explicit keys, avoid overwrites, keep previews disabled in headless runs, and verify where each result was stored.

## SpatialData Contracts

Most experimental imaging functions read and write named elements in a `SpatialData` object.

| Element | Required shape or role | Used by |
| --- | --- | --- |
| `sdata.images[image_key]` | RGB or multichannel image element, often multiscale with levels such as `scale0` | tissue detection, tiling, QC, stains, feature extraction |
| `sdata.labels[labels_key]` | integer label mask aligned to the image coordinate system | per-cell features, tiling QC, stitching |
| `sdata.labels[tissue_mask_key]` | integer or binary tissue mask, usually from `detect_tissue` | tiling, image QC, stain fitting/normalization |
| `sdata.shapes[shapes_key]` | polygons or point-like geometries; tile grids are written here | `make_tiles`, `make_tiles_from_spots`, feature/table linkage |
| `sdata.tables[table_key]` | AnnData table linked to a region via `uns['spatialdata_attrs']` | image QC, per-cell features, tiling QC, stitch groups |

Practical checks before calling experimental imaging APIs:

- Print `list(sdata.images)`, `list(sdata.labels)`, `list(sdata.shapes)`, and `list(sdata.tables)` and choose explicit keys.
- Prefer `scale="auto"` for tissue detection, tiling, and stain fitting when the image is multiscale; prefer explicit `scale="scale0"` or another known level when reproducing a prior analysis.
- Confirm image and mask transformations match. If a labels or shapes element came from another tool, inspect coordinate systems before assuming pixel coordinates align.
- Use new output keys and check that they do not already exist; several APIs raise on existing image keys but in-place table/shape workflows can replace expected names.

## Tissue Detection To Tiles

Use this route when the user needs a tissue mask and tile grid over a SpatialData image.

```python
import squidpy as sq

sq.experimental.im.detect_tissue(
    sdata,
    image_key="image",
    scale="auto",
    method="otsu",
    channel_format="infer",
    new_labels_key="image_tissue",
    inplace=True,
)

sq.experimental.im.make_tiles(
    sdata,
    image_key="image",
    tissue_mask_key="image_tissue",
    tile_size=(224, 224),
    center_grid_on_tissue=False,
    min_tissue_fraction=0.5,
    new_shapes_key="image_tiles",
    preview=False,
)
```

Expected outputs:

- `detect_tissue(..., inplace=True)` writes an integer mask to `sdata.labels[new_labels_key]` and returns `None`.
- `detect_tissue(..., inplace=False)` returns a NumPy mask and leaves `sdata` untouched.
- `make_tiles` writes polygons to `sdata.shapes[new_shapes_key]` with columns such as `pixel_y0`, `pixel_x0`, `pixel_y1`, `pixel_x1`, and `tile_classification`.
- Tile classes are `background`, `partial_tissue`, and `tissue`; use `min_tissue_fraction` to decide how strict inference-tile selection should be.

Method guidance:

- `method="otsu"` is the lowest-dependency default and is appropriate for many bright-background tissue slides.
- `method="felzenszwalb"` accepts `FelzenszwalbParams` or a mapping for superpixel tuning.
- `method="weka"` uses trainable segmentation-style features and `WekaParams`; verify dependency availability and runtime before choosing it for automation.
- Use `border_margin_px` to suppress slide edges, fiducials, or frame artifacts; pass four values `(top, bottom, left, right)` for asymmetric borders.

## Spot-Centered Tiles

Use `make_tiles_from_spots` for Visium-style point-like spot shapes. It reads spot centers from `sdata.shapes[spots_key]`, derives a square tile size from vertical spot spacing, classifies each tile by tissue coverage, writes tile polygons to `sdata.shapes[new_shapes_key]`, and propagates `tile_classification` back to the spot shapes when possible.

```python
sq.experimental.im.make_tiles_from_spots(
    sdata,
    spots_key="spots",
    image_key="image",
    tissue_mask_key="image_tissue",
    scale="auto",
    min_tissue_fraction=0.5,
    new_shapes_key="spot_tiles",
    preview=False,
)
```

Before using this route, confirm the spot shapes are point-like and in the same coordinate system as the image and tissue mask. If spacing inference is unstable, use regular `make_tiles` with an explicit `tile_size` instead.

## Image QC And QC Plots

Use `qc_image` for tile-level image quality metrics. It creates both an AnnData table of scores and a tile-grid shape element.

```python
from squidpy.experimental.im import QCMetric

sq.experimental.im.qc_image(
    sdata,
    image_key="image",
    scale="scale0",
    metrics=[QCMetric.TENENGRAD, QCMetric.VAR_OF_LAPLACIAN, QCMetric.BRIGHTNESS_MEAN],
    tile_size=(512, 512),
    is_hne=False,
    detect_outliers=True,
    detect_tissue=True,
    tissue_mask_key="image_tissue",
    outlier_threshold=0.1,
    progress=False,
    preview=False,
)
```

Expected outputs:

- `sdata.tables[f"qc_img_{image_key}"]` stores an AnnData table with `X` columns named in `.var_names` as `qc_<metric>` and observations corresponding to tiles.
- Tile centroids are stored in `.obs['centroid_y']`, `.obs['centroid_x']`, and `.obsm['spatial']`.
- When outlier detection is enabled, `.obs` can include `qc_outlier`, `is_tissue`, `is_background`, and `unfocus_score`.
- `sdata.shapes[f"qc_img_{image_key}_grid"]` stores tile polygons linked to the QC table.
- Metadata is recorded in `.uns['qc_image']`.

For H&E slides, default metrics include sharpness, brightness, hematoxylin, and eosin summaries. For non-H&E images, set `is_hne=False`; H&E-only metrics such as hematoxylin/eosin/fold scores are rejected in that mode.

Plot after computation with:

```python
sq.experimental.pl.qc_image(sdata, image_key="image", return_ax=False)
```

Use this plotter only for QC summaries produced by experimental `qc_image`; route general Squidpy plotting tasks to `visualization`.

## Per-Cell Image Features

Use experimental `calculate_image_features` when features must be extracted from `SpatialData` image/label/table contracts rather than stable `ImageContainer` spot crops.

```python
sq.experimental.im.calculate_image_features(
    sdata,
    image_key="image",
    labels_key="cells",
    shapes_key=None,
    scale="scale0",
    channels=["r", "g", "b"],
    features=["skimage:morphology", "squidpy:summary"],
    tile_size=2048,
    overlap_margin="auto",
    adata_key_added="morphology",
    invalid_as_zero=True,
    n_jobs=1,
    inplace=True,
)
```

Important behavior:

- `features` must be explicit; `None` raises a validation error.
- Supported groups include `skimage:morphology`, `skimage:intensity`, `squidpy:summary`, `squidpy:texture`, and `squidpy:color_hist`; fine-grained skimage properties can be requested with `skimage:morphology:<prop>` or `skimage:intensity:<prop>`.
- `cpmeasure:*` feature names are recognized but not implemented and raise `NotImplementedError`.
- Large images are tiled so that cells are fully contained in exactly one tile; tune `tile_size` and `overlap_margin` for large cells near boundaries.
- With `inplace=True`, results are written to a SpatialData-linked AnnData table; with `inplace=False`, an AnnData object is returned.

## Stain Normalization And Decomposition

Use the stain APIs for RGB H&E images and always establish a tissue mask first.

```python
sq.experimental.im.detect_tissue(
    sdata,
    image_key="he",
    scale="auto",
    new_labels_key="he_tissue",
    inplace=True,
)
reference = sq.experimental.im.fit_stain_reference(
    sdata,
    image_key="he",
    method="macenko",
    tissue_mask_key="he_tissue",
    method_params=sq.experimental.im.MacenkoParams(alpha=1.0, beta=0.15),
)
sq.experimental.im.normalize_stains(
    sdata,
    image_key="he",
    reference=reference,
    image_key_added="he_normalized",
    tissue_mask_key="he_tissue",
    preserve_background=True,
    inplace=True,
)
```

Method choices:

- `method="macenko"` is the default decomposition-style H&E reference and supports normalization plus decomposition.
- `method="vahadane"` uses sparse NMF and can be more expensive; set `VahadaneParams(random_state=...)` for reproducible fitting.
- `method="reinhard"` is a faster color-transfer method and does not produce a stain matrix for `decompose_stains`.
- `estimate_white_point` samples non-tissue background and should be used only when the slide background is genuinely not full white; keep the sampling scale coarse.

Decomposition writes separate single-channel images by default:

```python
sq.experimental.im.decompose_stains(
    sdata,
    image_key="he",
    reference_or_method=reference,
    image_key_added="he_stain",
    tissue_mask_key="he_tissue",
    include_residual=True,
    output_dtype="float32",
    inplace=True,
)
```

Expected outputs are `sdata.images['he_stain_hematoxylin']`, `sdata.images['he_stain_eosin']`, and optionally `sdata.images['he_stain_residual']`. The residual map is a quality diagnostic, not a biological stain.

## Tiling Artifact QC And Stitch Groups

Use this route after tile-wise segmentation has produced a labels element with possible boundary-cut cells.

```python
qc = sq.experimental.tl.calculate_tiling_qc(
    sdata,
    labels_key="cells",
    scale="scale0",
    tile_size=2048,
    overlap_margin="auto",
    nmads_cut=1.5,
    nmads_smoothed=3.0,
    n_neighbors=10,
    tiling_qc_params={"distance_tol": 0.75, "min_area": 20},
    n_jobs=1,
    table_key_added="cells_qc",
    inplace=False,
)
```

With `inplace=True`, the QC table defaults to `sdata.tables[f"{labels_key}_qc"]`. Scores live in `.obs`; `.X` is empty. Common columns include `max_straight_edge_ratio`, `cardinal_alignment_score`, `cut_score`, `smoothed_cut_score`, `is_outlier`, and `nhood_outlier_fraction`. Parameters are recorded in `.uns['tiling_qc']`.

Then annotate candidate stitch groups:

```python
sq.experimental.tl.assign_stitch_groups(
    sdata,
    labels_key="cells",
    qc_table_key="cells_qc",
    min_confidence=0.7,
    max_gap=3.0,
    max_group_size=4,
    stitch_params={"close_radius": 3},
    inplace=True,
)
```

`assign_stitch_groups` annotates QC-table observations with columns such as `stitch_group_id`, `is_stitched`, `n_pieces`, and `stitch_confidence`; it does not modify the labels element. Plot artifact scores with:

```python
sq.experimental.pl.tiling_qc(
    sdata,
    labels_key="cells",
    qc_key="cells_qc",
    score_col="nhood_outlier_fraction",
)
```

Use `score_col="is_outlier"` for a binary view, or continuous columns for diagnostic heatmaps.

## Automation Checklist

- Disable previews (`preview=False`) unless the task explicitly asks for interactive or notebook plots.
- Use `progress=False` or low verbosity for batch runs.
- Start with small `tile_size` only for tiny images; whole-slide workflows need larger tiles and enough overlap to contain cell boundaries.
- Keep `n_jobs=1` while debugging alignment or dtype issues, then increase after the workflow is validated.
- Inspect output keys and linked table metadata before passing results into plotting or downstream analysis.
