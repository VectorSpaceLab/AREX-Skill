# Spatial Integration API Reference

This reference lists OmicVerse public surfaces most relevant to spatial transcriptomics, histology-to-ST, mapping/deconvolution, and spatial-adjacent multimodal workflows.

## Spatial Readers

Import pattern:

```python
import omicverse as ov
from omicverse.io import spatial as ovs
```

| API | Signature | Use | Produces |
| --- | --- | --- | --- |
| `ovs.read_visium(path, ...)` | classic Visium reader | Standard Space Ranger Visium outputs | AnnData with `obsm['spatial']` and `uns['spatial']` |
| `ovs.read_visium_hd(path, data_type='bin', sample=None, binsize=16, ...)` | unified Visium HD reader | Dispatches to bin-level or cell-segmentation reader | AnnData with spatial slots |
| `ovs.read_visium_hd_bin(path, sample=None, binsize=16, count_h5_path='filtered_feature_bc_matrix.h5', count_mtx_dir='filtered_feature_bc_matrix', tissue_positions_path='spatial/tissue_positions.parquet', hires_image_path='spatial/tissue_hires_image.png', lowres_image_path='spatial/tissue_lowres_image.png', scalefactors_path='spatial/scalefactors_json.json')` | bin-level Visium HD | `outs` or `outs/binned_outputs/square_016um` style outputs | `obsm['spatial']`, `uns['spatial'][sample]['binsize']`, images, scalefactors |
| `ovs.read_visium_hd_seg(path, sample=None, cell_segmentations_path='graphclust_annotated_cell_segmentations.geojson', count_h5_path='filtered_feature_cell_matrix.h5', ...)` | cell-segmentation Visium HD | `outs/segmented_outputs` with cell matrix and GeoJSON | `obsm['spatial']`, `obs['geometry']`, `uns['omicverse_io']['type']='visium_hd_seg'` |
| `ovs.write_visium_hd_cellseg(adata, path, sample=None)` | writer | Export segmentation-compatible AnnData geometries | cellseg output files |
| `ovs.read_xenium(path, *, library_id=None, load_image=True, image_key='morphology_focus', image_max_dim=4096, load_boundaries=True, cache_file=None)` | Xenium reader | 10x Xenium `outs` bundle | `X` counts, cell metadata, micron centroids, optional morphology and WKT geometry |
| `ovs.read_nanostring(path, *, counts_file, meta_file, fov_file=None)` | NanoString/CosMx reader | SMI expression matrix plus metadata and optional FOV positions | `obsm['spatial']`, optional `obsm['spatial_fov']`, FOV images, optional `obs['geometry']` |
| `ovs.read_atera(path, ...)` | Atera reader | Atera-style spatial output | Similar to Xenium plus platform-specific metadata |

### Reader Notes

- `read_xenium(..., load_image=False)` is the safest first load for huge morphology images.
- `read_xenium(..., image_max_dim=2048 or 4096)` bounds the OME-TIFF pyramid level loaded into memory.
- `read_visium_hd_seg` requires geometry support (`geopandas`, `shapely`) because it reads GeoJSON segmentations.
- `read_nanostring` requires explicit `counts_file` and `meta_file`; it only loads FOV images when `CellComposite/` or `CellLabels/` folders exist.

## Core Spatial Analysis

