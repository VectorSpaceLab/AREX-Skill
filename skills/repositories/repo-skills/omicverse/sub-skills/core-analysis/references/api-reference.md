# Core API Reference

This reference summarizes public OmicVerse APIs used by the `core-analysis` sub-skill. Signatures may accept additional keyword arguments that are forwarded to Scanpy, AnnData, pandas, or backend-specific implementations.

## Root Lazy Attributes

| API | Purpose | Notes |
| --- | --- | --- |
| `ov.read(path, backend='python', **kwargs)` | Universal reader for `.h5ad`, `.csv`, `.tsv`, `.txt`, and gzipped text | For `.h5ad`, `backend='rust'` uses `anndataoom` when installed |
| `ov.set_seed(seed=0, deterministic=False, verbose=True)` | Seed Python, NumPy, PyTorch/CUDA, MLX, and `ov.settings.seed` | Core random-state defaults follow this seed unless explicitly overridden |
| `ov.list_functions(category=None)` | Print registered functions, optionally by category | Hydration may import submodules lazily |
| `ov.find_function(query, verbose=False)` | Print and return the best matching registered function | Works with aliases and multilingual names |
| `ov.get_function_help(query)` | Print description, aliases, category, signature, docs, examples, and related functions | Useful before using unfamiliar APIs |
| `ov.recommend_function(task_description, n=5)` | Print and return function recommendations from task keywords | Simple keyword scoring; verify with `get_function_help` |
| `ov.export_registry(filepath=None, format='json', include_source=False)` | Export registry metadata | Use `format='dict'` for machine-readable inspection |
| `ov.load_package(packages=None, omicverse_modules=None, include_omicverse_modules=True, show_summary=True)` | Preload common dependencies and lazy OmicVerse modules | Returns loaded/failed results rather than silently failing |

Lazy import failures are converted to `AttributeError` messages like `Failed to import omicverse.pp: <error>. A required dependency may not be installed.` Import the named module directly to inspect the underlying optional dependency error.

## IO APIs

| API | Key parameters | Returns | Slot/schema effects |
| --- | --- | --- | --- |
| `ov.io.read(path, backend='python', **kwargs)` | `backend='python'` or `'rust'` for `.h5ad`; pandas kwargs for tables | `AnnData` or `pandas.DataFrame` | `.h5ad` returns AnnData; tables return DataFrame |
| `ov.io.read_h5ad(filename, **kwargs)` | AnnData `read_h5ad` kwargs such as `backed='r'` | `AnnData` | Preserves existing h5ad slots |
| `ov.io.read_10x_h5(filename, genome=None, gex_only=True, backup_url=None)` | `gex_only` filters v3 feature types to Gene Expression | `AnnData` | `.obs_names` are barcodes; `.var_names` are feature names; `.var` includes IDs and feature metadata |
| `ov.io.read_10x_mtx(path, var_names='gene_symbols', make_unique=True, gex_only=True, prefix=None, compressed=True)` | `var_names` may be `'gene_symbols'` or `'gene_ids'`; `compressed=False` for plain STARsolo-like exports | `AnnData` | Matrix is transposed to cells × genes; `.var['gene_ids']` or `.var['gene_symbols']`; `.var['feature_types']` for v3 |
| `ov.io.read_csv(filepath_or_buffer, sep=None, on_duplicate='warn', **kwargs)` | `on_duplicate='warn'`, `'raise'`, or `'ignore'` | `DataFrame` | Raw header duplicate scan before pandas auto-renaming |
| `ov.io.read_table(filepath_or_buffer, sep='\t', on_duplicate='warn', **kwargs)` | TSV counterpart of `read_csv` | `DataFrame` | Same duplicate sample-label detection |
| `ov.io.save(file, path)` / `ov.io.load(path, backend=None)` | `backend=None`, `'pickle'`, or `'cloudpickle'` for load | Any Python object | Pickle/cloudpickle persistence for intermediate results |

Root `ov.read(...)` maps to the single-cell reader. Prefer `ov.io.read_*` when the format is known because parameters and error messages are clearer.

## Dataset APIs

| API | Purpose | Network behavior |
| --- | --- | --- |
| `ov.datasets.create_mock_dataset(n_cells=2000, n_genes=1500, n_cell_types=6, with_clustering=False, random_state=42)` | Generate synthetic `AnnData` with cell type, sample, condition, tissue, and gene metadata | No network |
| `ov.datasets.download_data(url, file_path=None, dir='./data')` | Download a resource to local storage with progress display | Networked |
| `ov.datasets.get_adata(url, filename=None)` | Download and load `.h5ad` or `.loom` into `AnnData` | Networked |
| `ov.datasets.pbmc3k(...)`, `ov.datasets.hematopoiesis(...)`, `ov.datasets.zebrafish(...)`, and similar named loaders | Load tutorial or benchmark datasets | Usually networked/cache-backed |

