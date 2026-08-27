# Spatial Data Formats and Slot Contracts

Use this reference to validate inputs before running OmicVerse spatial readers, plotting, deconvolution, or histology models.

## AnnData Spatial Contract

A spatial AnnData object should make these slots explicit:

| Slot | Required? | Expected content | Common producer |
| --- | --- | --- | --- |
| `adata.X` | yes | spots/cells × genes expression matrix | spatial readers, Scanpy |
| `adata.var_names` | yes | gene symbols or IDs; must intersect with references for mapping | all readers |
| `adata.obs_names` | yes | spot/cell/barcode IDs | all readers |
| `adata.obsm['spatial']` | yes for spatial workflows | `n_obs × 2` coordinates | Visium, Xenium, NanoString, Atera readers |
| `adata.uns['spatial']` | required for image-backed plotting | mapping from library/FOV/sample id to images/scalefactors/metadata | spatial readers |
| `adata.uns['spatial'][library]['images']['hires']` | optional but needed for image overlay | image array | Visium, Xenium, NanoString |
| `adata.uns['spatial'][library]['images']['lowres']` | optional | low-resolution image array | Visium/Visium HD |
| `adata.uns['spatial'][library]['images']['segmentation']` | optional | label image for cell segmentation | NanoString/CosMx |
| `adata.uns['spatial'][library]['scalefactors']['tissue_hires_scalef']` | image overlay | coordinate-to-image scale | spatial readers |
| `adata.uns['spatial'][library]['scalefactors']['spot_diameter_fullres']` | plotting | spot/cell marker diameter in full-res pixels | spatial readers |
| `adata.obs['geometry']` | segmentation plotting | WKT polygon or multipolygon strings | Xenium boundaries, Visium HD cellseg, NanoString contours |
| `adata.layers['counts']` | strongly recommended | raw counts used by deconvolution/split workflows | user or readers |
| `adata.obsp['spatial_connectivities']` | optional/generated | spatial graph connectivity matrix | `ov.space.spatial_neighbors` |
| `adata.obsp['spatial_distances']` | optional/generated | spatial graph distance matrix | `ov.space.spatial_neighbors` |

Coordinate units vary by platform:

- Visium/Visium HD bin: usually full-resolution pixel coordinates from tissue positions.
- Xenium: cell centroids in microns; image scalefactor maps microns to morphology pixels.
- NanoString/CosMx: local FOV pixel coordinates in `obsm['spatial']`; optional global coordinates in `obsm['spatial_fov']`.
- Manual/synthetic AnnData: unit is whatever the user stored; always document whether coordinates are pixels, microns, array rows/columns, or normalized embedding coordinates.

## Visium HD Layouts

### Bin-level Space Ranger output

Typical root passed to `read_visium_hd(..., data_type='bin')` or `read_visium_hd_bin`:

```text
outs/
  binned_outputs/
    square_016um/
      filtered_feature_bc_matrix.h5
      filtered_feature_bc_matrix/
      spatial/
        tissue_positions.parquet
        tissue_hires_image.png
        tissue_lowres_image.png
        scalefactors_json.json
```

You may pass either `outs/binned_outputs/square_016um` directly or pass a root and override relative paths. The reader falls back from H5 to MTX when both paths are configured and H5 fails.

Required files for bin-level loading:

- Count matrix: `filtered_feature_bc_matrix.h5` or `filtered_feature_bc_matrix/`.
- Tissue positions: `spatial/tissue_positions.parquet` or CSV fallback.
- Coordinate columns: one of `pxl_col_in_fullres`/`pxl_row_in_fullres`, `pxl_col`/`pxl_row`, `x`/`y`, or `array_col`/`array_row`.

Optional but important files:

- `spatial/tissue_hires_image.png`
- `spatial/tissue_lowres_image.png`
- `spatial/scalefactors_json.json`

Expected output:

- `obsm['spatial']` from tissue position columns.
- `uns['spatial'][sample]['images']` when images are present.
- `uns['spatial'][sample]['scalefactors']` from scale factors JSON.
- `uns['spatial'][sample]['binsize']` from the `binsize` argument.

### Cell-segmentation output

