# Core Workflows

This reference gives self-contained OmicVerse patterns for basic `AnnData` work without relying on external repository docs.

## Minimal Import and Introspection

```python
import omicverse as ov

print(ov.__version__)
ov.set_seed(0)
ov.list_functions("preprocessing")
ov.get_function_help("qc")
```

Use registry helpers when a task description is vague:

```python
matches = ov.recommend_function("quality control then UMAP")
first = ov.find_function("read 10x")
```

`ov.list_functions(...)` and `ov.get_function_help(...)` print human-readable output. `ov.export_registry(format="dict")` returns structured metadata including signatures and categories.

## Read, QC, Preprocess, Embed

Use this workflow for a 10x Matrix Market directory or an already loaded `AnnData`.

```python
import omicverse as ov

ov.set_seed(0)
adata = ov.io.read_10x_mtx(
    "filtered_feature_bc_matrix",
    var_names="gene_symbols",
    make_unique=True,
    gex_only=True,
)
adata.var_names_make_unique()

# Inspect before filtering.
ov.pp.qc_metrics(adata)
qc_fig = ov.pl.qc(
    adata,
    tresh={"mito_perc": 0.2, "nUMIs": 500, "detected_genes": 250},
    kind="hist",
)
qc_fig.savefig("qc_thresholds.png", dpi=150, bbox_inches="tight")

# Apply filters after selecting thresholds.
adata = ov.pp.qc(
    adata,
    mode="seurat",
    tresh={"mito_perc": 0.2, "nUMIs": 500, "detected_genes": 250},
    doublets=False,
)

# Normalize/HVG and preserve raw counts.
ov.pp.preprocess(
    adata,
    mode="shiftlog|pearson",
    target_sum=1e4,
    n_HVGs=2000,
    batch_key=None,
    no_cc=False,
)
ov.pp.scale(adata, max_value=10)
ov.pp.pca(adata, n_pcs=50)
ov.pp.neighbors(adata, n_neighbors=15, n_pcs=50, method="umap")
ov.pp.umap(adata, min_dist=0.5)

emb = ov.pl.embedding(adata, basis="X_umap", color=["nUMIs", "mito_perc"], show=False)
ov.report.from_anndata(adata, output="core_report.html", title="Core workflow")
adata.write_h5ad("processed.h5ad", compression="gzip")
```

### Validation Checkpoints

Check these after each phase:

| Phase | Expected signal | If missing |
| --- | --- | --- |
| Load | `adata.n_obs > 0`, `adata.n_vars > 0`, unique `.obs_names` and `.var_names` | Re-check file layout, `var_names`, compression, or h5ad path |
| QC metrics | `nUMIs`, `detected_genes`, `mito_perc` in `adata.obs`; `mt`, `ribo`, `hb` in `adata.var` | Run `ov.pp.qc_metrics(adata)` before `ov.pl.qc` |
| QC filter | filtered `adata.n_obs`; metrics retained in `.obs` | Relax `tresh`, set `doublets=False`, or inspect by `batch_key` |
| Preprocess | `layers['counts']`, `var['highly_variable']`, `var['highly_variable_features']` | Confirm raw count-like input and valid `mode`, such as `shiftlog|pearson` |
| Scale | `layers['scaled']`, `uns['status']['scaled']` | Run `ov.pp.scale(adata)` before PCA |
| PCA | `obsm['X_pca']`, `varm['PCs']`, `uns['pca']` | Confirm `layers['scaled']` exists or pass an existing `layer` |
| Neighbors | `uns['neighbors']`, `obsp['distances']`, `obsp['connectivities']` | Run PCA or set `use_rep` to an existing embedding |
| UMAP | `obsm['X_umap']` | Run neighbors first; check backend optional dependencies |
| Report | HTML file path returned; provenance in `uns['_ov_provenance']` when tracked calls ran | Use `ov.report.get_provenance(adata)` and inspect available slots |

## H5AD Load and Out-of-Memory Option

For ordinary `.h5ad`:

```python
adata = ov.read("sample.h5ad")
# equivalent: adata = ov.io.read_h5ad("sample.h5ad")
```

