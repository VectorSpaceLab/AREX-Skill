# Accessor and Namespace Troubleshooting

## Missing Keys

Symptom: `ref in adata` is `False`, or `adata[ref]` raises a key/index error.

Fix:

1. Log `str(ref)` and `ref.dims`.
2. Check the owning accessor: `ref.acc` shows the target such as `A.obs`, `A.layers['counts']`, or `A.obsm['pca']`.
3. Validate the relevant container key or axis name before extraction.
4. Report missing refs as strings so users see `A.obs['batch']` or `A.layers['counts'][:, 'gene-a']` instead of low-level pandas/numpy errors.

## Wrong Dimensions

Symptom: code expects an observation vector but receives a variable vector or two-dimensional array.

Fix:

- Inspect `ref.dims` before extraction.
- Require `ref.dims == {"obs"}` for observation-level colors, sample metadata, or per-cell masks.
- Require `ref.dims == {"var"}` for gene/feature metadata or loadings.
- Reject `{"obs", "var"}` or `("obs", "obs")` when the downstream consumer requires one-dimensional data.
- Route structural shape repair to `../data-model/SKILL.md` when the underlying `AnnData` object has invalid aligned containers.

## List vs Scalar Indexing

Symptom: constructing a ref returns a list, or a two-list index raises an error.

Fix:

- `A.obs[["a", "b"]]`, `A.obsm["pca"][:, [0, 1]]`, and `A.layers["counts"][:, ["g1", "g2"]]` intentionally return `list[AdRef]`.
- For one ref, pass a scalar string or integer: `A.obs["a"]`, `A.obsm["pca"][:, 0]`, `A.layers["counts"][:, "g1"]`.
- For two-dimensional layer/graph refs, only one dimension can contain a list at a time.
- Partial integer/slice indexing such as `A.X[:3, :]` is not a supported reference; accessors represent full axes or named rows/columns, not arbitrary ranges.

## String Parsing Errors

Symptom: `A.resolve(spec)` raises `ValueError`.

Fix:

- Use period-separated metadata and multi specs: `obs.batch`, `var.symbol`, `obsm.pca.0`, `varm.loadings.1`.
- Use bracketed two-dimensional specs for `X`, layers, and graphs: `X[:,:]`, `layers.counts[:,gene-a]`, `obsp.distances[cell-a,:]`.
- Use `A.resolve(spec, strict=False)` while validating user input so bad specs can be reported together.
- Prefer `A.to_json(ref)` / `A.from_json(data)` for durable configuration files.

## JSON Parsing Errors

Symptom: `A.from_json(data)` raises `ValueError`.

Fix:

- Ensure the payload is a list matching one of the supported shapes.
- Use `None` to represent full slices in two-dimensional JSON refs.
- Use integers only for `obsm`/`varm` column positions.
- Do not serialize custom `RefAcc` subclasses unless their refs match the built-in `LayerAcc`, `MetaAcc`, `MultiAcc`, or `GraphAcc` forms.

## Namespace Name Conflicts

Symptom: `register_anndata_namespace(name)` raises `AttributeError` or warns about overriding a custom namespace.

Fix:

- Rename namespaces that collide with reserved `AnnData` attributes such as `X`, `obs`, `var`, `uns`, `layers`, `copy`, or `write`.
- Treat override warnings as a package import-order or duplicate-registration bug unless intentional in tests.
- Use package-specific names and keep the namespace API small to reduce collision risk.

## Namespace Signature Validation

Symptom: registration raises `TypeError` or `AttributeError` about the initializer.

Fix:

- Define `__init__(self, adata: AnnData) -> None`.
- Name the second parameter exactly `adata`.
- Annotate it as the `AnnData` class.
- Keep constructor validation light; put object-state checks in explicit methods.

## Optional Plotting or Library Integration

Symptom: plotting/library code fails because refs are strings, arrays, or extension objects inconsistently.

Fix:

- Normalize all inputs to `AdRef` with `A.resolve(...)` or accept already-created `AdRef` instances.
- Check `ref in adata` before extraction.
- Extract with `adata[ref]` at the boundary where the plotting/library API needs concrete arrays.
- If an external plotting library treats references as strings, create a custom `AdAcc(ref_class=...)` only when necessary, and keep the custom ref behavior isolated from ordinary validation code.
