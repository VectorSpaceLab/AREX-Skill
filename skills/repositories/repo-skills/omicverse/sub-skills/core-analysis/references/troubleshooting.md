# Core Troubleshooting

Use this guide for OmicVerse core import, IO, preprocessing, plotting, report, and registry issues.

## Quick Diagnostic Commands

```bash
python -c "import omicverse as ov; print(ov.__version__); print(ov.set_seed(0, verbose=False))"
python sub-skills/core-analysis/scripts/inspect_core.py --json
python sub-skills/core-analysis/scripts/inspect_core.py --smoke-mock --mock-cells 40 --mock-genes 80
```

Inside Python:

```python
import omicverse as ov
ov.load_package(omicverse_modules=["io", "datasets", "pp", "pl", "report"], show_summary=True)
ov.get_function_help("qc")
```

## Lazy Import or Optional Dependency Errors

| Signal | Likely cause | Recovery |
| --- | --- | --- |
| `AttributeError: Failed to import omicverse.pp: ... A required dependency may not be installed.` | Root lazy import caught a transitive import failure | Import the exact module directly, e.g. `import omicverse.pp`, to see the full traceback; install or remove the mismatched optional dependency |
| `ImportError` mentioning `anndataoom` | Requested `ov.read(..., backend='rust')` or implicit centering without Rust/OOM package | Use `backend='python'`, install the optional OOM dependency, or avoid `use_implicit_centering=True` |
| GPU/RAPIDS/Torch errors during neighbors or UMAP | `ov.settings.mode` or explicit method selected a heavy backend | Run CPU mode or use default CPU calls first; avoid `method='pumap'` unless torch/GPU requirements are satisfied |
| Optional doublet backend missing during `ov.pp.qc` | `doublets=True` defaults to a backend that may not be installed | Start with `doublets=False`; add `doublets_method='scrublet'` or install the desired backend later |
| Plot imports fail on server | Matplotlib backend cannot open display | Set `import matplotlib; matplotlib.use('Agg')` before plotting |

When debugging lazy imports, avoid repeatedly touching `ov.<module>` through root access. Directly import the submodule and capture the first traceback.

## IO Failures