For large `.h5ad` files where `anndataoom` is installed:

```python
adata = ov.read("large.h5ad", backend="rust")
# Process with supported chunked `ov.pp.*` paths, then close/materialize as needed.
```

If the Rust backend rejects an unsorted sparse matrix, rewrite a sorted copy with normal Python `AnnData` or use `ov.utils.convert_adata_for_rust(...)`.

## Synthetic No-Network Smoke

Use synthetic data when you need a quick check that OmicVerse imports and plotting work:

```python
import matplotlib
matplotlib.use("Agg")
import omicverse as ov

adata = ov.datasets.create_mock_dataset(
    n_cells=100,
    n_genes=200,
    n_cell_types=4,
    with_clustering=True,
    random_state=0,
)
assert "X_umap" in adata.obsm
fig = ov.pl.embedding(adata, basis="X_umap", color="cell_type", show=False, return_fig=True)
fig.savefig("mock_umap.png", dpi=120, bbox_inches="tight")
```

`create_mock_dataset(..., with_clustering=True)` performs lightweight synthetic preprocessing without dataset downloads. It is useful for smoke tests, not biological conclusions.

## Plotting Patterns

Embedding plots use a basis name from `.obsm`. OmicVerse accepts either names such as `"umap"` through convenience wrappers or explicit basis keys such as `"X_umap"` through `ov.pl.embedding`.

```python
ov.pl.embedding(adata, basis="X_umap", color="leiden", frameon="small", show=False)
ov.pl.embedding(adata, basis="X_pca", color=["sample", "nUMIs"], ncols=2, show=False)
```

For headless scripts, set a noninteractive backend before importing pyplot:

```python
import matplotlib
matplotlib.use("Agg")
```

Use `save=` or returned figures/axes depending on the specific plotting function. For workflow-safe scripts, prefer `show=False` and explicit `fig.savefig(...)`.

## Reports and Provenance

OmicVerse report helpers scan `AnnData` for standard pipeline evidence and use tracked provenance when available.

```python
from pathlib import Path
import omicverse as ov

path = ov.report.from_anndata(adata, output="report.html", title="Analysis report")
assert Path(path).exists()
for step in ov.report.get_provenance(adata):
    print(step["name"], step.get("function"), step.get("params"))
```

Tracked core calls include provenance such as step name, function, user parameters, backend, duration, and selected visualization hints. Provenance is best-effort and should supplement, not replace, explicit notebook or script records.

## Reproducibility Pattern

Put `ov.set_seed(...)` at the top of notebooks and scripts:

```python
import omicverse as ov
seed = ov.set_seed(42, deterministic=False, verbose=True)
```

This seeds Python `random`, NumPy, PyTorch/CUDA when present, MLX when present, and records the value in `ov.settings.seed`. Core `ov.pp` functions with default random-state sentinels resolve to that global seed unless the call passes an explicit `random_state`.

Use `deterministic=True` only when bit-level reproducibility matters more than GPU speed.

## Parametric UMAP Projection

Use `method="pumap"` only for atlas/reference projection workflows where future data must land in the same embedding.

```python
model = ov.pp.umap(ref, method="pumap")
model.save("reference_pumap.pkl")
model = ov.pp.load_pumap("reference_pumap.pkl")
query.obsm["X_umap"] = model.transform(query_pca.astype("float32"))
```

The query must be transformed into exactly the same representation used for training: same features, same order, same scaling, and the reference PCA transform. Parametric UMAP requires heavier GPU/torch dependencies; default `ov.pp.umap(adata)` is better for one-off embeddings.

## Metadata Alignment Before Joint Analysis

For sample-by-metadata mismatches, use the generic alignment helpers before downstream statistics or plotting:

```python
result = ov.utils.preflight_alignment("counts.csv", "metadata.csv", sample_col="sample_id")
print(result)
if result.needs_alignment:
    matrix, metadata = ov.utils.align_to_common("counts.csv", "metadata.csv", result)
```

This detects duplicate sample labels that pandas would otherwise silently rename and reports samples missing from either side.
