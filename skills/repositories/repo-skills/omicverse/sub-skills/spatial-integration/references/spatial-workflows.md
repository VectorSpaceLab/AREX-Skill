# Spatial Integration Workflows

These workflows are safe, self-contained guides for using OmicVerse spatial APIs without depending on the source checkout. Validate inputs first, then choose the lightest model that answers the user's question.

## 1. Validate and Load Spatial Data

Use the bundled checker before parsing a large spatial directory:

```bash
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind auto --path outs
```

Then choose the reader:

```python
import omicverse as ov
from omicverse.io import spatial as ovs

# Visium HD bin-level output
adata = ovs.read_visium_hd('outs/binned_outputs/square_016um', data_type='bin', binsize=16)

# Visium HD cell segmentation output
adata_cell = ovs.read_visium_hd('outs/segmented_outputs', data_type='cellseg')

# Xenium lightweight first load
adata_xe = ovs.read_xenium('outs', load_image=False, load_boundaries=False)

# Xenium bounded image load
adata_xe_img = ovs.read_xenium('outs', load_image=True, image_max_dim=2048, cache_file='xenium_cache.h5ad')

# NanoString/CosMx
adata_ns = ovs.read_nanostring(
    'sample_dir',
    counts_file='sample_exprMat_file.csv',
    meta_file='sample_metadata_file.csv',
    fov_file='sample_fov_positions_file.csv',
)
```

Validation after load:

```python
assert 'spatial' in adata.obsm
print(adata.shape)
print(adata.obsm['spatial'][:3])
print(list(adata.uns.get('spatial', {}).keys()))
```

Expected outputs:

- A cells/spots × genes AnnData.
- Coordinates in `obsm['spatial']`.
- Image metadata in `uns['spatial']` when available.
- Optional segmentation geometry in `obs['geometry']`.

## 2. Spatial Graphs, Autocorrelation, and SVGs

Use this when the user asks for spatially variable genes, spatial autocorrelation, local neighborhoods, or graph features.

```python
import omicverse as ov

ov.space.spatial_neighbors(
    adata,
    spatial_key='spatial',
    n_neighs=6,
    key_added='spatial',
)

moran = ov.space.spatial_autocorr(
    adata,
    connectivity_key='spatial_connectivities',
    genes=None,
    mode='moran',
    n_perms=None,
)

adata = ov.space.svg(
    adata,
    mode='pearsonr',
    n_svgs=3000,
    platform='visium',
)
```

Use `radius=` when physical distance matters, for example Xenium microns or Visium pixel radius. Use `delaunay=True` only when the coordinate set is nondegenerate; duplicated coordinates can trigger triangulation errors.

Expected output signals:

- `adata.obsp['spatial_connectivities']`
- `adata.obsp['spatial_distances']`
- `adata.uns['spatial_neighbors']`
- Moran/Geary result table or SVG flags/rankings depending on mode.

## 3. Plot and Align Spatial Images

For simple spatial scatter/image overlay, ensure the AnnData has both coordinates and image metadata. Generic plotting basics route to the core analysis sub-skill, but spatial image alignment details belong here.

```python
import omicverse as ov

# Crop/subset coordinates without requiring image operations.
roi = ov.space.subset_window(adata, xlim=(1000, 2500), ylim=(500, 1800), basis='spatial')

# Visium-like image crop; requires uns['spatial'][library_id]['images'] and scalefactors.
library_id = next(iter(adata.uns['spatial']))
roi_img = ov.space.crop_space_visium(
    adata,
    crop_loc=(500, 500),
    crop_area=(1000, 1000),
    library_id=library_id,
    scale=1,
    res='hires',
)

rot = ov.space.rotate_space_visium(adata, angle=90, library_id=library_id, res='hires')
```

Coordinate caution:

- `crop_space_visium` treats crop coordinates as image pixel coordinates and uses `tissue_hires_scalef`.
- Xenium coordinates are in microns; image overlay uses `tissue_hires_scalef` to map microns to pixels.
- NanoString local coordinates are FOV-local pixels; global coordinates, when available, are in `obsm['spatial_fov']`.

## 4. Tangram-like scRNA-to-Spatial Mapping

Use when a user has a scRNA reference and spatial target and wants cell-type proportions or projected annotations.

Preflight:

```python
celltype_key = 'cell_type'
shared = adata_sc.var_names.intersection(adata_sp.var_names)
print({'shared_genes': len(shared), 'sc_cells': adata_sc.n_obs, 'sp_obs': adata_sp.n_obs})
assert celltype_key in adata_sc.obs
assert 'spatial' in adata_sp.obsm
assert len(shared) > 0
```