| Signal | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: The type is not supported.` from `ov.read` | File suffix is not `.h5ad`, `.csv`, `.tsv`, `.txt`, or supported gzipped text | Use a format-specific reader or convert the file |
| `backend must be 'python' or 'rust'` | Invalid `.h5ad` backend | Use `backend='python'` unless intentionally using OOM Rust reading |
| Rust backend rejects unsorted sparse `X` | Sparse h5ad indices are not sorted | Read with Python, sort indices, rewrite h5ad, or use `ov.utils.convert_adata_for_rust(...)` |
| `read_10x_mtx` cannot find files | Directory layout, compression, or prefix mismatch | Check for `matrix.mtx(.gz)`, `features.tsv(.gz)` or `genes.tsv`, and `barcodes.tsv(.gz)`; set `compressed=False` or `prefix=...` |
| `read_10x_h5` says missing datasets | Not a Cell Ranger matrix HDF5 | Inspect file source; use a different HDF5 reader or convert to h5ad |
| Duplicate sample labels warning from `ov.io.read_csv` | Raw table header has repeated column names; pandas would auto-rename | Run `ov.utils.preflight_alignment` and `align_to_common`; use `on_duplicate='raise'` in strict pipelines |

## AnnData Shape and Slot Issues

| Signal | Likely cause | Recovery |
| --- | --- | --- |
| Empty `n_obs` or `n_vars` after loading | Wrong feature filter or file path | Re-read with `gex_only=False`, adjust `var_names`, or inspect input layout |
| Duplicate gene names break plotting or HVG | Repeated symbols from 10x or merged datasets | Run `adata.var_names_make_unique()` before preprocessing |
| Gene color not found in `ov.pl.embedding` | Gene is absent from `.var_names` or stored in a different `gene_symbols` column | Use exact `.var_names`, pass `gene_symbols=...`, or align features |
| Metadata column not found | `adata.obs` lacks requested key | Print `list(adata.obs.columns)`; merge metadata before plotting |
| Layer missing for PCA | `ov.pp.pca` defaults to `layer='scaled'` | Run `ov.pp.scale(adata)` or pass `layer=` pointing to an existing layer |
| Neighbor graph missing for UMAP/clustering | `ov.pp.neighbors` has not run | Run `ov.pp.pca` then `ov.pp.neighbors`, or set `use_rep` to an existing embedding |

## Workflow Order Problems

Recommended order:

```text
read -> var_names_make_unique -> qc_metrics -> pl.qc -> qc/filter -> preprocess -> scale -> pca -> neighbors -> umap -> plot/report
```

Common order errors:

| Error/symptom | Fix |
| --- | --- |
| `ov.pl.qc` raises `No QC metrics found in adata.obs` | Run `ov.pp.qc_metrics(adata)` or `ov.pp.qc(adata)` first |
| `ov.pp.pca` raises `Selected layer scaled is not present` | Run `ov.pp.scale(adata)` first or call `ov.pp.pca(adata, layer='existing_layer')` |
| UMAP complains about missing neighbors | Run `ov.pp.neighbors(adata, n_neighbors=15, n_pcs=50)` first |
| Clustering labels absent from `.obs` | Run `ov.pp.leiden` or `ov.pp.louvain` after neighbors |
| Report is sparse or missing sections | Ensure core slots exist and tracked calls ran; inspect `ov.report.get_provenance(adata)` |

## QC Threshold Issues

`ov.pp.qc` uses `tresh`, not `thresh`. The typical keys are:

```python
tresh = {"mito_perc": 0.2, "nUMIs": 500, "detected_genes": 250}
```

`mito_perc` is a fraction, so `0.2` means 20%. Scanpy-compatible `pct_counts_mt` is a percent-scale column, so `20` means 20% there.

If `ov.pp.qc` removes too many cells:

1. Re-run from the unfiltered object.
2. Use `ov.pp.qc_metrics(adata)` and `ov.pl.qc(adata, batch_key='sample')` to inspect distributions.
3. Lower minimum `nUMIs`/`detected_genes` or increase allowed `mito_perc`.
4. Set `doublets=False` until threshold behavior is understood.
5. Check whether sample/batch-specific thresholds are needed.

If mitochondrial genes are not detected:

- Use `mt_startswith='MT-'` for common human symbols.
- Use `mt_startswith='mt-'` for common mouse symbols.
- Pass `mt_genes=[...]` when symbols use a custom naming convention.

## Preprocess and HVG Issues

| Signal | Likely cause | Recovery |
| --- | --- | --- |
| HVG column missing | Unsupported mode/backend combination or failed HVG method | Use `mode='shiftlog|pearson'` or `mode='shiftlog|seurat'`; inspect exceptions before continuing |
| `NotImplementedError` for OOM plus Seurat HVG | Out-of-memory backend does not support Seurat v3 HVG | Use `shiftlog|pearson` or materialize with CPU mode |
| `no_cc=True` fails in OOM mode | Cell-cycle removal materializes large slices | Run without `no_cc` or switch to CPU mode for smaller data |
| Values look already log-normalized | Raw counts were overwritten before preprocessing | Restore from `.layers['counts']`, `.raw`, or original file; preserve counts before transformations |
| Batch-aware HVG behaves unexpectedly | `batch_key` missing or has too few cells per batch | Confirm `batch_key in adata.obs` and inspect batch sizes |

## Plotting Backend and Figure Issues

| Signal | Recovery |
| --- | --- |
| `cannot connect to display` or GUI backend error | Set `matplotlib.use('Agg')` before importing pyplot or OmicVerse plotting modules in scripts |
| Plot appears blank in saved output | Use `show=False`, capture returned figure/axes where supported, then call `savefig(..., bbox_inches='tight')` |
| Legend/category colors inconsistent | Convert categories to categorical dtype and set/recompute palettes before plotting |
| Gene expression color is all missing | Verify gene names, `use_raw`, `layer`, and whether the gene survived HVG subsetting |
| Very large plots are slow or huge | Downsample for exploratory plots or use smaller marker `size` and rasterized output where supported |

## Dataset Download and Network Issues

Named dataset loaders may download large files. For offline or deterministic checks:

- Use local `.h5ad` or 10x fixture paths.
- Use `ov.datasets.create_mock_dataset(...)` for API smoke tests.
- Avoid using named real dataset loaders in CI unless network/cache policy allows it.

If a dataset load fails after interruption, remove the partial cache file and retry only if downloads are allowed.

## Deprecated AnnData Warnings

Warnings from AnnData, pandas, or Scanpy often reflect upstream API changes rather than immediate failure. Handle them as follows:

| Warning type | Response |
| --- | --- |
| Future/deprecation warning during read/write | Confirm output round-trips with `read_h5ad`; update code when convenient |
| View mutation warning | Call `.copy()` after subsetting before assigning layers or metadata |
| Categorical assignment warning | Convert categories explicitly or add categories before assignment |
| Sparse efficiency warning | Convert to CSR/CSC as appropriate for repeated slicing |

Do not silence warnings globally until the workflow has passed validation.

## Registry Discovery Problems

| Signal | Recovery |
| --- | --- |
| `ov.list_functions()` returns fewer entries than expected | Import relevant modules first or use `ov.export_registry(format='dict')`, which hydrates for export |
| `ov.recommend_function(...)` gives a surprising match | Check `ov.get_function_help(...)` and module-specific references before using it |
| Function appears registered but import fails | Registry metadata can hydrate modules; optional dependencies may still fail at call time |

## Report Issues

| Signal | Recovery |
| --- | --- |
| Report file is not created | Confirm parent directory is writable; `ov.report.from_anndata` creates parents but cannot override permissions |
| Report lacks QC or UMAP sections | Ensure corresponding `.obs`, `.var`, `.obsm`, `.obsp`, and `.uns` slots exist |
| Provenance missing | Only tracked OmicVerse functions automatically record provenance; manual Scanpy calls will be detected heuristically or require `ov.report.record_step` |
| H5AD round-trip loses custom objects | Keep `.uns` values JSON-like where possible; complex objects can fail AnnData serialization |

## Minimal Recovery Checklist

When a core workflow fails midstream:

1. Confirm import and version with `inspect_core.py --json`.
2. Print `adata.shape`, first `.obs`/`.var` columns, and available `.layers`, `.obsm`, `.obsp`, `.uns` keys.
3. Validate workflow order against the recommended sequence.
4. Disable optional-heavy paths first: `doublets=False`, CPU/default UMAP, no named dataset downloads.
5. Re-run from a saved raw-count h5ad or from the original input; do not continue from a half-mutated object unless you understand which slots changed.
