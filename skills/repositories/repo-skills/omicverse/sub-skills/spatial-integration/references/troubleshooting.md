# Spatial Integration Troubleshooting

Use this matrix to diagnose OmicVerse spatial reader, AnnData, plotting, deconvolution, and histology failures. Prefer schema validation and small subsets before rerunning heavy models.

## Fast Diagnosis Commands

```bash
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind auto --path PATH
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind h5ad --path spatial.h5ad
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind xenium --path outs
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind nanostring --path sample_dir --counts-file expr.csv --meta-file metadata.csv
```

Success means `ERRORS: 0`; warnings identify optional images, boundaries, scale factors, or metadata that may affect plotting but not always expression analysis.

## Reader and File Layout Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `cell_feature_matrix.h5 not found` in Xenium | Passed wrong directory level, not the `outs` directory | Pass the directory containing `cell_feature_matrix.h5`; unzip/copy the complete Xenium outs bundle. |
| `cells.parquet / cells.csv.gz not found` | Missing Xenium cell metadata | Include `cells.parquet`, `cells.csv.gz`, or `cells.csv` from the same Xenium run. |
| `Could not find centroid columns` | Xenium cells metadata lacks accepted centroid column names | Ensure metadata has `x_centroid`/`y_centroid` or `CenterX_local_px`/`CenterY_local_px`. |
| Xenium morphology silently absent or warning says no image loaded | No OME-TIFF found, `tifffile` missing, channel key wrong, or image read failed | Start with `load_image=False`; then try `image_key='morphology_focus_0000'`, `image_max_dim=2048`, and install `tifffile` if needed. |
| Xenium V2/Prime huge memory use | Loading large morphology pyramid at high resolution | Lower `image_max_dim`; use `load_image=False` for analysis that only needs coordinates; use `cache_file` after a successful bounded parse. |
| `Tissue positions file not found` in Visium HD bin reader | Wrong root or bin-size directory | Pass `outs/binned_outputs/square_016um` or override `tissue_positions_path`; check for `.parquet` or CSV fallback. |
| `Neither filtered_feature_bc_matrix.h5 nor filtered_feature_bc_matrix found` | Count matrix not present under selected Visium HD bin root | Pass the correct bin output directory or override `count_h5_path`/`count_mtx_dir`. |
| Visium HD cellseg `Cell segmentations file not found` | Segmentation file name differs or segmented output not generated | Pass `cell_segmentations_path`; expected fallbacks include `cell_segmentations.geojson`, `cell_segmentations_annotated.geojson`, `annotated_cell_segmentations.geojson`. |
| Visium HD cellseg `No overlapping cell IDs` | Cell matrix and segmentation file from different run or naming mismatch | Confirm `filtered_feature_cell_matrix.h5` and GeoJSON are paired; inspect `cell_id`/`cellid` normalization. |
| NanoString `Counts file not found` or `Metadata file not found` | `counts_file`/`meta_file` not provided or typo | Pass filenames relative to the sample directory. |
| NanoString `No overlapping cell IDs` | Counts and metadata FOV/cell IDs are not combined consistently | Check `cell_ID` and `fov` columns in both files; ensure same FOV IDs and cell IDs. |
| NanoString missing `obsm['spatial_fov']` | Global coordinate columns absent | Local workflows can use `obsm['spatial']`; only cross-FOV/global plotting needs `obsm['spatial_fov']`. |

## AnnData Slot and Coordinate Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'spatial'` or `obsm['spatial'] absent` | Data is not spatial or reader did not populate coordinates | Use the correct spatial reader; add a `n_obs × 2` coordinate array to `adata.obsm['spatial']`; validate with the checker. |
| Spatial plot has points but no image | `uns['spatial']` lacks images or scalefactors | Use reader image options; verify `uns['spatial'][library]['images']`; plot scatter-only if images are unavailable. |
| Points/image are shifted or scaled incorrectly | Coordinate units and image pixels mismatch | Inspect `tissue_hires_scalef`, coordinate min/max, and image shape; for Xenium remember coordinates are microns. |
| Segmentation plotting fails | `obs['geometry']` absent or malformed | Enable `load_boundaries=True` for Xenium, use Visium HD cellseg, or ensure NanoString geometry/CellLabels are available. |
| `Delaunay triangulation` error | Too few, duplicated, or degenerate coordinates | Use KNN/radius graph instead of `delaunay=True`; deduplicate or filter invalid coordinates. |
| Spatial graph has unexpected degree | Wrong radius units or `n_neighs` too small/large | Match `radius` to coordinate units; print coordinate ranges before selecting radius. |
| Cropping wrong region | `crop_loc`/`crop_area` interpreted in image pixels, not gene-space or microns | Use `subset_window` for coordinate windows; use `crop_space_visium` only with correct image-scaled coordinates. |

## Optional Dependency and Backend Failures

