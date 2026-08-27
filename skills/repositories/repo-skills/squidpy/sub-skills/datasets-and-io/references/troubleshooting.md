# Datasets and IO Troubleshooting

Use this reference when Squidpy loading fails, when a loaded object is incomplete, or when the next sub-skill cannot find expected spatial keys.

## Unknown Dataset or Registry Entry

Symptoms:

- `ValueError: Unknown dataset`
- `ValueError: Unknown Visium sample`
- An old notebook calls a dataset helper that no longer exists.

Fixes:

1. Use only fixed public helpers listed in `references/api-reference.md`.
2. For 10x public samples, call `sq.datasets.visium(sample_id, base_dir=...)`; do not call `sq.datasets.<sample_id>()`.
3. For custom local files, use `anndata.read_h5ad`, `sq.read.visium`, `sq.read.vizgen`, `sq.read.nanostring`, or `spatialdata.read_zarr` instead of the registry.
4. If an example is not in the registry, ask the user for the local file layout or a cache directory rather than silently starting a download search.

## Download, Cache, Network, or Hash Failure

Symptoms:

- Download timeout, remote disconnect, or `ExceptionGroup` from all registry URLs.
- Hash mismatch from the downloader.
- A dataset works online but fails in a restricted environment.
- A stale cached file is reused and then fails to read.

Fixes:

1. Treat `sq.datasets.*` as network-capable unless all expected files already exist locally.
2. Pass explicit paths: `sq.datasets.visium(sample_id, base_dir=cache_dir)` or `sq.datasets.imc(cache_dir / "imc.h5ad")`.
3. For Visium registry samples, verify `base_dir / sample_id / filtered_feature_bc_matrix.h5` and extracted `spatial/` files exist before an offline run.
4. If a hash mismatch occurs, remove only the suspect cached file and retry in a network-enabled environment.
5. Set `include_hires_tiff=False` unless the next workflow actually needs the optional source tissue image.
6. Do not build public runtime workflows around CI download/pre-cache scripts; they are networked and layout-specific.

## Missing Visium `spatial/` Files

Symptoms:

- `FileNotFoundError` for `spatial/scalefactors_json.json`, `tissue_hires_image.png`, `tissue_lowres_image.png`, `tissue_positions.csv`, or `tissue_positions_list.csv`.
- Counts load but `.obsm['spatial']` is absent.
- Plotting cannot find image metadata after a Visium read.

Expected full layout:

```text
sample/
  filtered_feature_bc_matrix.h5
  spatial/
    tissue_hires_image.png
    tissue_lowres_image.png
    scalefactors_json.json
    tissue_positions.csv or tissue_positions_list.csv
```

Fixes:

- Pass the Space Ranger output root as `path`, not `path/spatial`.
- Restore or rename position files to one of Squidpy's expected names.
- Restore `scalefactors_json.json` for image overlays and spot-size scaling.
- Restore hires/lowres PNGs or route plotting with no image after confirming the plotting sub-skill supports the requested view.
- Use `sq.read.visium(..., load_images=False)` only to recover counts and initial metadata when spatial files are unavailable; it does not populate `.obsm['spatial']`.

## Wrong or Missing `library_id`

Symptoms:

- `KeyError: Unable to extract library id from attributes. Please specify one explicitly.`
- Plotting asks for a valid `library_id`.
- `adata.uns['spatial']` has a key different from the user's expected sample id.
- Concatenated samples overwrite image/scalefactor metadata.

Fixes:

1. Pass `library_id="sample_a"` when reading local Visium unless you have verified the HDF5 attributes contain the intended id.
2. Always pass `library_id` for text/CSV and matrix-market counts.
3. After loading, inspect `list(adata.uns['spatial'])` and use one of those exact keys downstream.
4. When concatenating samples, preserve a categorical library column in `.obs` and separate `uns['spatial'][library_id]` entries.
5. Do not assume a registry `sample_id` and a local `library_id` are interchangeable unless you set them that way.