| API | Signature | Inputs | Outputs |
| --- | --- | --- | --- |
| `ov.space.spatial_neighbors` | `spatial_neighbors(adata, spatial_key='spatial', n_neighs=6, radius=None, delaunay=False, set_diag=False, key_added='spatial', copy=False)` | AnnData with `obsm[spatial_key]` | `obsp['{key_added}_connectivities']`, `obsp['{key_added}_distances']`, `uns['{key_added}_neighbors']` |
| `ov.space.spatial_autocorr` | `spatial_autocorr(adata, connectivity_key='spatial_connectivities', genes=None, mode='moran', transformation=True, n_perms=None, two_tailed=False, corr_method='fdr_bh', layer=None, seed=None, copy=False, n_jobs=1)` | Spatial graph and expression | DataFrame of Moran or Geary statistics |
| `ov.space.moranI` | `moranI(..., auto_spatial_neighbors=False, n_neighs=6, radius=None, spatial_key='spatial')` | Spatial graph or coordinates | Moran I result table |
| `ov.space.svg` | `svg(adata, mode='prost', n_svgs=3000, target_sum=50*1e4, platform='visium', mt_startwith='MT-', **kwargs)` | Spatial AnnData | Spatially variable gene annotations and selected features |
| `ov.space.subset_window` | `subset_window(adata, xlim, ylim, basis='spatial')` | Spatial coordinates | AnnData copy restricted to rectangular coordinate window |
| `ov.space.crop_space_visium` | `crop_space_visium(adata, crop_loc, crop_area, library_id, scale, spatial_key='spatial', res='hires')` | Visium-like image-backed AnnData | Cropped AnnData and image |
| `ov.space.rotate_space_visium` | `rotate_space_visium(adata, angle, center=None, spatial_key='spatial', res='hires', library_id=None, interpolation_order=1)` | Visium-like image-backed AnnData | Rotated image and coordinates |
| `ov.space.map_spatial_auto` | `map_spatial_auto(adata_rotated, method='phase')` | Rotated spatial image | Automated image offset mapping |
| `ov.space.map_spatial_manual` | `map_spatial_manual(...)` | Spatial image and manual control points | Manual alignment/mapping output |

Minimal graph/SVG sequence:

```python
import omicverse as ov

ov.space.spatial_neighbors(adata, spatial_key='spatial', n_neighs=6, key_added='spatial')
moran = ov.space.spatial_autocorr(adata, mode='moran', genes=['EPCAM', 'KRT8'])
adata = ov.space.svg(adata, mode='pearsonr', n_svgs=3000, platform='visium')
```

## Spatial Mapping and Deconvolution

| API | Signature | Main Assumptions | Output Signal |
| --- | --- | --- | --- |
| `ov.space.Tangram` | `Tangram(adata_sc, adata_sp, clusters='', marker_size=100, gene_to_lowercase=False)` then `train(mode='clusters', num_epochs=500, device='cuda:0', **kwargs)` | `tangram-sc` installed; scRNA reference has `obs[clusters]`; genes intersect | `ad_map`, projected cell-type annotations, `cell2location()` output |
| `ov.space.Deconvolution` | `Deconvolution(adata_sp, adata_sc=None)` | Spatial AnnData plus optional scRNA reference; `layers['counts']` recommended | Manager object for backend-specific outputs |
| `Deconvolution.preprocess_sc` | `preprocess_sc(mode='shiftlog|pearson', n_HVGs=3000, target_sum=1e4, **kwargs)` | scRNA reference | HVG-filtered normalized reference |
| `Deconvolution.preprocess_sp` | `preprocess_sp(mode='pearsonr', n_svgs=3000, target_sum=50*1e4, platform='visium', mt_startwith='MT-', subset_genes=True, **kwargs)` | Spatial data | SVG-filtered spatial object |
| `Deconvolution.deconvolution` | `deconvolution(method='Tangram', celltype_key_sc='cell_type', batch_key_sc=None, batch_key_sp=None, tangram_kwargs=None, cell2location_scrna_kwargs=None, cell2location_spatial_kwargs=None, N_cells_per_location=30, detection_alpha=200, sample_kwargs=None, flashdeconv_kwargs=None, starfysh_kwargs=None, rctd_kwargs=None, spatial_type='visium', gene_sig=None, categorical_covariate_keys_sc=None)` | Backend-specific dependencies and labels | `adata_cell2location`, `adata_impute`, model attributes, or backend-specific matrices |
| `ov.space.calculate_gene_signature` | `calculate_gene_signature(adata_sc, clustertype, rank=True, key='rank_genes_groups', foldchange=2, topgenenumber=20)` | scRNA labels/marker ranking | Gene-signature table |
| `ov.space.nmf_tissue_zones` | `nmf_tissue_zones(adata, obsm_key='q05_cell_abundance_w_sf', n_factors=10, cell_type_names=None, top_k=5, obsm_added='X_tissue_zones', factor_prefix='zone', normalize=None, init='nndsvd', max_iter=500, tol=1e-4, seed=0)` | Nonnegative spot × cell-type abundance matrix | `obsm['X_tissue_zones']`, `TissueZones` factor loadings and top cell types |

