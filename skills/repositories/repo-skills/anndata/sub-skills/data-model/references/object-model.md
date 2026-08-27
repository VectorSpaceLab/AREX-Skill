# AnnData Object Model

`AnnData` stores one annotated matrix with observations on rows and variables on columns. Most validation follows from the shape `(n_obs, n_vars)`.

## Mental Model

```text
                 variables axis: var / var_names / varm / varp
             gene-0     gene-1     gene-2
obs cell-0   X[0,0]     X[0,1]     X[0,2]      obs row 0, obsm row 0
axis cell-1   X[1,0]     X[1,1]     X[1,2]      obs row 1, obsm row 1

layers[key]  has the same 2D shape as X
obsp[key]    is observation-by-observation, shape (n_obs, n_obs)
varp[key]    is variable-by-variable, shape (n_vars, n_vars)
uns          is not axis-aligned
raw          is an optional snapshot of X/var/varm
```

The first axis is observations (`obs`), and the second axis is variables (`var`). Keep that ordering consistent when constructing, slicing, or validating objects.

## Slot Contracts

| Slot | Required shape or index contract | Use for |
| --- | --- | --- |
| `X` | 2D, shape `(n_obs, n_vars)` | Primary data matrix. |
| `obs` | DataFrame-like, length `n_obs`; index is `obs_names` | Per-observation annotations such as sample, batch, QC metrics. |
| `var` | DataFrame-like, length `n_vars`; index is `var_names` | Per-variable annotations such as gene symbol or feature type. |
| `layers[key]` | 2D, shape `(n_obs, n_vars)` | Alternative matrices such as counts, normalized values, imputed values. |
| `obsm[key]` | First dimension `n_obs`; DataFrame index must equal `obs_names` | Observation embeddings or multidimensional observation annotations. |
| `varm[key]` | First dimension `n_vars`; DataFrame index must equal `var_names` | Variable loadings or multidimensional variable annotations. |
| `obsp[key]` | 2D, shape `(n_obs, n_obs)` | Observation-pairwise graphs, distances, connectivities. |
| `varp[key]` | 2D, shape `(n_vars, n_vars)` | Variable-pairwise graphs or correlations. |
| `uns[key]` | No alignment enforced | Unstructured metadata, parameters, palettes, nested dictionaries. |
| `raw` | Same `n_obs`; independent `raw.n_vars` and `raw.var_names` | Snapshot of `X`, `var`, and `varm` before variable filtering or normalization. |

AnnData validates aligned containers when they are assigned. One-dimensional NumPy-like values in aligned multidimensional mappings are reshaped to column vectors when appropriate. DataFrames in `obsm` and `varm` must have simple columns and matching axis indexes.

## Index And Name Rules

- `obs_names` is `adata.obs.index`; `var_names` is `adata.var.index`.
- Constructor inputs with integer-like indexes are commonly transformed to strings, which can emit `ImplicitModificationWarning`.
- Non-unique names are allowed but warned about when `anndata.settings.check_uniqueness` is true. Repair with `adata.obs_names_make_unique()` or `adata.var_names_make_unique()`.
- Duplicate names make label-based slicing and joins ambiguous; fix before concatenation, vector lookup, or exporting.
- DataFrames with MultiIndex columns are rejected for constructor-facing tabular inputs and for DataFrame values in `obsm`/`varm`.

## Construction Checklist

Before calling `ad.AnnData(...)`, check:

```python
assert X.ndim == 2
assert len(obs) == X.shape[0]
assert len(var) == X.shape[1]
for key, value in layers.items():
    assert value.shape == X.shape, key
for key, value in obsm.items():
    assert value.shape[0] == X.shape[0], key
for key, value in varm.items():
    assert value.shape[0] == X.shape[1], key
for key, value in obsp.items():
    assert value.shape == (X.shape[0], X.shape[0]), key
for key, value in varp.items():
    assert value.shape == (X.shape[1], X.shape[1]), key
```

For DataFrame `X`, either let AnnData derive `obs` and `var`, or ensure explicit `obs.index` equals `X.index` and explicit `var.index` equals `X.columns`.

## Slicing And Views

Normal slicing uses two dimensions:

