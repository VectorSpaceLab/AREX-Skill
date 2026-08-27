# Data Model API Reference

This reference covers stable public APIs for constructing and inspecting one `anndata.AnnData` object in memory. Use public imports such as `import anndata as ad`; avoid internal modules in runtime code.

## Core Constructor

Verified constructor shape:

```python
ad.AnnData(
    X=None,
    obs=None,
    var=None,
    uns=None,
    *,
    obsm=None,
    varm=None,
    layers=None,
    raw=None,
    shape=None,
    filename=None,
    filemode=None,
    asview=False,
    obsp=None,
    varp=None,
    oidx=None,
    vidx=None,
)
```

Use the constructor for in-memory objects as follows:

- `X`: primary 2D matrix. Common inputs are NumPy arrays, SciPy sparse matrices/arrays, masked arrays, pandas DataFrames, dask/cupy-style arrays supported by AnnData, or `None` with `shape=(n_obs, n_vars)`.
- `obs`: observation annotations. Accepts a pandas DataFrame or mapping and must have exactly `n_obs` rows.
- `var`: variable annotations. Accepts a pandas DataFrame or mapping and must have exactly `n_vars` rows.
- `uns`: unstructured metadata mapping. Use for dictionaries, scalars, colors, parameters, or other data not aligned to an axis.
- `obsm`: observation-aligned multidimensional arrays or DataFrames, each with first dimension `n_obs`.
- `varm`: variable-aligned multidimensional arrays or DataFrames, each with first dimension `n_vars`.
- `layers`: additional 2D matrices, each with shape `(n_obs, n_vars)`.
- `obsp`: observation-pairwise matrices, each with shape `(n_obs, n_obs)`.
- `varp`: variable-pairwise matrices, each with shape `(n_vars, n_vars)`.
- `raw`: mapping or `Raw`-like value used to initialize `.raw`; most user code should set `adata.raw = adata.copy()` after construction instead.
- `shape`: use only when `X is None`; it fixes `(n_obs, n_vars)` for an empty object.
- `filename` and `filemode`: storage/backed-mode concerns; route substantial use to `../storage-io/SKILL.md`.
- `asview`, `oidx`, and `vidx`: internal view construction controls; normal user code should slice with `adata[obs_indexer, var_indexer]` instead.

## Construction Patterns

### From Arrays And Mappings

```python
import anndata as ad
import numpy as np
import pandas as pd

X = np.array([[1.0, 0.0, 2.0], [0.0, 3.0, 4.0]])
obs = pd.DataFrame({"batch": ["a", "b"]}, index=["cell-0", "cell-1"])
var = pd.DataFrame({"symbol": ["g0", "g1", "g2"]}, index=["gene-0", "gene-1", "gene-2"])
adata = ad.AnnData(X=X, obs=obs, var=var)
adata.layers["counts"] = X.astype("int64")
adata.obsm["pca"] = np.array([[0.1, 0.2], [0.3, 0.4]])
adata.obsp["distances"] = np.eye(adata.n_obs)
```

Check lengths before construction when data come from different sources:

```python
assert X.shape == (len(obs), len(var))
```

### From A DataFrame `X`

When `X` is a pandas DataFrame, its index becomes `obs_names` and its columns become `var_names` unless explicit `obs` or `var` are supplied. If explicit annotations are supplied, their indexes must match the DataFrame index/columns.

```python
frame = pd.DataFrame([[1, 2], [3, 4]], index=["cell-a", "cell-b"], columns=["gene-a", "gene-b"])
adata = ad.AnnData(frame)
assert list(adata.obs_names) == ["cell-a", "cell-b"]
assert list(adata.var_names) == ["gene-a", "gene-b"]
```

AnnData rejects pandas DataFrames with MultiIndex columns for `X`, `obs`, `var`, and DataFrame values stored in `obsm`/`varm`.

### Empty Matrix With Known Shape

Use `shape=(n_obs, n_vars)` only when `X` is absent:

```python
adata = ad.AnnData(X=None, shape=(100, 200))
assert adata.X is None
assert adata.shape == (100, 200)
```

If `X` is provided, do not also pass `shape`.

## Key Properties

- `adata.shape`: tuple `(n_obs, n_vars)`.
- `adata.n_obs`, `adata.n_vars`: axis lengths.
- `adata.obs`, `adata.var`: pandas DataFrames for axis annotations.
- `adata.obs_names`, `adata.var_names`: indexes from `obs` and `var`; assignable, and often stringified during construction.
- `adata.layers`, `adata.obsm`, `adata.varm`, `adata.obsp`, `adata.varp`: validated mapping-like containers.
- `adata.uns`: mutable mapping for unstructured metadata.
- `adata.raw`: optional `Raw` snapshot containing `.raw.X`, `.raw.var`, `.raw.varm`, `.raw.obs_names`, and `.raw.var_names`.
- `adata.is_view`: `True` for sliced views until actualized.
- `adata.isbacked`, `adata.filename`, `adata.file`: storage state. Use this sub-skill to notice backed state; route backing lifecycle and persistence to `../storage-io/SKILL.md`.

## Common Methods

### `adata.copy(filename=None)`

Verified signature:

```python
adata.copy(filename=None)
```

Creates a full copy of an in-memory object. If the object is backed, `copy()` without a filename raises and storage handling should route to `../storage-io/SKILL.md`. For normal in-memory independence, use:

```python
subset = adata[adata.obs["batch"] == "a", :].copy()
```

### `adata.to_memory(copy=False)`

Verified signature:

```python
adata.to_memory(copy=False)
```

Returns a new `AnnData` with non-in-memory arrays loaded into memory. `copy=False` may share arrays that are already in memory; use `copy=True` when the result must not share mutable in-memory buffers. This is useful after a backed or lazy read, but storage and lazy choices belong in `../storage-io/SKILL.md`.

### `adata.to_df(layer=None)`

Returns a shallow pandas DataFrame with `obs_names` as the index and `var_names` as columns. If `layer` is provided, uses `adata.layers[layer]`; otherwise uses `adata.X`. Sparse matrices are densified, and annotations are not included.

```python
dense_expression = adata.to_df()
counts = adata.to_df(layer="counts")
```

### `obs_names_make_unique(join="-")` And `var_names_make_unique(join="-")`

Use when duplicate axis names would make slicing, joining, or downstream lookup ambiguous:

```python
adata.obs_names_make_unique()
adata.var_names_make_unique(join="-")
```

These update indexes through AnnData setters so aligned DataFrame-backed containers remain consistent.

## Settings That Affect Data Model Behavior

Verified defaults include:

- `anndata.settings.check_uniqueness = True`: warn when non-null `obs_names` or `var_names` contain duplicates.
- `anndata.settings.remove_unused_categories = True`: slicing views can drop unused categories in `obs`/`var` and related color metadata.
- `anndata.settings.use_sparse_array_on_read = False`: storage reads default toward sparse matrix classes rather than sparse array classes.
- `anndata.settings.zarr_write_format = 3`: default Zarr write target; route storage details to `../storage-io/SKILL.md`.

## Warnings And Error Classes

`anndata.ImplicitModificationWarning` is raised when AnnData changes user input or actualizes a view during mutation. Common triggers include converting indexes to strings during construction, assigning into `.obs`, `.var`, `.layers`, `.obsm`, `.varm`, `.obsp`, `.varp`, or `.X` on a view, and writing certain views. Treat the warning as a signal to decide whether `.copy()` was intended.
