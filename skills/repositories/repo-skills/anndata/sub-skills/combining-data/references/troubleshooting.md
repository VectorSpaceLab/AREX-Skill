# Combining Data Troubleshooting

Use this table when concat output shape, metadata, pairwise arrays, indexes, or memory behavior differs from expectations.

| Symptom | Likely Cause | Recovery / Validation |
| --- | --- | --- |
| Genes or cells disappeared after concat. | `join="inner"` kept only labels shared by all inputs on the non-concatenated axis. | Use `join="outer"` if a union is intended; print `combined.obs_names` or `combined.var_names` and compare against input unions. |
| Outer join introduced unexpected zeros. | Sparse `.X` or sparse layers fill absent entries with zero by default when `fill_value=None`. | Decide whether zeros are biologically/statistically meaningful; if not, use `join="inner"`, choose an explicit `fill_value`, or handle missingness before downstream analysis. |
| Dense matrices or annotations contain missing values after outer join. | Dense arrays and DataFrames use missing values for introduced labels when `fill_value=None`. | Pass an explicit sentinel where appropriate and check dense/dataframe missing counts before analysis. |
| `.uns` is empty. | `uns_merge=None` is the default. | Use `uns_merge="same"` for shared metadata, `"unique"` for non-conflicting metadata, or `"first"` only with a documented first-input-wins policy. |
| Nested `.uns` keys are partly retained and partly missing. | `uns_merge` applies recursively; conflicting nested values are dropped by `"same"` or `"unique"`. | Inspect the conflicting nested keys before concat and decide whether to drop, keep first, or recompute the analysis state. |
| `.varm`, `.obsm`, `.layers`, `.varp`, or `.obsp` entries are missing. | `merge=None` drops metadata not directly concatenated; `pairwise=False` drops pairwise mappings on the concatenated axis. | Choose `merge="same"`, `"unique"`, `"first"`, or `"only"` for alternative-axis elements; set `pairwise=True` only for meaningful block-diagonal pairwise arrays. |
| Observation or variable names are duplicated. | Inputs shared names and `index_unique=None` preserved them. | Pass a mapping or `keys`, set `index_unique="-"`, and assert `combined.obs_names.is_unique` or `combined.var_names.is_unique`. |
| `TypeError` says categories were specified in mapping keys and `keys`. | Mapping keys already provide the keys used for labels and index suffixes. | Use either `ad.concat({"a": a, "b": b}, label="batch")` or `ad.concat([a, b], keys=["a", "b"], label="batch")`, not both. |
| No batch/source label column appears. | `label=None` by default. | Pass `label="batch"`, `"dataset"`, or another column name and validate category counts on `.obs` for `axis="obs"` or `.var` for `axis="var"`. |
| Pairwise graphs in `.obsp` disappeared. | `pairwise=False` is the default for `axis="obs"`. | If block-diagonal zero-padded graphs are intended, use `pairwise=True`; otherwise recompute graphs after concat. |
| Pairwise concat on files raises `NotImplementedError`. | `experimental.concat_on_disk(..., pairwise=True)` is not implemented. | Run on-disk concat with `pairwise=False`, then recompute pairwise arrays on the combined object, or use in-memory `anndata.concat(..., pairwise=True)` if feasible. |
| `concat_on_disk` raises that there are no objects. | Input collection is empty after discovery/filtering. | Fail before calling and report the discovery criteria; pass at least one file/store. |
| `concat_on_disk` cannot create the output. | The parent directory of a path-like output does not exist. | Create the parent directory first and decide overwrite behavior explicitly. |
| `concat_on_disk` uses too much memory. | `max_loaded_elems` is too high for sparse arrays, or dense arrays rely on dask chunking. | Lower `max_loaded_elems`, prefer compatible sparse stores where possible, and use storage guidance for chunked Zarr/H5AD workflows. |
| `AnnCollection` raises that variables differ. | `AnnCollection` assumes identical `var_names` unless `join_vars="inner"` is specified. | Pass `join_vars="inner"` for the variable intersection, or align/filter variables before constructing the collection. |
| `AnnCollection` warns observation names are not unique. | Inputs share `.obs_names` and `index_unique=None`. | Provide mapping keys or `keys` and set `index_unique="-"`. |
| `AnnCollection.to_adata()` lacks a materialized `.X`. | `AnnCollection` is lazy; `to_adata()` materializes annotations/shape but not the full matrix. | Use subset views for `.X`, or use `anndata.concat` when a complete in-memory `AnnData.X` is required. |
| Lazy concat still reads or materializes more than expected. | `force_lazy=True` only affects supported `.obs`/`.var` and xarray Dataset elements in `.obsm`/`.varm`. | For many large files prefer `concat_on_disk`; for lazy observation-axis access prefer `AnnCollection`; validate memory with a small subset first. |
| A workflow asks for `AnnLoader`. | `AnnLoader` requires optional PyTorch and is deprecated in favor of `annbatch.Loader`. | Prefer `AnnCollection` for the combined dataset and `annbatch.Loader` for new loader-style training code. |

## Minimal Debug Sequence

```python
print("shape", combined.shape)
print("obs unique", combined.obs_names.is_unique)
print("var unique", combined.var_names.is_unique)
print("obs columns", list(combined.obs.columns))
print("var columns", list(combined.var.columns))
print("uns keys", sorted(combined.uns.keys()))
print("obsp keys", sorted(combined.obsp.keys()))
print("varp keys", sorted(combined.varp.keys()))
```

For outer joins, also check introduced labels and missing/fill behavior on the non-concatenated axis before saving the result or running downstream analysis.