## Missing or Invalid `.obsm['spatial']`

Symptoms:

- Graph construction, spatial statistics, or plotting says spatial coordinates are missing.
- The bundled validator reports missing, non-2D, row-mismatched, or non-numeric coordinates.
- A generic `.h5ad` has coordinate-like columns in `.obs` but no `.obsm['spatial']`.

Fixes:

- Ensure `.obsm['spatial']` is numeric with one row per observation and at least two columns.
- For Visium, verify tissue position barcodes/index values match `.obs_names`.
- For Vizgen, verify `meta_file` has `center_x` and `center_y` for the same cells as the count file.
- For Nanostring/CosMx, verify local center columns `CenterX_local_px` and `CenterY_local_px` exist.
- For a generic `.h5ad`, construct `.obsm['spatial']` from trusted coordinate columns before routing to graph, tools, or plotting.

Minimal repair pattern for generic coordinates:

```python
adata.obsm["spatial"] = adata.obs[["x", "y"]].to_numpy(dtype=float)
```

## Missing or Incomplete `uns['spatial']`

Symptoms:

- Image-backed plotting cannot find images or scalefactors.
- The validator warns or errors on missing `uns['spatial']`.
- `uns['spatial']` exists but contains no matching library entry.

Fixes:

- For graph/statistics only, decide whether `.obsm['spatial']` is sufficient and route to `graph-analysis` without inventing image metadata.
- For Visium plotting with images, prefer a complete `sq.read.visium(..., load_images=True)` from a repaired Space Ranger folder.
- Use `scripts/check_spatial_adata.py --require-uns-spatial --library-id <id>` when downstream code requires a specific library.
- Use `--require-images --require-scalefactors` only when the requested workflow needs image overlays or spot scaling.
- Do not create fake image arrays merely to satisfy plotting; either restore the images/scalefactors or route to no-image plotting.

## Image or Scalefactor Loading Failure

Symptoms:

- PIL/image errors while opening Visium tissue images or Nanostring FOV images.
- Missing `images['hires']`, `images['lowres']`, or `images['segmentation']`.
- Vizgen transform file not found.

Fixes:

- Visium images must be exactly `spatial/tissue_hires_image.png` and `spatial/tissue_lowres_image.png` for `load_images=True`.
- Vizgen `transformation_file` is resolved below `images/`, not at the root.
- Nanostring image discovery scans `CellComposite/` for hires images and `CellLabels/` for segmentation images; filenames must expose an `_F<number>` FOV pattern.
- Route processing of loaded image arrays to `image-analysis` or `experimental-imaging`; this sub-skill only validates loading preconditions.

## SpatialData `table_key` Ambiguity

Symptoms:

- A graph/tool call on `SpatialData` asks for `table_key`.
- The validator reports that the object has `.tables` and needs `--table-key`.
- A requested table key is absent from `sdata.tables`.

Fixes:

1. Inspect `list(sdata.tables)` before calling stable graph/tool APIs.
2. Pass `table_key=<existing table>` to graph/tool functions that accept `AnnData | SpatialData`.
3. Use `scripts/check_spatial_adata.py --callable module:load_sdata --table-key <table>` to validate the selected table's AnnData-like structure.
4. If the task concerns images, labels, shapes, tiling, QC, or stain normalization, route to `experimental-imaging` instead of forcing table validation.

## Safe Diagnostic Sequence

1. Identify the source: registry dataset, local Visium, Vizgen, Nanostring/CosMx, generic `.h5ad`, or `SpatialData`.
2. Decide no-download vs download/cache explicitly.
3. Load with the narrowest API that matches the source.
4. Validate `.obsm['spatial']`, `uns['spatial']`, library ids, images, scalefactors, or `table_key` as needed.
5. Route onward only when preconditions match the next workflow: graph/statistics to `graph-analysis`, stable image work to `image-analysis`, plotting to `visualization`, and experimental SpatialData imaging to `experimental-imaging`.