Typical root passed to `read_visium_hd(..., data_type='cellseg')` or `read_visium_hd_seg`:

```text
outs/
  segmented_outputs/
    filtered_feature_cell_matrix.h5
    graphclust_annotated_cell_segmentations.geojson
    spatial/
      tissue_hires_image.png
      tissue_lowres_image.png
      scalefactors_json.json
```

Required files:

- `filtered_feature_cell_matrix.h5`
- `graphclust_annotated_cell_segmentations.geojson` or fallback names `cell_segmentations.geojson`, `cell_segmentations_annotated.geojson`, `annotated_cell_segmentations.geojson`.
- Segmentation table must include `cell_id` or `cellid` and geometry.

Expected output:

- `obsm['spatial']`: polygon centroids.
- `obs['geometry']`: WKT serialization of segmentation geometry.
- `uns['omicverse_io']`: `{'type': 'visium_hd_seg', 'sample': sample}`.
- `uns['spatial'][sample]`: images and scalefactors when present.

## Xenium `outs` Layout

Typical root passed to `read_xenium(path)`:

```text
outs/
  cell_feature_matrix.h5
  cells.parquet              # or cells.csv.gz / cells.csv
  experiment.xenium
  cell_boundaries.parquet    # optional, or cell_boundaries.csv.gz / .csv
  morphology_focus.ome.tif   # optional V1
  morphology_mip.ome.tif     # optional V1
  morphology_focus/          # optional V2 / Prime
    morphology_focus_0000.ome.tif
    morphology_focus_0001.ome.tif
    morphology_focus_0002.ome.tif
    morphology_focus_0003.ome.tif
```

Required files:

- `cell_feature_matrix.h5`
- `cells.parquet`, `cells.csv.gz`, or `cells.csv`

Required cell metadata columns:

- Cell ID column: one of `cell_id`, `cellID`, `CellID`, `cell_ID`; otherwise first column is treated as cell ID.
- Centroids: `x_centroid`/`y_centroid` or `CenterX_local_px`/`CenterY_local_px`.

Optional files and effects:

- `experiment.xenium`: region/run/panel metadata and `pixel_size` for image scaling.
- `cell_boundaries.*`: converted to WKT in `obs['geometry']` when `load_boundaries=True`.
- Morphology OME-TIFFs: loaded into `uns['spatial'][library_id]['images']['hires']` when `load_image=True` and `tifffile` is available.

Memory guidance:

```python
adata = ov.io.spatial.read_xenium(
    'outs',
    load_image=False,          # safest first parse
    load_boundaries=False,     # skip polygon conversion for quick schema checks
)

adata_img = ov.io.spatial.read_xenium(
    'outs',
    load_image=True,
    image_key='morphology_focus_0000',
    image_max_dim=2048,
    cache_file='xenium_cached.h5ad',
)
```

Expected output:

- `X`: cells × genes sparse counts after non-gene features are dropped.
- `obs`: cell metadata excluding centroid columns.
- `obsm['spatial']`: centroid coordinates.
- `uns['spatial'][library_id]['metadata']`: parsed experiment metadata.
- `uns['spatial'][library_id]['scalefactors']['tissue_hires_scalef']`: `1 / pixel_size`, rescaled when a downsampled image pyramid level is loaded.
- `obs['geometry']`: optional WKT polygons.

## NanoString/CosMx SMI Layout

Typical root passed to `read_nanostring(path, counts_file=..., meta_file=..., fov_file=...)`:

```text
sample_dir/
  sample_exprMat_file.csv
  sample_metadata_file.csv
  sample_fov_positions_file.csv      # optional
  CellComposite/                     # optional FOV images
    ..._F001.png
  CellLabels/                        # optional segmentation label images
    ..._F001.png
```

Required arguments:

- `counts_file`: expression matrix CSV relative to `path`.
- `meta_file`: cell metadata CSV relative to `path`.

Required columns:

