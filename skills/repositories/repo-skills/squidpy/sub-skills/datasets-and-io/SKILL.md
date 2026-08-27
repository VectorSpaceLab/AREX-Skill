---
name: datasets-and-io
description: "Load Squidpy datasets and local spatial inputs with safe cache,
  layout, AnnData, and SpatialData validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Squidpy Datasets and IO

Use this sub-skill when a task starts with Squidpy sample data, local spatial omics outputs, saved `.h5ad` files, or `SpatialData` tables that must be checked before analysis, imaging, or plotting.

## Route Here For

- Choosing between `squidpy.datasets` download/cache helpers and local no-download readers.
- Loading local 10x Visium, Vizgen, or Nanostring/CosMx outputs with `sq.read.*`.
- Validating Squidpy-ready `AnnData` structure: `.obsm['spatial']`, `.uns['spatial']`, `library_id`, image metadata, and scalefactors.
- Checking `SpatialData` table availability and `table_key` before routing to graph or experimental imaging workflows.
- Diagnosing registry, cache, network/hash, `spatial/` layout, non-numeric coordinates, or image/scalefactor problems.

## Start Here

1. Read `references/data-loading.md` to pick a no-download local reader or a registry-backed dataset loader.
2. Check exact public signatures and required file conventions in `references/api-reference.md`.
3. Use `scripts/check_spatial_adata.py --help` to validate a saved `.h5ad` or an importable callable returning `AnnData`/`SpatialData`.
4. Use `references/troubleshooting.md` when loading succeeds but downstream workflows cannot find coordinates, `library_id`, images, scalefactors, or `table_key`.

## Safe Defaults

- Prefer `sq.read.visium`, `sq.read.vizgen`, `sq.read.nanostring`, `anndata.read_h5ad`, or `spatialdata.read_zarr` for user-owned local data; these do not consult Squidpy's dataset registry.
- Treat `sq.datasets.*` calls as potentially networked unless the needed files already exist in the chosen cache directory.
- Pass an explicit cache or input path instead of relying on global Scanpy settings.
- For Visium, use `load_images=False` only as a count/metadata fallback; it does not create `.obsm['spatial']`, images, or scalefactors.

## Boundaries

- Route spatial graph construction and statistics to `graph-analysis` after coordinates and table routing are clear.
- Route stable `ImageContainer`, image processing, segmentation, and image features to `image-analysis`.
- Route plot rendering and visual styling to `visualization`.
- Route experimental `SpatialData` tiling, tissue detection, QC, stitching, and stain workflows to `experimental-imaging`.