```python
view = adata[adata.obs["batch"] == "a", ["gene-0", "gene-1"]]
```

Slicing returns a view when possible. View behavior:

- `view.is_view` is `True` until the view is actualized.
- `view.obs`, `view.var`, `view.layers`, `view.obsm`, `view.varm`, `view.obsp`, `view.varp`, and `view.X` present sliced views of the parent data.
- Mutating a view triggers `ImplicitModificationWarning` and initializes the view as an independent actual object.
- Use `adata[...].copy()` before intended edits to make that transition explicit and avoid warning-driven surprises.
- Slicing with one dimension like `adata[cells, ]` is invalid; use `adata[cells, :]`.

Safe mutation pattern:

```python
subset = adata[adata.obs["batch"] == "a", :].copy()
subset.obs["selected"] = True
subset.layers["scaled"] = subset.X.copy()
```

When a task asks whether editing a slice changes the parent, answer: normal AnnData views use copy-on-modify, so the edit actualizes the view rather than intentionally mutating the parent. If parent mutation is desired, assign through the parent object directly with explicit indexers.

## `.raw` Semantics

`.raw` stores a snapshot of `X`, `var`, and `varm`.

Common pattern:

```python
adata.raw = adata.copy()
```

Important behavior:

- `adata.raw` is optional and may be `None`.
- `adata.raw.X` and `adata.raw.var` are read through a `Raw` object rather than regular `adata.X` and `adata.var`.
- `.raw` follows observation slicing: `adata[obs_mask, :].raw.n_obs` matches the sliced observations.
- `.raw` ignores normal variable-axis slicing of the parent, so a filtered object can keep access to genes that were removed from `adata.var_names`.
- Access a removed original variable with `adata.raw[:, "original_gene"].X` when it exists in `raw.var_names`.
- Delete or clear with `del adata.raw` or `adata.raw = None`.
- Assigning `.raw` requires an AnnData object; assigning a raw object whose number of observations does not match raises.

Use `.raw` for stable reference data, not for arbitrary extra matrices. Use `layers` for aligned alternative matrices with the current variable axis.

## `to_df`, Layers, And Dense Conversion

`adata.to_df()` converts `X` to a pandas DataFrame with `obs_names` and `var_names`. `adata.to_df(layer="counts")` uses that layer instead. Sparse matrices are densified, so check size before converting large objects. The DataFrame does not carry `obs`, `var`, `obsm`, `uns`, or `.raw` annotations.

## Copy And Memory Boundaries

- Use `.copy()` for an independent in-memory object.
- Use `.copy(filename=...)` only when intentionally creating an on-disk copy; route details to `../storage-io/SKILL.md`.
- For backed or lazy objects that should become normal in-memory objects, use `.to_memory(copy=False)` or `.to_memory(copy=True)`. `copy=True` is safer when later mutation must not share existing in-memory buffers.
- If `.copy()` fails because the object contains backed raw HDF5/Zarr arrays or is in backed mode without a filename, route the storage lifecycle to `../storage-io/SKILL.md` and use `.to_memory()` or a storage-aware copy.

## Mutation Patterns

Preferred mutations on actual objects:

```python
adata.obs["batch"] = adata.obs["batch"].astype("category")
adata.var["highly_variable"] = False
adata.layers["counts"] = counts_matrix
adata.obsm["X_pca"] = pca_scores
adata.varm["PCs"] = pca_loadings
adata.obsp["connectivities"] = graph_matrix
adata.uns["method"] = {"name": "demo", "version": 1}
```

After mutation, validate:

```python
assert not adata.is_view
assert adata.layers["counts"].shape == adata.shape
assert adata.obsm["X_pca"].shape[0] == adata.n_obs
assert adata.varm["PCs"].shape[0] == adata.n_vars
```

## Boundary Reminders

- File persistence, backed mode, lazy storage, compression, and H5AD/Zarr format rules belong in `../storage-io/SKILL.md`.
- Multi-object concatenation, batch labels, `join`, `merge`, `uns_merge`, `AnnCollection`, and `concat_on_disk` belong in `../combining-data/SKILL.md`.
- Reference accessors and extension namespaces belong in `../accessors-extensions/SKILL.md`.