Safe Tangram-like preflight:

```python
shared = adata_sc.var_names.intersection(adata_sp.var_names)
assert len(shared) >= 200, f'Only {len(shared)} shared genes; check gene symbols.'
assert 'cell_type' in adata_sc.obs
assert 'spatial' in adata_sp.obsm
```

CPU-friendly Tangram sketch after preflight:

```python
tg = ov.space.Tangram(adata_sc[:, shared].copy(), adata_sp[:, shared].copy(), clusters='cell_type')
tg.train(mode='clusters', num_epochs=50, device='cpu')
adata_ct = tg.cell2location()
```

## Split Purification and Tissue Zones

| API | Signature | Use |
| --- | --- | --- |
| `ov.space.split_purify` | `split_purify(adata, deconvolution_weights, reference, primary_cell_type=None, layer='counts', result_layer='split_purified', cells_to_purify=None, chunk_size=50000, copy=False)` | Purify mixed spots/cells using cell-type weights and reference profiles |
| `ov.space.split_spatial_score` | `split_spatial_score(adata, deconvolution_weights, primary_cell_type, secondary_cell_type=None, spatial_key='spatial', k=20, radius=None)` | Score spatial support for secondary contamination/diffusion |
| `ov.space.split_balance` | `split_balance(adata, purified_layer='split_purified', score_key='neighborhood_weights_second_type', threshold=0.15, spot_class_key=None, result_layer='split_balanced', raw_layer='counts', swap_labels=False)` | Select purified/raw/removed profiles by score and optional spot class |
| `ov.space.split_reassign_residuals` | `split_reassign_residuals(adata, raw_layer='counts', purified_layer='split_balanced', spatial_key='spatial', mode='count_proportional', result_layer='split_reassigned', k=20, radius=None, self_keep=0.0)` | Reassign residual counts through spatial neighborhoods |

Expected inputs for split workflows:

- `deconvolution_weights`: cells/spots × cell types, nonnegative, aligned to `adata.obs_names`.
- `reference`: cell types × genes or genes × cell types; cell-type labels must match weights and `primary_cell_type`.
- `adata.layers['counts']`: raw counts preferred; sparse matrices are accepted by tested paths.
- `adata.obsm['spatial']`: required for neighborhood scoring/reassignment.

## Spatial Domain, Alignment, and Communication Helpers

| API | Use | Gating |
| --- | --- | --- |
| `ov.space.pySTAGATE`, `clusters`, `merge_cluster` | Graph attention spatial domains | Requires `torch` and `torch_geometric`; GPU recommended for large data |
| `ov.space.pySTAligner`, `Cal_Spatial_Net` | Multi-sample spatial alignment/network construction | Requires `torch` and `torch_geometric` |
| `ov.space.pySpaceFlow` | Spatial flow analysis | Requires `torch` and `torch_geometric` |
| `ov.space.GASTON` | Spatial deconvolution/domain modeling | Requires `torch` |
| `ov.space.CAST(adata, sample_key=None, basis='spatial', layer='norm_1e4', output_path='output/CAST_Mark', gpu_t=0, device='cuda:0', **kwargs)` | CAST spatial organization/alignment | Writes output files; set output path intentionally |
| `ov.space.cellcharter(adata, n_clusters, ..., build_spatial_graph=True, delaunay=True, ...)` | Spatial neighborhood feature aggregation and clustering | Backend can use optional `cellcharter`; graph keys must match |
| `ov.space.STT(adata, spatial_loc='xy_loc', region='Region')` then `train(...)` | Spatial transition tensor / state dynamics | Needs expected coordinate and region keys |
| `ov.space.CellMap(adata_sc, adata_sp, use_rep_sc='X_pca', use_rep_sp='X_pca')` | Cell mapping between single-cell and spatial embeddings | Requires precomputed embeddings |
| `ov.space.CellLoc(adata_sc, adata_sp, use_rep_sc='X_pca', use_rep_sp='X_pca')` | Cell localization | Requires precomputed embeddings |
| `ov.space.create_communication_anndata(adata, clustering_column, n_permutations=100)` | Spatial communication summary AnnData | Needs ligand/receptor database-derived results and cluster labels |

