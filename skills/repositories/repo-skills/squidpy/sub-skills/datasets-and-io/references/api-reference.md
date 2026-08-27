# Datasets and IO API Reference

Import convention:

```python
import squidpy as sq
```

## Public Dataset Loaders

All registry-backed dataset loaders may read from or write to a cache path. If the target file/folder is missing, they can perform network downloads.

### AnnData Datasets

Signature pattern:

```python
sq.datasets.<name>(path=None, **kwargs)
```

Available AnnData loaders:

- `sq.datasets.four_i`
- `sq.datasets.imc`
- `sq.datasets.seqfish`
- `sq.datasets.visium_hne_adata`
- `sq.datasets.visium_hne_adata_crop`
- `sq.datasets.visium_fluo_adata`
- `sq.datasets.visium_fluo_adata_crop`
- `sq.datasets.sc_mouse_cortex`
- `sq.datasets.mibitof`
- `sq.datasets.merfish`
- `sq.datasets.slideseqv2`

Behavior:

- `path` is the local `.h5ad` target to save/reuse.
- Extra keyword arguments are passed to `anndata.read_h5ad`.
- Registry shape mismatches are warnings, not a replacement for downstream validation.

### Image Datasets

Signature pattern:

```python
sq.datasets.<name>(path=None, **kwargs)
```

Available image loaders:

- `sq.datasets.visium_fluo_image_crop`
- `sq.datasets.visium_hne_image_crop`
- `sq.datasets.visium_hne_image`

Behavior:

- `path` is the local `.tiff` target to save/reuse.
- The return value is `sq.im.ImageContainer` with layer `image`.
- Registry `library_id` metadata is used when available.
- Route actual `ImageContainer` processing to `image-analysis`.

### Visium 10x Registry Loader

```python
sq.datasets.visium(sample_id, *, include_hires_tiff=False, base_dir=None)
```

Behavior:

- `sample_id` must be one of Squidpy's fixed 10x registry names.
- `base_dir=None` uses Scanpy's global dataset directory; pass `base_dir` for reproducible cache behavior.
- Files live under `base_dir / sample_id`.
- The loader downloads/reuses `filtered_feature_bc_matrix.h5` and `spatial.tar.gz`, extracts missing spatial files, and reads the result with `sq.read.visium`.
- `include_hires_tiff=True` tries to fetch an optional `image.tif` or `image.jpg` and records its path in `uns['spatial'][sample_id]['metadata']['source_image_path']` when available.

Useful pattern:

```python
adata = sq.datasets.visium(
    "V1_Mouse_Kidney",
    include_hires_tiff=False,
    base_dir="squidpy-cache",
)
```

### SpatialData Registry Loaders

```python
sq.datasets.visium_hne_sdata(folderpath=None)
sq.datasets.cells(folderpath=None)
```

Behavior:

- `folderpath=None` uses Scanpy's global dataset directory.
- Squidpy downloads/reuses a `.zip`, extracts a `.zarr`, and returns `spatialdata.SpatialData`.
- Before graph/tool routing, inspect `sdata.tables` and choose a `table_key`.
- Route SpatialData image/label/shape workflows to `experimental-imaging`.

## Local Readers

Local readers do not use the dataset registry. They require exact local file layouts and platform-specific columns.

### `sq.read.visium`

```python
sq.read.visium(
    path,
    *,
    counts_file="filtered_feature_bc_matrix.h5",
    library_id=None,
    load_images=True,
    source_image_path=None,
    **kwargs,
)
```

Inputs:

- `path`: Space Ranger output root.
- `counts_file`: usually `filtered_feature_bc_matrix.h5`, `raw_feature_bc_matrix.h5`, a matrix-market `.mtx.gz` indicator, or a text/CSV count file.
- `library_id`: required for text/CSV and matrix-market inputs; inferred from `.h5` attributes only when present.
- `load_images`: whether to require and load `spatial/` images, scalefactors, and positions.
- `source_image_path`: optional metadata for a full-resolution source image.

Outputs with `load_images=True`:

- `.obsm['spatial']` from full-resolution pixel coordinates.
- `uns['spatial'][library_id]['images']['hires']` and `['lowres']`.
- `uns['spatial'][library_id]['scalefactors']` from `scalefactors_json.json`.
- position columns such as `in_tissue`, `array_row`, and `array_col` in `.obs`.

Caveat:

- `load_images=False` returns counts and `uns['spatial'][library_id]['metadata']` only. It is not spatial-ready for graph or image-backed plotting until coordinates and metadata are repaired.

### `sq.read.vizgen`

```python
sq.read.vizgen(
    path,
    *,
    counts_file,
    meta_file,
    transformation_file=None,
    library_id="library",
    **kwargs,
)
```

Inputs and outputs:

- Counts are read from `path / counts_file`, comma-delimited with first-column cell identifiers.
- Metadata is read from `path / meta_file` and must include `center_x` and `center_y`.
- `.obsm['spatial']` is filled from `center_x`, `center_y`.
- Genes containing `Blank` move to `.obsm['blank_genes']` and are removed from variables.
- `transformation_file`, when provided, is read from `path / "images" / transformation_file` and stored as `uns['spatial'][library_id]['scalefactors']['transformation_matrix']`.

### `sq.read.nanostring`

```python
sq.read.nanostring(
    path,
    *,
    counts_file,
    meta_file,
    fov_file=None,
)
```

Inputs and outputs:

- Counts require `cell_ID` as index plus a `fov` column.
- Metadata requires `cell_ID`, `fov`, `CenterX_local_px`, `CenterY_local_px`, `CenterX_global_px`, and `CenterY_global_px`.
- Observation names become `<cell_ID>_<fov>` after intersecting counts and metadata.
- `.obsm['spatial']` stores local cell centers.
- `.obsm['spatial_fov']` stores global FOV coordinates.
- Each FOV category creates `uns['spatial'][fov]` with `images` and unit `scalefactors`.
- Optional `CellComposite/` and `CellLabels/` folders populate `hires` and `segmentation` image entries.
- Optional `fov_file` rows add FOV metadata.

## Validation Script Interface

```bash
python scripts/check_spatial_adata.py H5AD [options]
python scripts/check_spatial_adata.py --callable MODULE:FUNCTION [options]
```

Common options:

- `--library-id ID`: require one `uns['spatial']` library entry.
- `--require-uns-spatial`: treat missing `uns['spatial']` as an error instead of a warning.
- `--require-images`: require image metadata under selected library entries.
- `--require-scalefactors`: require scalefactors under selected library entries.
- `--library-key OBS_COL`: validate a library id column in `.obs`.
- `--require-categorical-library`: require `--library-key` to be categorical.
- `--table-key TABLE`: when the loaded object has `.tables`, validate one `SpatialData` table.
- `--json`: emit machine-readable output.

Use stricter options only when the next workflow needs those structures. For example, graph routing normally needs numeric `.obsm['spatial']`, while image-backed plotting needs a matching `library_id`, images, and scalefactors.
