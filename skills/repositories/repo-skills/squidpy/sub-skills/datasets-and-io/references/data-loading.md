# Data Loading Workflows

This reference helps choose the correct Squidpy loading path before graph, imaging, tool, or plotting work. It is self-contained and assumes only an installed Squidpy environment plus user-provided data or an explicit cache directory.

## Choose the Loader

| Source | Use | Download behavior | Main validation |
| --- | --- | --- | --- |
| Named bundled AnnData, image, or SpatialData example | `sq.datasets.<loader>(path_or_folder)` | May download if missing from cache | Confirm expected object type and downstream keys. |
| Named 10x public Visium sample | `sq.datasets.visium(sample_id, base_dir=cache_dir)` | May download matrix, spatial archive, and optional source image | Confirm `.obsm['spatial']` and `uns['spatial'][sample_id]`. |
| Local Space Ranger Visium folder | `sq.read.visium(path, library_id=...)` | No registry download | Confirm count file, `spatial/` files, coordinates, images, and scalefactors. |
| Local Vizgen/MERSCOPE output | `sq.read.vizgen(path, counts_file=..., meta_file=...)` | No registry download | Confirm `center_x`/`center_y` and optional transform file. |
| Local Nanostring/CosMx output | `sq.read.nanostring(path, counts_file=..., meta_file=...)` | No registry download | Confirm local/global coordinate columns and optional FOV images. |
| Saved object from another pipeline | `anndata.read_h5ad(path)` then validate | No registry download | Confirm numeric `.obsm['spatial']`; require `uns['spatial']` only when plotting/images need it. |
| `SpatialData` `.zarr` or object | `spatialdata.read_zarr(path)` or Squidpy SpatialData dataset loader | No registry download unless using `sq.datasets.*` | Confirm `sdata.tables` and selected `table_key`. |

## Registry Dataset Behavior

Squidpy dataset helpers use a fixed registry of dataset names and four data types:

- `anndata`: downloads/reuses one `.h5ad` file and returns `AnnData`.
- `image`: downloads/reuses one `.tiff` file and returns `sq.im.ImageContainer` with layer `image`.
- `spatialdata`: downloads/reuses one `.zip`, extracts a `.zarr`, and returns `spatialdata.SpatialData`.
- `visium_10x`: downloads/reuses `filtered_feature_bc_matrix.h5`, `spatial.tar.gz`, and optionally a high-resolution `image.tif`/`image.jpg`, then reads the folder as Visium.

Important choices:

- Unknown dataset names raise `ValueError` with available names; custom user data should use local readers instead of trying to extend `sq.datasets` at runtime.
- Existing files are reused before download. Corrupt cached files can still raise hash or read errors.
- If no path is supplied, Squidpy falls back to Scanpy's global dataset directory. For reproducibility, pass a path explicitly.
- `sq.datasets.visium(sample_id, base_dir=cache_dir)` stores files below `cache_dir / sample_id`.
- `include_hires_tiff=True` asks for the optional source tissue image and records `metadata['source_image_path']` when the file is available; `False` avoids that optional request but does not remove a previously cached image file.

Offline-friendly examples:

```python
from pathlib import Path
import squidpy as sq

cache_dir = Path("squidpy-cache")
adata = sq.datasets.visium("V1_Mouse_Kidney", base_dir=cache_dir)
# Later offline runs can reuse squidpy-cache/V1_Mouse_Kidney/ if all files are present.
```

```python
import squidpy as sq

adata = sq.datasets.imc("squidpy-cache/imc.h5ad")
img = sq.datasets.visium_hne_image_crop("squidpy-cache/visium_hne_image_crop.tiff")
sdata = sq.datasets.cells("squidpy-cache/spatialdata")
```

## Local Visium Workflow

`sq.read.visium(path, ...)` expects `path` to be the Space Ranger output root, not the `spatial/` subdirectory.

Typical layout with images enabled:

```text
sample/
  filtered_feature_bc_matrix.h5
  spatial/
    tissue_hires_image.png
    tissue_lowres_image.png
    scalefactors_json.json
    tissue_positions.csv
    # or tissue_positions_list.csv
```

Recommended full read:

```python
import squidpy as sq

adata = sq.read.visium("sample", library_id="sample_a")
```

Reader behavior to remember:

- `.h5` counts are read with `scanpy.read_10x_h5`; if the HDF5 attributes do not expose a `library_id`, pass one explicitly.
- `.mtx.gz` counts use `scanpy.read_10x_mtx`; text/CSV counts require an explicit `library_id`.
- With `load_images=True`, Squidpy reads hires/lowres PNGs, scalefactors JSON, and tissue positions, then fills `.obsm['spatial']` from full-resolution pixel row/column coordinates.
- With `load_images=False`, Squidpy returns counts and initializes `uns['spatial'][library_id]['metadata']` only; coordinates, images, and scalefactors are not populated.
- `source_image_path` is optional metadata for the full-resolution tissue image. Squidpy records it and warns if the path does not exist.

Count-only fallback:

```python
adata = sq.read.visium("sample", library_id="sample_a", load_images=False)
# Do not route to image-backed plotting until coordinates and uns['spatial'] are repaired.
```

## Local Vizgen Workflow

```python
import squidpy as sq

adata = sq.read.vizgen(
    "vizgen-output",
    counts_file="cell_by_gene.csv",
    meta_file="cell_metadata.csv",
    transformation_file="micron_to_mosaic_pixel_transform.csv",
    library_id="library",
)
```

Expected conventions:

- Counts are comma-delimited with first-column cell names.
- Metadata index is cast to string and merged by cell id.
- Metadata must contain `center_x` and `center_y`; they become `.obsm['spatial']`.
- Genes containing `Blank` are moved to `.obsm['blank_genes']` and removed from `.var_names`.
- `transformation_file`, when provided, is read from `images/` and stored under `uns['spatial'][library_id]['scalefactors']['transformation_matrix']`.

## Local Nanostring/CosMx Workflow

```python
import squidpy as sq

adata = sq.read.nanostring(
    "nanostring-output",
    counts_file="sample_exprMat_file.csv",
    meta_file="sample_metadata_file.csv",
    fov_file="sample_fov_positions_file.csv",
)
```

Expected conventions:

- Counts have `cell_ID` as index plus a `fov` column; observations become `<cell_ID>_<fov>`.
- Metadata includes `cell_ID`, `fov`, `CenterX_local_px`, `CenterY_local_px`, `CenterX_global_px`, and `CenterY_global_px`.
- `.obsm['spatial']` stores local coordinates; `.obsm['spatial_fov']` stores global coordinates.
- Each FOV in `obs['fov']` gets `uns['spatial'][fov]` with empty image metadata and unit scalefactors.
- Optional `CellComposite/` images populate `images['hires']`; optional `CellLabels/` images populate `images['segmentation']` when filenames expose `_F<number>`.
- Optional `fov_file` rows are copied into each matching FOV's metadata.

## AnnData Spatial Preconditions

Most downstream Squidpy workflows expect:

```python
adata.obsm["spatial"]              # numeric n_obs x 2-or-more coordinate matrix
adata.uns["spatial"]              # mapping from library id to spatial metadata
adata.uns["spatial"][library_id]
```

A Visium-style library entry often contains:

```python
{
    "images": {"hires": image_array, "lowres": image_array},
    "scalefactors": {
        "tissue_hires_scalef": float,
        "tissue_lowres_scalef": float,
        "spot_diameter_fullres": float,
    },
    "metadata": {...},
}
```

Graph/statistical workflows usually need only a valid numeric `.obsm['spatial']`. Image-backed plotting and image workflows need matching `uns['spatial']` entries, image arrays, scalefactors, and a valid `library_id`.

## SpatialData Routing Preconditions

For a `SpatialData` object:

1. Inspect `list(sdata.tables)`.
2. Select one table for stable graph/tool workflows with `table_key=<table name>`.
3. Validate that selected table as AnnData-like when the workflow needs `.obsm['spatial']` or `.obs` categories.
4. Route image, labels, shapes, tiling, QC, or stain operations to `experimental-imaging` rather than treating them as AnnData loading problems.

## Bundled Validator

Use the bundled script for local structural checks:

```bash
python scripts/check_spatial_adata.py sample.h5ad
python scripts/check_spatial_adata.py sample.h5ad --library-id sample_a --require-images --require-scalefactors
python scripts/check_spatial_adata.py sample.h5ad --json
python scripts/check_spatial_adata.py --callable mypkg.data:load_object --table-key table
```

The script does not download data, read external fixtures, or run graph/image computations. It reports whether the object is structurally ready for downstream routing.