Use `create_mock_dataset` for smoke tests and examples where downloads are not appropriate. Treat named real dataset loaders as optional network/caching workflows.

## QC APIs

| API | Signature focus | Produces | Notes |
| --- | --- | --- | --- |
| `ov.pp.qc_metrics(adata, mt_startswith='auto', mt_genes=None, ribo_startswith=('RPS', 'RPL'), ribo_genes=None, hb_startswith='^HB[^(P)]', hb_genes=None)` | Compute metrics only | `.obs['nUMIs']`, `.obs['detected_genes']`, `.obs['mito_perc']`, Scanpy QC columns; `.var['mt']`, `.var['ribo']`, `.var['hb']` | Does not filter cells |
| `ov.pl.qc(adata, metrics=None, kind='hist', batch_key=None, tresh=None, bins=50, log='auto', ncols=3, figsize=None, color='#4C72B0', palette=None)` | Plot QC distributions | `matplotlib.figure.Figure` | Raises `ValueError` when no QC metrics exist in `.obs` |
| `ov.pp.qc(adata, mode='seurat', min_cells=3, min_genes=200, nmads=5, batch_key=None, doublets=True, doublets_method='scdblfinder', filter_doublets=True, tresh=None, mt_startswith='auto', ...)` | Filter cells/genes and optionally call doublet detection | Filtered `AnnData`; QC columns in `.obs`; gene flags in `.var` | `tresh` keys are `mito_perc`, `nUMIs`, and `detected_genes`; `mito_perc` is a fraction such as `0.2` |
| `ov.pp.filter_cells(adata, ...)` / `ov.pp.filter_genes(adata, ...)` | Direct low-level filtering | Filtered AnnData or masks depending kwargs | Use for focused filters when full `qc` is too broad |

Default `ov.pp.qc` doublet detection can require optional backends. For robust basic workflows, set `doublets=False` first, then add doublet detection after imports are confirmed.

## Preprocessing APIs

| API | Key parameters | Produces | Required inputs |
| --- | --- | --- | --- |
| `ov.pp.preprocess(adata, mode='shiftlog|pearson', target_sum=500000.0, n_HVGs=2000, organism='human', no_cc=False, batch_key=None, identify_robust=True)` | Normalization method before `|` and HVG method after `|`; common modes include `shiftlog|pearson` and `shiftlog|seurat` | `.layers['counts']`, `.var['highly_variable']`, `.var['highly_variable_features']`, `.uns['status']['preprocess']` | Raw count-like `.X`; optional batch key in `.obs` |
| `ov.pp.normalize_total(adata, target_sum=..., ...)` | Total count normalization | Updates expression matrix/layer depending kwargs | Count-like data |
| `ov.pp.log1p(adata, ...)` | Log transform | Updates expression matrix/layer depending kwargs | Normalized counts |
| `ov.pp.normalize_pearson_residuals(adata, theta=100, clip=None, check_values=True, layer=None, inplace=True, copy=False, **kwargs)` | Analytic Pearson residual normalization | Residualized matrix or in-place update | Count-like data |
| `ov.pp.highly_variable_genes(...)` | HVG selection | `.var['highly_variable']` and statistics | Normalized or count layer depending flavor |
| `ov.pp.scale(adata, max_value=10, layers_add='scaled', to_sparse=False, use_implicit_centering=False, **kwargs)` | Z-score scaling and clipping | `.layers[layers_add]`, usually `.layers['scaled']`; `.var['mean']`, `.var['std']` where applicable | Preprocessed matrix; sparse data may densify unless implicit centering is used |
| `ov.pp.regress(adata, keys=None, layer=None, n_jobs=8, **kwargs)` | Regress technical covariates | `.layers['regressed']` | `.obs` columns such as `mito_perc` and `nUMIs` |
| `ov.pp.regress_and_scale(adata, ...)` | Convenience regression plus scaling | `.layers['regressed_and_scaled']` | `.layers['regressed']` or compatible input |

`ov.pp.preprocess` stores raw counts in `.layers['counts']` before normalization. If it slices to robust genes, it mirrors the result back onto the original object, but users should still assign the return value when possible.

## Dimensionality and Graph APIs