- Counts cell ID: one of `cell_ID`, `cell_id`, `cellid`, `CellID`.
- Counts FOV: one of `fov`, `FOV`, `fov_id`, `fovID`.
- Metadata cell ID: same accepted cell ID set.
- Metadata FOV: same accepted FOV set.
- Local coordinates in metadata: one of `CenterX_local_px`/`CenterY_local_px`, `centerx_local_px`/`centery_local_px`, `center_x_local_px`/`center_y_local_px`, or `CenterX`/`CenterY`.

Optional columns/files:

- Global coordinates: `CenterX_global_px`/`CenterY_global_px`, `centerx_global_px`/`centery_global_px`, `center_x_global_px`/`center_y_global_px`, or `x_global_px`/`y_global_px` create `obsm['spatial_fov']`.
- Geometry-like metadata columns: `geometry`, `WKT`, `polygon`, `cell_boundary`, or similar are converted to `obs['geometry']` when possible.
- `CellLabels/` images can be used to extract contours when geometry columns are absent and `shapely`/`scikit-image` are installed.

Expected output:

- `X`: cell × gene sparse counts.
- `obs`: metadata with FOV categorical column and `cell_ID` for segmentation matching.
- `obsm['spatial']`: local cell center coordinates.
- `obsm['spatial_fov']`: optional global coordinates.
- `uns['spatial'][fov]['images']['hires']`: optional FOV composite image.
- `uns['spatial'][fov]['images']['segmentation']`: optional label image.
- `uns['omicverse_io']['type']`: `nanostring` or `nanostring_seg`.

## Deconvolution Reference Contract

For `Tangram`, `Deconvolution`, split workflows, and tissue-zone workflows, record these assumptions before training:

| Object | Required fields | Notes |
| --- | --- | --- |
| scRNA reference `adata_sc` | `var_names`, `obs[celltype_key]`, preferably `layers['counts']` | Labels must be nonempty and biologically meaningful. |
| Spatial target `adata_sp` | `var_names`, `obsm['spatial']`, preferably `layers['counts']` | For image overlay also needs `uns['spatial']`. |
| Shared genes | `adata_sc.var_names.intersection(adata_sp.var_names)` | If too small, check gene symbol casing or use `gene_to_lowercase=True` for Tangram. |
| Deconvolution weights | DataFrame or array aligned to spots/cells × cell types | Nonnegative; rows should align to `adata.obs_names`. |
| Reference signatures | cell types × genes or genes × cell types | Cell-type labels must match deconvolution weights. |

Preflight snippet:

```python
shared = adata_sc.var_names.intersection(adata_sp.var_names)
print({'shared_genes': len(shared), 'sc_cells': adata_sc.n_obs, 'sp_spots': adata_sp.n_obs})
assert 'cell_type' in adata_sc.obs
assert 'spatial' in adata_sp.obsm
if 'counts' not in adata_sc.layers or 'counts' not in adata_sp.layers:
    print('Warning: layers["counts"] missing; use raw counts for deconvolution when possible.')
```

## Histology / WSI Contract

`ov.space.histo` uses WSIData/LazySlide-style containers rather than plain AnnData only.

Expected container slots:

- `wsi.shapes['tiles']`: tile polygons after `ov.space.histo.tile`.
- `wsi.tables['{backbone}_tiles']`: tile embeddings after `ov.space.histo.embed`.
- Prediction outputs: AnnData tables from `predict_expression` or `super_resolve`.
- Cache/scratch directories: user-selected paths with enough disk space for tiles and model outputs.

Gates before running:

- Python 3.10+ for `omicverse[histo]` dependencies.
- WSI format readable by `tiffslide`/OpenSlide stack.
- Tile size and `mpp` chosen for the WSI.
- Confirm model weights/access and GPU/CPU plan.
- Confirm gene list and method (`stpath`, `stflow`, `hest_fm`, `istar`).

## Plotting Contract

Common spatial plotting APIs consume these slots:

- Coordinate scatter: `obsm['spatial']`.
- Image overlay: `uns['spatial'][library]['images']` plus scalefactors.
- Segmentation overlay: `obs['geometry']` or segmentation images.
- Cell-type proportions: deconvolution output in `obsm`, often a DataFrame such as `tangram_ct_pred` or `q05_cell_abundance_w_sf`.

If image and points do not align, verify coordinate units and `tissue_hires_scalef` before changing biological parameters.