Lightweight CPU sketch for small data or verification:

```python
import omicverse as ov

adata_sc2 = adata_sc[:, shared].copy()
adata_sp2 = adata_sp[:, shared].copy()

tg = ov.space.Tangram(
    adata_sc=adata_sc2,
    adata_sp=adata_sp2,
    clusters=celltype_key,
    marker_size=100,
    gene_to_lowercase=False,
)
tg.train(mode='clusters', num_epochs=50, device='cpu')
adata_ct = tg.cell2location()
```

Production choices:

- Increase `num_epochs` only after validating labels, shared genes, and memory.
- Use `gene_to_lowercase=True` when reference and spatial gene symbols differ only by casing.
- Use `device='cuda:0'` only when the user confirms a working GPU backend.

Expected output:

- `tg.ad_map`: Tangram mapping AnnData.
- Projected cell-type annotations in spatial data.
- `adata_ct` or an `obsm` table such as `tangram_ct_pred` for downstream tissue zones.

## 5. Unified Deconvolution Manager

Use `ov.space.Deconvolution` when the user wants to compare or switch among Tangram, cell2location, FlashDeconv, Starfysh, or RCTD.

```python
import omicverse as ov

decov = ov.space.Deconvolution(adata_sp=adata_sp, adata_sc=adata_sc)
decov.preprocess_sc(mode='shiftlog|pearson', n_HVGs=3000, target_sum=1e4)
decov.preprocess_sp(mode='pearsonr', n_svgs=3000, platform='visium', target_sum=50*1e4)

decov.deconvolution(
    method='Tangram',
    celltype_key_sc='cell_type',
    tangram_kwargs={'mode': 'clusters', 'num_epochs': 100, 'device': 'cpu'},
)
```

Backend gates:

- `method='Tangram'`: requires `tangram-sc`; GPU optional.
- `method='cell2location'`: requires cell2location stack and PyTorch; OmicVerse defaults to GPU training args when CUDA is available unless explicit device args are passed.
- `method='RCTD'`: requires RCTD-related backend; configure `rctd_kwargs` intentionally.
- `method='FlashDeconv'` and `method='starfysh'`: use only after dependency and input checks.

Output handling:

```python
if decov.adata_cell2location is not None:
    print(decov.adata_cell2location.shape)
if 'q05_cell_abundance_w_sf' in decov.adata_sp.obsm:
    print(decov.adata_sp.obsm['q05_cell_abundance_w_sf'].shape)
```

## 6. Tissue Zones from Cell-Type Abundances

Use after Tangram/cell2location/deconvolution creates a nonnegative spot × cell-type matrix.

```python
import omicverse as ov

tz = ov.space.nmf_tissue_zones(
    adata,
    obsm_key='q05_cell_abundance_w_sf',
    n_factors=3,
    top_k=5,
    normalize='rows',
    seed=0,
)

print(adata.obsm['X_tissue_zones'].shape)
print(tz.factor_loadings.head())
print(tz.factor_top_cell_types)
```

When `obsm[obsm_key]` is a DataFrame, OmicVerse uses its columns as cell-type labels. If `uns[f'{obsm_key}_names']` or `uns['mod']['factor_names']` exists, those clean labels are preferred.

Failure signals:

- Missing `obsm_key`: choose the deconvolution output actually present.
- Negative values: use an abundance/proportion matrix, not centered/scaled embeddings.
- Wrong `cell_type_names` length: ensure labels match the number of abundance columns.

## 7. Split Purification and Balancing

Use when deconvolution produced mixed spot/cell weights and the user wants purified profiles or residual reassignment.

```python
import omicverse as ov

ov.space.split_purify(
    adata,
    deconvolution_weights=weights,       # rows align to adata.obs_names
    reference=reference_profiles,        # cell types × genes, or transpose-compatible
    primary_cell_type=primary_labels,
    layer='counts',
    result_layer='split_purified',
)

ov.space.split_spatial_score(
    adata,
    deconvolution_weights=weights,
    primary_cell_type=primary_labels,
    secondary_cell_type=secondary_labels,
    spatial_key='spatial',
    k=20,
)

ov.space.split_balance(
    adata,
    purified_layer='split_purified',
    threshold=0.15,
    spot_class_key='spot_class',
    result_layer='split_balanced',
)

ov.space.split_reassign_residuals(
    adata,
    raw_layer='counts',
    purified_layer='split_balanced',
    spatial_key='spatial',
    result_layer='split_reassigned',
    self_keep=0.25,
)
```

Expected outputs:

- `layers['split_purified']`
- `obs['first_type']`, `obs['purification_status']`
- `obs['neighborhood_weights_second_type']`
- `layers['split_balanced']`
- `layers['split_reassigned']`
- `uns['split_spatial_neighbors']`, `uns['split_reassignment_operator']`, and residual statistics.

Input validation checklist:

- Weights are nonnegative.
- Weight rows align with `adata.obs_names`.
- Reference genes align with `adata.var_names`.
- Primary/secondary labels exist in the reference cell-type index.
- `radius` is positive when provided.

## 8. Optional Spatial Domain and Alignment Backends

Use these only after confirming dependencies and backend choices.

```python
# Spatial graph attention domains; requires torch + torch_geometric.
ov.space.pySTAGATE(adata, n_domains=7, radius=50)

# CellCharter-style spatial feature aggregation/clustering.
ov.space.cellcharter(
    adata,
    n_clusters=8,
    use_rep='X_pca',
    spatial_key='spatial',
    build_spatial_graph=True,
    n_neighs=6,
)

# CAST writes output files; choose output_path intentionally.
ov.space.CAST(
    adata,
    sample_key='sample',
    basis='spatial',
    layer='norm_1e4',
    output_path='cast_output',
    device='cuda:0',
)
```

Gates:

- `torch`/`torch_geometric` for `pySTAGATE`, `pySTAligner`, `Cal_Spatial_Net`, `pySpaceFlow`.
- GPU and output directory policy for `CAST`.
- Correct embedding keys for `CellMap`/`CellLoc`: `use_rep_sc` and `use_rep_sp` must exist.
- Correct coordinate and region keys for `STT`: defaults are `spatial_loc='xy_loc'` and `region='Region'`, so pass `spatial_loc='spatial'` when using standard spatial AnnData.

## 9. Histology-to-Spatial Prediction

Use only when the user explicitly requests H&E/WSI to spatial expression or super-resolution. This is not a default validation route.

Preflight questions:

- Is Python 3.10+ available with `omicverse[histo]` installed?
- What WSI file and paired spatial reference, if any, should be used?
- Which method: `stpath`, `stflow`, `hest_fm`, or `istar`?
- Which backbone: for example `gigapath` or `ctranspath`?
- What tile size, `mpp`, gene list, cache directory, and GPU/CPU plan?
- Does the user have required model access or credentials for gated weights?

Skeleton after confirmation:

```python
import omicverse as ov

wsi = ov.space.histo.open_wsi('slide.svs')
ov.space.histo.tile(wsi, tile_px=224, mpp=0.5)
ov.space.histo.embed(wsi, model='gigapath', batch_size=16, num_workers=0)

pred = ov.space.histo.predict_expression(
    wsi,
    method='stpath',
    organ='Breast',
    tech='Visium',
    genes=['EPCAM', 'CDH1', 'KRT8'],
)
```

For paired-reference HEST-FM:

```python
pred = ov.space.histo.predict_expression(
    wsi,
    method='hest_fm',
    reference=ref_adata,
    fm_backbone='ctranspath',
)
```

Expected outputs are method-specific AnnData predictions or WSIData tables; inspect shape, gene names, and coordinate/table alignment before downstream plotting.

## 10. Epigenomics and Bulk-to-Spatial Bridges

Use when spatial interpretation depends on upstream multimodal features.

Epigenomics/multiome route:

```python
import omicverse as ov

ov.epi.check_epione()
adata_atac = ov.epi.pp.import_fragments(fragment_file, chrom_sizes=ov.epi.data.hg38)
genes = ov.epi.io.get_gene_annotation(ov.epi.data.hg38)
ov.epi.pp.tsse(adata_atac, genes)
ov.epi.pp.qc(adata_atac)
ov.epi.pp.add_tile_matrix(adata_atac, bin_size=500)
ov.epi.tl.iterative_lsi(adata_atac, n_components=30)
ov.epi.tl.transfer_labels(query=adata_atac, reference=adata_ref)
```

Bulk/single/spatial route:

```python
import omicverse as ov

b2s = ov.bulk2single.Bulk2Single(
    bulk_data=bulk_adata,
    single_data=sc_adata,
    celltype_key='cell_type',
    gpu=0,
)
# Heavy: run only after confirming runtime budget.
# b2s.train(epoch_num=5000, save=True)

s2sp = ov.bulk2single.Single2Spatial(
    single_data=sc_adata,
    spatial_data=spatial_adata,
    celltype_key='cell_type',
    spot_key=['xcoord', 'ycoord'],
    gpu=0,
)
```

Route external FASTQ/BAM alignment and binary installation policies to specialist domains.
