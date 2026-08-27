# Accessor and Extension API Reference

This reference summarizes the public accessor and extension APIs verified for this skill.

## Imports and Exports

```python
import anndata as ad
from anndata.acc import A, AdAcc, AdRef
```

`anndata.acc` exports `A`, `AdAcc`, `AdRef`, `RefAcc`, `LayerAcc`, `MetaAcc`, `MultiAcc`, `GraphAcc`, `LayerMapAcc`, `MultiMapAcc`, `GraphMapAcc`, and `Idx2D`. The map accessors are subclasses of the abstract `MapAcc` pattern even though `MapAcc` itself is not exported in `anndata.acc.__all__`.

## Core Signatures

- `AdAcc(ref_class=AdRef, layer_cls=LayerAcc, meta_cls=MetaAcc, multi_cls=MultiAcc, graph_cls=GraphAcc)`: creates a root accessor like the global `A`; override classes to customize reference or accessor behavior.
- `AdRef(acc, idx)`: object-independent reference with `.acc`, `.idx`, `.dims`, `str(ref)`, `repr(ref)`, equality, and hash behavior.
- `register_anndata_namespace(name: str) -> Callable[[type], type]`: returns a class decorator that attaches a namespace descriptor to `AnnData`.

## Object Relationships

- `A` is an `AdAcc` and owns accessors for `X`, `layers`, `obs`, `var`, `obsm`, `varm`, `obsp`, and `varp`.
- `A.X` and `A.layers[key]` are `LayerAcc` objects; `A.X` is the same addressing model as `A.layers[None]`.
- `A.obs` and `A.var` are `MetaAcc` objects for one-dimensional metadata columns and indexes.
- `A.obsm[key]` and `A.varm[key]` are `MultiAcc` objects for selecting integer columns from multidimensional aligned arrays.
- `A.obsp[key]` and `A.varp[key]` are `GraphAcc` objects for selecting rows, columns, or the full pairwise matrix along one axis.
- `A.layers`, `A.obsm`, `A.varm`, `A.obsp`, and `A.varp` are map accessors: indexing them with a string produces a reference accessor.

## Reference Shapes and Reprs

| Expression | Repr/string | Dims | Meaning |
| --- | --- | --- | --- |
| `A.X[:, :]` | `A.X[:, :]` | `{"obs", "var"}` | Full data matrix |
| `A.X[:, "gene-a"]` | `A.X[:, 'gene-a']` | `{"obs"}` | One variable vector from `X` |
| `A.layers["counts"]["cell-a", :]` | `A.layers['counts']['cell-a', :]` | `{"var"}` | One observation row from a layer |
| `A.obs["batch"]` | `A.obs['batch']` | `{"obs"}` | One observation annotation column |
| `A.obs.index` | `A.obs.index` | `{"obs"}` | Observation index |
| `A.var["symbol"]` | `A.var['symbol']` | `{"var"}` | One variable annotation column |
| `A.obsm["pca"][:, 0]` or `A.obsm["pca"][0]` | `A.obsm['pca'][:, 0]` | `{"obs"}` | One column from an observation-aligned matrix |
| `A.varm["loadings"][:, 1]` | `A.varm['loadings'][:, 1]` | `{"var"}` | One column from a variable-aligned matrix |
| `A.obsp["distances"][:, "cell-a"]` | `A.obsp['distances'][:, 'cell-a']` | `{"obs"}` | One graph column aligned to observations |
| `A.varp["correlations"][:, :]` | `A.varp['correlations'][:, :]` | `("var", "var")` | Full pairwise variable matrix |

## Membership and Extraction

- `ref in adata` calls the reference accessor’s `isin(...)` method and checks container keys, axis names, or multidimensional column bounds as appropriate.
- `accessor in adata` checks whether the accessor target exists: for example, `A.layers["counts"] in adata` checks the named layer; `A.obsm in adata` checks whether `.obsm` has any entries.
- `adata[ref]` extracts the referenced array through the accessor. One-dimensional selections flatten dense, sparse, Dask, CuPy, and view-backed arrays where the accessor implementation can do so safely.
- `obs`/`var` metadata extraction returns pandas extension arrays for DataFrame-backed metadata, and `Dataset2D` variables/indexes for lazy DataFrame-like metadata.

## Indexing Rules

- `LayerAcc` accepts only two-dimensional indexes containing `:` or one string: `[:, :]`, `["cell-a", :]`, or `[:, "gene-a"]`; lists or pandas indexes in one dimension expand to a list of refs.
- `MetaAcc` accepts a string column or `None` for `.index`; lists/pandas indexes expand to a list of refs.
- `MultiAcc` accepts an integer column or `[:, integer]`; lists/pandas indexes of integers expand to a list of refs.
- `GraphAcc` accepts graph indexes with one or two full slices and at most one string in ordinary extraction paths; lists/pandas indexes in one dimension expand to a list of refs.
- Invalid scalar/list shapes raise `TypeError` or `ValueError` at reference-construction time before any `AnnData` object is needed.

## Parsing and Serialization

`AdAcc` provides two reference interchange formats:

- `A.resolve(spec, strict=True)` parses strings such as `"X[:,:]"`, `"layers.counts[:,gene-a]"`, `"obs.batch"`, `"var.symbol"`, `"obsm.pca.0"`, `"varm.loadings.1"`, `"obsp.distances[cell-a,:]"`, and `"varp.correlations[:,gene-b]"`.
- `A.resolve(spec, strict=False)` returns `None` instead of raising `ValueError` when parsing fails.
- `A.to_json(ref)` serializes supported references to JSON-compatible lists, and `A.from_json(data)` parses those lists back into refs.
- JSON shapes are `['layers', layer_or_null, obs_name_or_null, var_name_or_null]`, `['obs'|'var', column_or_null]`, `['obsm'|'varm', key, integer_column]`, and `['obsp'|'varp', key, row_name_or_null, col_name_or_null]`.

## Extension Namespace API

`anndata.register_anndata_namespace(name)` attaches a descriptor to `AnnData`. The decorated class must accept an `AnnData` instance as the second initializer parameter named `adata` and annotated as `AnnData`.

```python
import anndata as ad
from anndata import AnnData

@ad.register_anndata_namespace("qc")
class QCNamespace:
    def __init__(self, adata: AnnData) -> None:
        self._adata = adata

    def require_obs(self, key: str) -> None:
        if key not in self._adata.obs:
            raise KeyError(key)
```

Namespace instances are cached per `AnnData` object after first access. Registering over an existing custom namespace emits a warning and replaces it; registering over a reserved `AnnData` attribute such as `X`, `obs`, `var`, `uns`, `layers`, `copy`, or `write` raises `AttributeError`.
