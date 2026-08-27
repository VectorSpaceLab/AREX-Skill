---
name: accessors-extensions
description: "Use anndata reference accessors for validation, plotting, data
  selection, and typed AnnData extension namespaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Accessors and Extensions

Use this sub-skill when code needs portable references to arrays inside `AnnData` objects or a small typed namespace attached to `AnnData` instances.

## Route Here

- Build and inspect `anndata.acc` references such as `A.obs["batch"]`, `A.var["symbol"]`, `A.obsm["pca"][:, 0]`, `A.layers["counts"][:, "gene-a"]`, `A.obsp["connectivities"][:, "cell-a"]`, or `A.X[:, :]`.
- Check whether a reference/accessor is present in an object with `ref in adata` or `A.obsm in adata`, then extract values with `adata[ref]`.
- Parse or serialize references with `A.resolve(...)`, `A.to_json(ref)`, and `A.from_json(data)` for validation/configuration layers.
- Register a typed extension namespace with `anndata.register_anndata_namespace(name)` for library-style helpers on `AnnData`.

## Route Elsewhere

- For `AnnData` shape, view, `obs`/`var`, `layers`, `obsm`, `obsp`, and container mutation semantics, use `../data-model/SKILL.md`.
- For `.h5ad`, Zarr, lazy/backed reads, or element I/O, use `../storage-io/SKILL.md`.
- For `anndata.concat`, `concat_on_disk`, `AnnCollection`, or batch-combination choices, use `../combining-data/SKILL.md`.

## References

- `references/api-reference.md` lists the accessor classes, signatures, object relationships, and extraction contracts.
- `references/accessor-recipes.md` gives practical recipes for membership checks, extraction, JSON/string parsing, and validation-friendly reference handling.
- `references/extension-namespaces.md` covers the namespace decorator, class shape, validation, caching, and conflict avoidance.
- `references/troubleshooting.md` maps common accessor and namespace failures to fixes.
- `scripts/demo_anndata_accessor.py` is a tiny runnable demo for refs, extraction, JSON/string parsing, and namespace registration.

## Operating Rules

- Treat `AdRef` objects as object-independent references; validate `ref in adata` before extraction when user input or optional fields are involved.
- Prefer public `AnnData` APIs and small typed namespace methods; extension namespaces are for library code, not ad-hoc per-notebook state.
- Keep plotting/data-selection APIs accepting either `AdRef` instances or parseable strings, then normalize to refs with `A.resolve(..., strict=True)`.