| API | Key parameters | Produces | Prerequisites |
| --- | --- | --- | --- |
| `ov.pp.pca(adata, n_pcs=50, layer='scaled', inplace=True, random_state=<ov seed default>, **kwargs)` | `layer` defaults to `'scaled'` | `.obsm['X_pca']`, `.varm['PCs']`, `.uns['pca']`, alias keys such as `scaled|original|X_pca` | `adata.layers[layer]` or implicit scaled wrapper |
| `ov.pp.neighbors(adata, n_neighbors=15, n_pcs=None, use_rep=None, knn=True, random_state=<ov seed default>, n_jobs=None, method='umap', transformer=None, metric='euclidean', key_added=None, copy=False, **kwargs)` | Build kNN graph; `use_rep='X_pca'` can be explicit | `.uns['neighbors']`, `.obsp['distances']`, `.obsp['connectivities']` or keyed variants | PCA or other representation |
| `ov.pp.umap(adata, min_dist=0.5, spread=1.0, n_components=2, maxiter=None, random_state=<ov seed default>, method=None, key_added=None, neighbors_key='neighbors', copy=False, **kwargs)` | Compute embedding; `method='pumap'` returns fitted parametric model | `.obsm['X_umap']` by default; optional model for parametric UMAP | Neighbor graph |
| `ov.pp.leiden(adata, resolution=1.0, key_added='leiden', neighbors_key=None, random_state=0, ...)` | Community detection | `.obs[key_added]` | Neighbor graph |
| `ov.pp.louvain(adata, resolution=None, key_added='louvain', neighbors_key=None, random_state=0, ...)` | Louvain clustering | `.obs[key_added]` | Neighbor graph |
| `ov.pp.load_pumap(path)` | Load saved parametric UMAP model | Model with `.transform(...)` | Parametric UMAP optional backend |

In CPU/GPU mixed mode, `neighbors` defaults to a PyTorch Geometric transformer when available. GPU and parametric UMAP routes require optional heavy dependencies.

## Plotting APIs

| API | Key parameters | Expected inputs |
| --- | --- | --- |
| `ov.pl.embedding(adata, basis, color=None, layer=None, projection='2d', palette=None, frameon='small', legend_loc='right margin', show=None, save=None, return_fig=None, **kwargs)` | Generic scatter over `.obsm[basis]`; color from `.obs` or genes | Existing embedding such as `X_umap` or `X_pca` |
| `ov.pl.umap(adata, **kwargs)` / `ov.pl.pca(adata, **kwargs)` | Convenience wrappers | `.obsm['X_umap']` or `.obsm['X_pca']` |
| `ov.pl.qc(...)` | QC metrics histograms/violins | QC columns in `.obs` |
| `ov.pl.violin(...)`, `ov.pl.dotplot(...)`, `ov.pl.heatmap(...)` | General expression/annotation plots | Matching `.obs`, `.var_names`, `.raw`, or `layer` |
| `ov.pl.palette`, `ov.pl.ov_plot_set`, `ov.pl.plot_set`, `ov.pl.style` | Color and style helpers | Matplotlib/seaborn environment |

For noninteractive execution, set `matplotlib.use('Agg')` before plotting and use `show=False` plus explicit saving.

## Report APIs

| API | Purpose | Produces |
| --- | --- | --- |
| `ov.report.from_anndata(adata, output='anndata_report.html', title=None)` | Render a self-contained HTML report by scanning pipeline evidence and provenance | `pathlib.Path` to HTML |
| `ov.report.record_step(adata, name, function=..., params=..., backend=..., duration_s=..., viz=...)` | Manually append provenance | `adata.uns['_ov_provenance']` |
| `ov.report.get_provenance(adata)` | Return ordered provenance list | `list[dict]` |
| `ov.report.clear_provenance(adata)` | Remove provenance | Empty provenance list |
| `ov.report.track(...)` | Decorator used by OmicVerse internals | Automatic provenance for tracked functions |

Report generation is best after core slots are populated. It can still produce heuristic sections if provenance is absent but embeddings, neighbors, or clustering slots exist.

## Utility APIs Useful in Core Work

| API | Purpose |
| --- | --- |
| `ov.utils.preflight_alignment(matrix, meta, sample_col=None, sep=None, matrix_sample_axis='columns')` | Detect duplicate and mismatched sample IDs before joint analyses |
| `ov.utils.align_to_common(matrix, meta, result)` | Drop duplicates/missing samples and return aligned objects |
| `ov.utils.align_samples(matrix, meta, ...)` | One-shot preflight plus alignment |
| `ov.utils.convert_adata_for_rust(adata, output_file=...)` | Prepare sparse h5ad data for Rust-backed out-of-memory reading |
| `ov.utils.store_layers(adata, ...)` / `ov.utils.retrieve_layers(adata, ...)` | Layer management helpers |
| `ov.utils.patch_rust_adata(...)` | Rust AnnData compatibility helper |

Use these utilities to make input assumptions explicit before handing data to domain-specific sub-skills.