| Feature | Missing dependency signal | Fix/gate |
| --- | --- | --- |
| `pySTAGATE`, `pySTAligner`, `Cal_Spatial_Net`, `pySpaceFlow` | Optional dependency error mentioning `torch` or `torch_geometric` | Install compatible torch/geometric stack; confirm CPU/GPU plan before running. |
| GASTON | Optional dependency error mentioning `torch` | Install torch; use small subset first. |
| Tangram | `Please install the tangram: pip install -U tangram-sc` | Install `tangram-sc`; validate shared genes and labels before training. |
| cell2location | import errors under `cell2location` stack | Install backend dependencies; choose explicit `accelerator`/`device` if GPU defaults are wrong. |
| RCTD | backend import/config errors | Confirm RCTD package and `rctd_kwargs` mode/config; use small pilot. |
| Visium HD cellseg geometry | `read_visium_hd_seg requires geopandas and shapely` | Install `geopandas` and `shapely`; or use bin-level input if segmentation is not needed. |
| NanoString contour extraction | warning about `shapely` or `scikit-image` | Install needed packages or provide WKT geometry column in metadata. |
| Xenium morphology | warning about `tifffile` | Install `tifffile` or set `load_image=False`. |
| Histology | optional dependency error for `lazyslide`, `wsidata`, `spatialdata`, `tiffslide`, `timm`, `huggingface_hub` | Use Python 3.10+ and install `omicverse[histo]`; confirm model access/cache/GPU. |
| Epigenomics | `epione` import error | Install the epione-backed optional stack before `ov.epi` wrappers. |

## GPU, Torch, and Runtime Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CUDA device error in Tangram/CAST/cell2location | Default device `cuda:0` or backend GPU default unavailable | Pass `device='cpu'` for Tangram/CAST-like calls or explicit `accelerator='cpu', device='auto'` in cell2location kwargs. |
| Torch/geometric import ABI failure | Incompatible torch, Python, CUDA, or PyG wheels | Install a matched torch/PyG stack; verify imports before running spatial models. |
| Out-of-memory during mapping/deconvolution | Too many cells, genes, spots, epochs, or image pixels | Subset genes/spots; reduce `marker_size`, `n_svgs`, epochs, `image_max_dim`, or batch size; use CPU for small validation. |
| CAST writes unexpected files | Default `output_path='output/CAST_Mark'` used | Choose a task-specific `output_path` and confirm write permissions. |
| Long-running histology tile/embed job | WSI too large, too many tiles, model download/cache slow | Start with smaller ROI/tile set; set cache/scratch explicitly; confirm weights before full run. |

## Deconvolution and Mapping Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Very few shared genes | Reference and spatial use different gene IDs or casing | Report shared-gene count; harmonize symbols; consider `gene_to_lowercase=True` for Tangram. |
| `cell_type` or requested label key missing | Wrong `celltype_key_sc` | Inspect `adata_sc.obs.columns`; pass the correct label key or run annotation first in the single-cell sub-skill. |
| Poor or all-zero cell-type predictions | Reference and spatial preprocessing mismatch, insufficient markers, or wrong counts layer | Use raw counts in `layers['counts']`; normalize consistently; verify marker genes and shared genes. |
| cell2location factor labels look prefixed/ugly | Labels stored in DataFrame columns instead of clean `uns` names | Check `uns[f'{obsm_key}_names']` or `uns['mod']['factor_names']`; pass explicit `cell_type_names` to tissue zones when needed. |
| `nmf_tissue_zones` rejects negative values | Input is centered/scaled embedding, not abundance | Use nonnegative proportions/abundances such as `q05_cell_abundance_w_sf` or `tangram_ct_pred`; do not use PCA/UMAP. |
| `cell_type_names` length error | Provided names do not match abundance columns | Match the number/order of columns in `obsm[obsm_key]`. |
| Split workflow negative weight error | Deconvolution weights contain negative values | Use valid nonnegative proportions; clip only if scientifically justified and documented. |
| Split secondary-cell error | `secondary_cell_type` includes labels missing from reference/weights | Align primary/secondary labels to reference cell-type names. |
| Reference mismatch in split purification | Reference genes/cell types do not align with `adata`/weights | Reindex reference to `adata.var_names` and weight columns before calling split helpers. |

## Histology-to-Spatial Specific Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Python version marker skips histo dependencies | `omicverse[histo]` dependencies require Python 3.10+ | Use Python 3.10 or newer for histology work; base OmicVerse can run on older supported Python. |
| WSI cannot open | Missing OpenSlide/tiffslide support or unsupported file | Install `tiffslide`/OpenSlide-compatible dependencies; test `open_wsi` before tiling. |
| Model download/auth failure | Gated Hugging Face model or no network/cache | Ask user to provide access and cache policy; do not embed credentials in code or notes. |
| Tile cache explodes in size | Full WSI tiled without ROI/budget | Select ROI or smaller pilot; choose cache/scratch paths with enough space; clean stale caches intentionally. |
| Predictions have unexpected genes | Method vocabulary/organ/tech mismatch | Pass explicit gene list; verify method supports requested organ/technology. |
| HEST-FM poor fit | Paired reference slide insufficient or misaligned | Validate reference coordinates and expression; inspect spot features before model fitting. |

## Epigenomics and Spatial-Adjacent Routes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ov.epi.check_epione()` fails | Epione optional stack missing | Install epione dependencies before ATAC/multiome workflows. |
| scATAC fragment import fails | Fragment file/chrom sizes mismatch | Verify fragment path, chromosome names, and `ov.epi.data.hg38`/`mm10` choice. |
| Transfer labels/joint embedding poor | Reference and query modalities/features do not align | Build gene activity/peak features first; verify shared features and labels. |
| User asks for FASTQ/BAM alignment | Upstream external binary workflow, not this sub-skill | Route to specialist domains for binary/path/auto-install policy. |

## Reporting Checklist

When handing off a spatial result, include:

- Reader/API used and key arguments (`load_image`, `image_max_dim`, `data_type`, `binsize`, label keys).
- AnnData shape and key slots present: `obsm`, `layers`, `uns['spatial']`, `obs['geometry']`.
- Coordinate units and image/scalefactor assumptions.
- Shared-gene count for mapping/deconvolution.
- Optional dependencies or GPU/backend choices actually used.
- Warnings, skipped optional images/boundaries, and any remaining uncertainty.
