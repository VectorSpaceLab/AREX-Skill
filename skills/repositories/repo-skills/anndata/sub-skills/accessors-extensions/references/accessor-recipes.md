# Accessor Recipes

Reference accessors make validation and plotting code independent of one specific `AnnData` object. Build refs once, validate them against an object, and extract only after membership checks pass.

## Create Common References

```python
from anndata.acc import A

refs = [
    A.obs["batch"],
    A.var["symbol"],
    A.obsm["pca"][:, 0],
    A.layers["counts"][:, "gene-a"],
    A.X[:, "gene-b"],
]
```

Useful concrete reprs are stable enough for logs and user-facing error messages:

- `str(A.obs["batch"])` -> `A.obs['batch']`
- `str(A.var.index)` -> `A.var.index`
- `str(A.obsm["pca"][:, 0])` -> `A.obsm['pca'][:, 0]`
- `str(A.layers["counts"][:, "gene-a"])` -> `A.layers['counts'][:, 'gene-a']`

## Validate Before Extracting

```python
missing = [str(ref) for ref in refs if ref not in adata]
if missing:
    raise KeyError(f"AnnData is missing required fields: {missing}")
values = {str(ref): adata[ref] for ref in refs}
```

This avoids hard-coded container logic. Each ref owns its membership test:

- Metadata refs check `.obs` or `.var` columns, while `.index` refs are always present on populated or empty objects.
- Layer refs check `.X` or `.layers[key]` and any named `obs_names`/`var_names` used in the index.
- Multi refs check `.obsm[key]`/`.varm[key]` and that the requested integer column is in bounds.
- Graph refs check `.obsp[key]`/`.varp[key]` and any named axis index used in the graph row/column.

## Accept Strings or Refs in User APIs

```python
from anndata.acc import A, AdRef

def normalize_ref(ref_or_spec: AdRef | str) -> AdRef:
    if isinstance(ref_or_spec, AdRef):
        return ref_or_spec
    return A.resolve(ref_or_spec, strict=True)
```

Good string specs include:

- `"obs.batch"` -> `A.obs['batch']`
- `"var.symbol"` -> `A.var['symbol']`
- `"X[:,gene-a]"` -> `A.X[:, 'gene-a']`
- `"layers.counts[cell-a,:]"` -> `A.layers['counts']['cell-a', :]`
- `"obsm.pca.0"` -> `A.obsm['pca'][:, 0]`
- `"varm.loadings.1"` -> `A.varm['loadings'][:, 1]`
- `"obsp.distances[:,cell-a]"` -> `A.obsp['distances'][:, 'cell-a']`

Use `A.resolve(spec, strict=False)` when invalid user input should be reported as a validation error instead of raising immediately.

## Use JSON for Config Files

`A.to_json(ref)` and `A.from_json(data)` are safer for machine configs than parsing display strings. Supported JSON forms are schema-like lists:

```python
payloads = [
    A.to_json(A.obs["batch"]),              # ["obs", "batch"]
    A.to_json(A.var.index),                 # ["var", None]
    A.to_json(A.layers["counts"][:, "g1"]), # ["layers", "counts", None, "g1"]
    A.to_json(A.obsm["pca"][:, 0]),         # ["obsm", "pca", 0]
]
refs = [A.from_json(payload) for payload in payloads]
```

JSON parsing raises `ValueError` for unknown containers, wrong lengths, unsupported index patterns, or unsupported ref accessor classes.

## Expand Lists into Multiple Refs

Some accessors accept lists or pandas indexes and return `list[AdRef]`:

```python
plot_refs = [
    *A.obs[["batch", "phase"]],
    *A.obsm["pca"][:, [0, 1]],
    *A.layers["counts"][:, ["gene-a", "gene-b"]],
]
```

Only one dimension of a two-dimensional layer/graph index can be a list at a time. If both dimensions are lists, construct separate refs intentionally.

## Plotting and Data Selection Pattern

For plotting integrations, pass refs as data selectors rather than extracting early:

```python
def collect_plot_data(adata, x, y, color=None):
    refs = [normalize_ref(x), normalize_ref(y)]
    if color is not None:
        refs.append(normalize_ref(color))
    missing = [str(ref) for ref in refs if ref not in adata]
    if missing:
        raise KeyError(f"Missing plot inputs: {missing}")
    return {str(ref): adata[ref] for ref in refs}
```

This accepts `AdRef` instances, display-friendly string specs, and different containers without branching per `.obs`, `.obsm`, `.layers`, or `.X`.