## Bulk/Single/Spatial Bridge

Import pattern:

```python
import omicverse as ov
```

| API | Signature | Use |
| --- | --- | --- |
| `ov.bulk2single.Bulk2Single` | `Bulk2Single(bulk_data, single_data, celltype_key, bulk_group=None, max_single_cells=5000, top_marker_num=500, ratio_num=1, gpu=0)` | Generate single-cell-like profiles from bulk and reference |
| `Bulk2Single.train` | `train(vae_save_dir='save_model', vae_save_name='vae', generate_save_dir='output', generate_save_name='output', batch_size=512, learning_rate=1e-4, hidden_size=256, epoch_num=5000, patience=50, save=True)` | VAE training/generation; heavy by default |
| `ov.bulk2single.Single2Spatial` | `Single2Spatial(single_data, spatial_data, celltype_key, spot_key=['xcoord', 'ycoord'], top_marker_num=500, marker_used=True, gpu=0)` | Map generated or observed single cells to spatial coordinates |
| `Single2Spatial.train` | `train(spot_num, cell_num, ..., num_epochs=1000, batch_size=1000, predicted_size=32)` | Heavy spatial mapping training |
| `ov.bulk2single.spatial_mapping` | `spatial_mapping(generate_sc_meta, generate_sc_data, input_st_data_path, input_st_meta_path, map_save_dir='output', map_save_name='map')` | File-based mapping output |

Use these routes only after validating that bulk/sample metadata, cell-type labels, and spatial coordinate keys are aligned. Route purely statistical bulk work to the multiomics statistics sub-skill.

## Histology-to-Spatial (`ov.space.histo`)

Optional extra: install with `omicverse[histo]` on Python 3.10+ to pull `lazyslide`, `wsidata`, `spatialdata`, `tiffslide`, `timm`, and `huggingface_hub`.

| API | Use |
| --- | --- |
| `ov.space.histo.open_wsi` | Open a WSI as WSIData |
| `ov.space.histo.tile` | Create tiles in `wsi.shapes['tiles']` |
| `ov.space.histo.read_visium_with_image` | Pair Visium counts and H&E WSI |
| `ov.space.histo.embed` | Compute tile embeddings with backbones such as `gigapath` or `ctranspath` |
| `ov.space.histo.available_backbones` | Inspect supported embedding backbones |
| `ov.space.histo.predict_expression` | Predict expression with `method='stpath'`, `'stflow'`, or `'hest_fm'` |
| `ov.space.histo.super_resolve` | Super-resolve ST expression, e.g. iStar-style workflows |
| `ov.space.histo.spot_features` | Extract spot-aligned pathology features |

Never start histology prediction as a default check. First confirm WSI path, tile size, microns-per-pixel, cache location, model/backbone, gene list, and whether the user has required model access.

## Epigenomics / Spatial-Adjacent Multimodal Routes

`ov.epi` wraps epione and is useful for ATAC/multiome features that later become spatial labels, gene activity matrices, or peak-to-gene interpretation.

| API area | Examples | Use |
| --- | --- | --- |
| `ov.epi.check_epione()` | dependency check | Verify backing package before using wrappers |
| `ov.epi.io` | `read_ATAC_10x`, `read_gtf`, `get_gene_annotation`, `merge_peaks` | Read epigenomic inputs |
| `ov.epi.pp` | `import_fragments`, `tsse`, `qc`, `add_tile_matrix`, `make_peak_matrix`, `make_gene_matrix`, `neighbors` | Build ATAC/multiome AnnData slots |
| `ov.epi.tl` | `iterative_lsi`, `clusters`, `umap`, `add_gene_score_matrix`, `peak_to_gene`, `coaccessibility`, `transfer_labels`, `joint_embedding` | Analyze and integrate epigenomic data |
| `ov.epi.pl` | `umap`, `embedding`, `plot_peak2gene`, `plot_footprints` | Visualize epigenomic results |

Route raw upstream alignment from FASTQs/BAMs and external binaries to specialist domains, not this sub-skill.
