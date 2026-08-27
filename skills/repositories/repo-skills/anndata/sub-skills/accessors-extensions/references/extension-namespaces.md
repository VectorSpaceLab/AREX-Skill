# Extension Namespaces

Use `anndata.register_anndata_namespace(name)` when a library needs a small, typed, reusable public API attached to every `AnnData` instance. Do not use it for temporary analysis state or large private helper objects.

## Decorator Pattern

```python
import anndata as ad
from anndata import AnnData

@ad.register_anndata_namespace("qc")
class QCNamespace:
    def __init__(self, adata: AnnData) -> None:
        self._adata = adata

    def require_obs_column(self, key: str) -> None:
        if key not in self._adata.obs:
            raise KeyError(f"Missing obs column: {key}")
```

After registration, `adata.qc` returns a namespace instance bound to that object. The instance is cached on the `AnnData` object, so repeated `adata.qc` access returns the same namespace instance.

## Required Class Shape

The initializer is validated:

- It must accept a second parameter for the `AnnData` object.
- The second parameter must be named `adata`.
- The second parameter must be annotated as `AnnData`.
- Missing parameters, wrong names, wrong annotations, or missing annotations raise validation errors during registration.

Keep the namespace constructor cheap. Expensive validation should happen in explicit methods such as `validate()` or `require_ready()`.

## Conflict Avoidance

- Choose a short, package-specific namespace name such as `mytool`, not a generic word such as `plot` or `data`.
- Never register over reserved `AnnData` attributes like `X`, `obs`, `var`, `uns`, `obsm`, `varm`, `layers`, `copy`, or `write`; registration raises `AttributeError`.
- Re-registering an existing custom namespace warns and overrides it. Treat that warning as a packaging/debug signal, not as normal runtime behavior.
- Keep namespace methods public-API based: use `adata.obs`, `adata.var`, `adata.layers`, `adata.obsm`, `adata.uns`, and methods such as `.copy()` rather than private fields.

## Validation Methods

A namespace can refuse invalid object state without preventing construction:

```python
@ad.register_anndata_namespace("modelqc")
class ModelQCNamespace:
    def __init__(self, adata: AnnData) -> None:
        self._adata = adata

    def validate_inputs(self) -> list[str]:
        missing = []
        if "batch" not in self._adata.obs:
            missing.append("obs['batch']")
        if "counts" not in self._adata.layers:
            missing.append("layers['counts']")
        return missing

    def require_valid(self) -> None:
        missing = self.validate_inputs()
        if missing:
            raise ValueError(f"Invalid AnnData for modelqc: missing {missing}")
```

This pattern is easier to debug than raising during namespace construction, because users can still inspect `adata.modelqc` and call targeted validation methods.

## Namespace plus Accessors

Extension namespaces can use refs internally to avoid hard-coding extraction logic:

```python
from anndata.acc import A

REQUIRED_REFS = [A.obs["batch"], A.layers["counts"][:, :]]

def missing_refs(adata):
    return [str(ref) for ref in REQUIRED_REFS if ref not in adata]
```

For library code, expose small typed methods that accept explicit keys or refs. Avoid storing external file handles, mutable global state, or environment-specific paths in namespace instances.
